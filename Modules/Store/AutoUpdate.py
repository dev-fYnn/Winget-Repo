import atexit
import json
import os
import re
import threading
import time

if os.name == 'nt':
    import msvcrt
else:
    import fcntl

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from Modules.Database.Database import SQLiteDatabase
from Modules.PreIndexed.Creator import generate_indexed_db_package
from Modules.Database.Store_DB import StoreDB
from Modules.Functions import parse_version
from Modules.Packages.Functions import delete_overflow_package_versions
from Modules.Store.Functions import download_source_msix, load_store_manifest, add_installer_version
from settings import PATH_CONFIG


def read_state():
    with SQLiteDatabase() as db:
        return json.loads(db.get_winget_Settings().get('AUTO_UPDATE_STATE', '{}'))


def save_state(state):
    with SQLiteDatabase() as db:
        db.update_wingetrepo_Setting('AUTO_UPDATE_STATE', json.dumps(state))


def enabled():
    with SQLiteDatabase() as db:
        settings = db.get_winget_Settings()
    return settings.get('PACKAGE_STORE') == '1' and settings.get('AUTO_UPDATE_PACKAGES') == '1'


def variant(row, manifest=False):
    fields = (
        ('InstallerType', 'INSTALLER_TYPE', 'msi'),
        ('Architecture', 'ARCHITECTURE', 'x64'),
        ('InstallerLocale', 'LOCALE', 'en-US'),
        ('Scope', 'INSTALLER_SCOPE', 'machine'),
        ('NestedInstallerType', 'INSTALLER_NESTED_TYPE', ''),
        ('Channel', 'CHANNEL', 'stable'),
    )
    return tuple(str(row.get(m if manifest else d, default) or '').lower() for m, d, default in fields)


def auto_update_summary():
    state = read_state()
    summary = dict(updated=0, skipped=0, current=0, failed=0, pending=0)
    for result in state.get('results', {}).values():
        added = re.search(r': (\d+) installer\(s\) added;', result)
        if result.startswith('Error:'):
            summary['failed'] += 1
        elif result.startswith('Skipped:'):
            summary['skipped'] += 1
        elif result == 'Up to date.' or (added and int(added[1]) == 0):
            summary['current'] += 1
        elif added:
            summary['updated'] += 1
        else:
            summary['pending'] += 1
    display = dict(state, summary=summary)
    for field in ('started', 'finished'):
        if display.get(field):
            try:
                timestamp = datetime.fromisoformat(display[field])
                display[field] = timestamp.astimezone(timezone.utc).strftime('%d.%m.%Y, %H:%M:%S')
            except (TypeError, ValueError):
                pass
    return display


@contextmanager
def worker_lock():
    path = Path(PATH_CONFIG) / 'package-auto-update.lock'
    with path.open('a+b') as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b'0')
            handle.flush()
        handle.seek(0)
        try:
            if os.name == 'nt':
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            yield False
            return
        try:
            yield True
        finally:
            handle.seek(0)
            if os.name == 'nt':
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def update_package(package_id, state):
    with SQLiteDatabase() as db:
        rows = db.get_All_Versions_from_Package(package_id)
    if not rows:
        return 'Skipped: no existing installer versions.'

    plans = state.setdefault('pending', {})
    plan = plans.get(package_id)
    latest = max(rows, key=lambda row: parse_version(row['VERSION']))['VERSION']
    if plan and parse_version(latest) > parse_version(plan['version']):
        del plans[package_id]
        plan = None
    if not plan:
        with StoreDB() as store:
            available = store.get_Package_Versions(package_id)
        if not available:
            return 'Skipped: package not found in store.'
        target = max(available, key=parse_version)
        if parse_version(target) <= parse_version(latest):
            return 'Up to date.'
        plan = {
            'version': target,
            'variants': [list(variant(row)) for row in rows if row['VERSION'] == latest],
        }
        plans[package_id] = plan
        save_state(state)

    manifest, error = load_store_manifest(package_id, plan['version'])
    if error:
        raise RuntimeError(error)
    wanted = {tuple(item) for item in plan['variants']}
    selected = {}
    for installer in manifest['Installers']:
        key = variant(installer, manifest=True)
        if key in wanted:
            selected.setdefault(key, installer)
    if not selected:
        del plans[package_id]
        return 'Skipped: no matching installer variants in the new version.'

    added = 0
    errors = []
    for installer in selected.values():
        if not enabled():
            return 'Paused: automatic updates disabled.'
        try:
            state['index_dirty'] = True
            save_state(state)
            with SQLiteDatabase() as db:
                success, message = add_installer_version(db, package_id, plan['version'], installer)
            if success:
                added += 1
                state['index_dirty'] = True
                save_state(state)
            elif message != 'Version already exists!':
                errors.append(message)
        except Exception as exc:
            errors.append(str(exc))
    if errors:
        raise RuntimeError('; '.join(errors))
    with SQLiteDatabase() as db:
        delete_overflow_package_versions(package_id, db)
    del plans[package_id]
    missing = len(wanted - selected.keys())
    return f'{plan["version"]}: {added} installer(s) added; {missing} variant(s) unavailable.'


def run_due(app):
    with worker_lock() as acquired:
        if not acquired or not enabled():
            return
        state = read_state()
        if state.get('status') != 'Running' and time.time() - state.get('last_attempt', 0) < (24 * 60 * 60):
            return
        state.update(last_attempt=time.time(), started=datetime.now(timezone.utc).isoformat(), status='Running', results={}, finished=None)
        save_state(state)
        try:
            if not download_source_msix(True):
                raise RuntimeError('Could not refresh the package store.')
            with SQLiteDatabase() as db:
                packages = db.get_All_Packages()
            package_ids = {p['PACKAGE_ID'] for p in packages}
            state['pending'] = {k: v for k, v in state.get('pending', {}).items() if k in package_ids}
            for package in packages:
                if not enabled():
                    break
                package_id = package['PACKAGE_ID']
                try:
                    state['results'][package_id] = update_package(package_id, state)
                except Exception as exc:
                    state['results'][package_id] = f'Error: {exc}'
                save_state(state)
            with SQLiteDatabase() as db:
                settings = db.get_winget_Settings()
            if state.get('index_dirty') and settings.get('INDEXED_DB_ACTIV') == '1':
                message, category = generate_indexed_db_package(app.config['ENCRYPTION_KEY'])
                if category != 'success':
                    raise RuntimeError(message)
            state['index_dirty'] = False
            state['status'] = ('Completed with errors' if any(
                value.startswith('Error:') for value in state['results'].values()) else 'Completed')
            if not enabled():
                state['status'] = 'Paused: automatic updates disabled'
        except Exception as exc:
            state['status'] = f'Error: {exc}'
        finally:
            state['finished'] = datetime.now(timezone.utc).isoformat()
            save_state(state)


def start_auto_updates(app):
    if 'package_auto_updater' in app.extensions:
        return
    stop = threading.Event()

    def loop():
        while not stop.wait(30):
            try:
                with app.app_context():
                    run_due(app)
            except Exception:
                pass

    thread = threading.Thread(target=loop, name='package-auto-updater', daemon=True)
    app.extensions['package_auto_updater'] = (thread, stop)
    atexit.register(stop.set)
    thread.start()
