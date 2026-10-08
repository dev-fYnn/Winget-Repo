#!/usr/bin/env python3
"""Conservative, hash-verified backfill of WinGet-Repo correlation fields.

Run INSIDE the Winget-Repo container. Dry run is the default; --apply writes to
SQLite after a consistent backup. Only package versions found in the official
CDN store index AND whose installer SHA, architecture/type/scope match are used.
"""
import argparse
import csv
import hashlib
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
import yaml

PROJECT = Path('/wingetrepo') if Path('/wingetrepo/settings.py').is_file() else Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
from settings import PATH_DATABASE, URL_WINGET_REPOSITORY, PATH_WINGET_REPOSITORY_DB
from Modules.Database.Store_DB import StoreDB

FIELDS = {'ProductCode': 'PRODUCTCODE', 'UpgradeCode': 'UPGRADECODE', 'PackageFamilyName': 'PACKAGE_FAMILY_NAME'}


def unique_value(entries, key):
    vals = {str(e.get(key, '')).strip() for e in entries if isinstance(e, dict) and e.get(key)}
    if len(vals) > 1:
        raise ValueError(f'multiple conflicting AppsAndFeaturesEntries.{key}')
    return next(iter(vals), '')


def manifest_metadata(manifest, installer):
    # Installer fields override manifest defaults. A&F fields override ProductCode.
    aaf = installer.get('AppsAndFeaturesEntries')
    if aaf is None:
        aaf = manifest.get('AppsAndFeaturesEntries', [])
    if not isinstance(aaf, list):
        raise ValueError('malformed AppsAndFeaturesEntries')
    product = unique_value(aaf, 'ProductCode') or installer.get('ProductCode') or manifest.get('ProductCode') or ''
    upgrade = unique_value(aaf, 'UpgradeCode') or installer.get('UpgradeCode') or manifest.get('UpgradeCode') or ''
    family = installer.get('PackageFamilyName') or manifest.get('PackageFamilyName') or ''
    return {'PRODUCTCODE': str(product).strip(), 'UPGRADECODE': str(upgrade).strip(), 'PACKAGE_FAMILY_NAME': str(family).strip()}


def normalize(s):
    return str(s or '').strip().lower()


def get_candidate(manifest, row):
    wanted_sha = normalize(row['INSTALLER_SHA256'])
    if len(wanted_sha) != 64 or any(ch not in '0123456789abcdef' for ch in wanted_sha):
        raise ValueError('invalid stored SHA256')
    matches = []
    for installer in manifest.get('Installers', []):
        if not isinstance(installer, dict) or normalize(installer.get('InstallerSha256')) != wanted_sha:
            continue
        if normalize(installer.get('Architecture', 'x64')) != normalize(row['ARCHITECTURE']):
            continue
        if normalize(installer.get('InstallerType') or manifest.get('InstallerType')) != normalize(row['INSTALLER_TYPE']):
            continue
        if normalize(installer.get('Scope') or manifest.get('Scope') or 'machine') != normalize(row['INSTALLER_SCOPE']):
            continue
        matches.append(installer)
    if not matches:
        raise ValueError('installer SHA256/architecture/type/scope not matched')
    values = [manifest_metadata(manifest, item) for item in matches]
    if any(value != values[0] for value in values[1:]):
        raise ValueError('ambiguous installers with different correlation metadata')
    return values[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--apply', action='store_true', help='Apply missing values after consistent DB backup')
    ap.add_argument('--report', default='', help='Report CSV path (default: Config/metadata-reconciliation.csv)')
    args = ap.parse_args()

    db_path = Path(PATH_DATABASE)
    store_index = Path(PATH_WINGET_REPOSITORY_DB)
    if not db_path.is_file() or not store_index.is_file():
        sys.exit(f'Missing database or Store index: {db_path} / {store_index}')

    report_path = Path(args.report) if args.report else db_path.parent.parent / 'metadata-reconciliation.csv'
    conn = sqlite3.connect(f'{db_path.as_uri()}?mode=rw', uri=True, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA busy_timeout=30000')
    required = {'UID', 'PACKAGE_ID', 'VERSION', 'ARCHITECTURE', 'INSTALLER_TYPE', 'INSTALLER_SCOPE', 'INSTALLER_SHA256', *FIELDS.values()}
    actual = {row[1] for row in conn.execute('PRAGMA table_info(tbl_PACKAGES_VERSIONS)')}
    if not required <= actual:
        sys.exit(f'Unexpected DB schema, missing: {sorted(required - actual)}')
    if conn.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
        sys.exit('Database integrity check failed')

    versions = conn.execute('SELECT UID, PACKAGE_ID, VERSION, ARCHITECTURE, INSTALLER_TYPE, INSTALLER_SCOPE, '
                            'INSTALLER_SHA256, PRODUCTCODE, UPGRADECODE, PACKAGE_FAMILY_NAME '
                            'FROM tbl_PACKAGES_VERSIONS ORDER BY PACKAGE_ID, VERSION, UID').fetchall()
    if not versions:
        sys.exit('No package versions found; refusing to continue')
    session = requests.Session()
    session.headers['User-Agent'] = 'WingetRepoMetadataReconcile/1.0'
    cache = {}
    changes = []
    records = []

    with StoreDB() as store:
        for row in versions:
            identity = (row['PACKAGE_ID'], row['VERSION'])
            if identity not in cache:
                try:
                    pieces = store.get_Package_Path(*identity)
                    if not pieces:
                        raise ValueError('package version not found in official Store index')
                    url = urljoin(URL_WINGET_REPOSITORY, '/'.join(pieces))
                    if not url.startswith('https://cdn.winget.microsoft.com/cache/'):
                        raise ValueError('untrusted manifest URL')
                    response = session.get(url, timeout=(8, 25))
                    response.raise_for_status()
                    if len(response.content) > 1_000_000:
                        raise ValueError('oversized manifest')
                    manifest = yaml.safe_load(response.text)
                    if not isinstance(manifest, dict) or (manifest.get('PackageIdentifier'), str(manifest.get('PackageVersion'))) != identity:
                        raise ValueError('manifest ID/version mismatch')
                    cache[identity] = (manifest, '')
                except (requests.RequestException, ValueError, yaml.YAMLError) as exc:
                    cache[identity] = (None, str(exc))

            manifest, error = cache[identity]
            if not error:
                try:
                    values = get_candidate(manifest, row)
                except ValueError as exc:
                    error = str(exc)
            if error:
                records.append({'UID': row['UID'], 'Package': identity[0], 'Version': identity[1],
                                'Field': '-', 'Current': '-', 'Online': '-', 'Status': 'SKIP', 'Reason': error})
                continue
            for field, online in values.items():
                if not online:
                    continue
                current = str(row[field] or '').strip()
                status = ('OK' if current.casefold() == online.casefold() else
                          'CONFLICT' if current else 'UPDATE')
                records.append({'UID': row['UID'], 'Package': identity[0], 'Version': identity[1],
                                'Field': field, 'Current': current, 'Online': online, 'Status': status,
                                'Reason': 'exact installer SHA256/architecture/type/scope match'})
                if status == 'UPDATE':
                    changes.append((row['UID'], field, online))

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['UID', 'Package', 'Version', 'Field', 'Current', 'Online', 'Status', 'Reason'])
        writer.writeheader()
        writer.writerows(records)
    count = Counter(r['Status'] for r in records)
    print(f'Rows inspected: {len(versions)} | Online manifests: {len(cache)}')
    print('Status:', dict(count))
    print('CSV report:', report_path)
    if count['CONFLICT']:
        print('WARNING: Existing non-empty values disagree with online; these will NOT be overwritten.')
    if count['SKIP']:
        print('WARNING: Some records skipped. See CSV. They will NOT be modified.')

    if not args.apply:
        print('DRY RUN: No database changes. Use --apply only after reviewing CSV.')
        conn.close()
        return
    if not changes:
        print('No missing values to add.')
        conn.close()
        return

    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup = db_path.with_name(f'{db_path.name}.before-metadata-reconcile-{stamp}.bak')
    with sqlite3.connect(backup) as dst:
        conn.backup(dst)
        if dst.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            sys.exit('Backup integrity check failed')
    print('SQLite backup:', backup, flush=True)
    try:
        conn.execute('BEGIN IMMEDIATE')
        for uid, field, online in changes:
            # field is derived only from fixed FIELDS mapping, never untrusted input
            cursor = conn.execute(f'UPDATE tbl_PACKAGES_VERSIONS SET {field} = ? '
                                  f'WHERE UID = ? AND TRIM(COALESCE({field}, "")) = ""',
                                  (online, uid))
            if cursor.rowcount != 1:
                raise RuntimeError(f'Concurrent modification or missing row: {uid}/{field}')
        if conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise RuntimeError('Database integrity check failed after update')
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    print(f'APPLIED: {len(changes)} missing metadata fields. Existing non-empty fields preserved.')


if __name__ == '__main__':
    main()
