import hashlib
import sqlite3
import time
import uuid
import os

from pathlib import Path

from Modules.Database.Database import SQLiteDatabase
from Modules.PreIndexed.Functions import normalize_name
from Modules.PreIndexed.Manifests import rest_response_to_manifests
from Modules.Winget.Functions import generate_Installer_Manifest
from settings import PATH_PREINDEXED_FILES


class WingetIndexBuilder:
    def __init__(self):
        self.index_db  = os.path.join(PATH_PREINDEXED_FILES, "Public", "index.db")
        os.makedirs(self.index_db.replace("index.db", ""), exist_ok=True)

        self._ids_cache             = {}
        self._names_cache           = {}
        self._monikers_cache        = {}
        self._versions_cache        = {}
        self._channels_cache        = {}
        self._pathparts_cache       = {}
        self._tags_cache            = {}
        self._commands_cache        = {}
        self._pfns_cache            = {}
        self._productcodes_cache    = {}
        self._norm_names_cache      = {}
        self._norm_publishers_cache = {}
        self._upgradecodes_cache    = {}

    def build(self):
        if Path(self.index_db).exists():
            Path(self.index_db).unlink()

        dst = sqlite3.connect(self.index_db)
        try:
            self._create_schema(dst)
            self._write_metadata(dst)
            self._migrate_packages(dst)
            dst.commit()

            dst.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            dst.execute("PRAGMA journal_mode=DELETE")
            dst.commit()
        finally:
            dst.close()

    def _create_schema(self, dst: sqlite3.Connection):
        dst.executescript("""
        PRAGMA journal_mode=WAL;

        CREATE TABLE IF NOT EXISTS metadata (
            name  TEXT NOT NULL,
            value TEXT NOT NULL,
            PRIMARY KEY(name)
        ) WITHOUT ROWID;

        CREATE TABLE IF NOT EXISTS ids (
            rowid INTEGER PRIMARY KEY,
            id    TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS names (
            rowid INTEGER PRIMARY KEY,
            name  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS monikers (
            rowid   INTEGER PRIMARY KEY,
            moniker TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS versions (
            rowid   INTEGER PRIMARY KEY,
            version TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS channels (
            rowid   INTEGER PRIMARY KEY,
            channel TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS pathparts (
            rowid    INTEGER PRIMARY KEY,
            parent   INT64,
            pathpart TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS manifest (
            rowid           INTEGER PRIMARY KEY,
            id              INT64 NOT NULL,
            name            INT64 NOT NULL,
            moniker         INT64 NOT NULL,
            version         INT64 NOT NULL,
            channel         INT64 NOT NULL,
            pathpart        INT64 NOT NULL,
            hash            BLOB,
            arp_min_version INT64,
            arp_max_version INT64
        );

        CREATE TABLE IF NOT EXISTS tags (
            rowid INTEGER PRIMARY KEY,
            tag   TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tags_map (
            tag      INT64 NOT NULL,
            manifest INT64 NOT NULL,
            PRIMARY KEY(tag, manifest)
        ) WITHOUT ROWID;

        CREATE TABLE IF NOT EXISTS commands (
            rowid   INTEGER PRIMARY KEY,
            command TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS commands_map (
            command  INT64 NOT NULL,
            manifest INT64 NOT NULL,
            PRIMARY KEY(command, manifest)
        ) WITHOUT ROWID;

        CREATE TABLE IF NOT EXISTS pfns (
            rowid INTEGER PRIMARY KEY,
            pfn   TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS pfns_map (
            pfn      INT64 NOT NULL,
            manifest INT64 NOT NULL,
            PRIMARY KEY(pfn, manifest)
        ) WITHOUT ROWID;

        CREATE TABLE IF NOT EXISTS productcodes (
            rowid       INTEGER PRIMARY KEY,
            productcode TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS productcodes_map (
            productcode INT64 NOT NULL,
            manifest    INT64 NOT NULL,
            PRIMARY KEY(productcode, manifest)
        ) WITHOUT ROWID;

        CREATE TABLE IF NOT EXISTS norm_names (
            rowid     INTEGER PRIMARY KEY,
            norm_name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS norm_names_map (
            norm_name INT64 NOT NULL,
            manifest  INT64 NOT NULL,
            PRIMARY KEY(norm_name, manifest)
        ) WITHOUT ROWID;

        CREATE TABLE IF NOT EXISTS norm_publishers (
            rowid          INTEGER PRIMARY KEY,
            norm_publisher TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS norm_publishers_map (
            norm_publisher INT64 NOT NULL,
            manifest       INT64 NOT NULL,
            PRIMARY KEY(norm_publisher, manifest)
        ) WITHOUT ROWID;

        CREATE TABLE IF NOT EXISTS upgradecodes (
            rowid       INTEGER PRIMARY KEY,
            upgradecode TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS upgradecodes_map (
            upgradecode INT64 NOT NULL,
            manifest    INT64 NOT NULL,
            PRIMARY KEY(upgradecode, manifest)
        ) WITHOUT ROWID;

        CREATE INDEX IF NOT EXISTS manifest_id_index ON manifest(id);
        CREATE INDEX IF NOT EXISTS manifest_name_index ON manifest(name);
        CREATE INDEX IF NOT EXISTS manifest_moniker_index ON manifest(moniker);

        CREATE INDEX IF NOT EXISTS norm_names_map_index ON norm_names_map(manifest, norm_name);
        CREATE UNIQUE INDEX IF NOT EXISTS norm_names_pkindex ON norm_names(norm_name);

        CREATE INDEX IF NOT EXISTS norm_publishers_map_index ON norm_publishers_map(manifest, norm_publisher);
        CREATE UNIQUE INDEX IF NOT EXISTS norm_publishers_pkindex ON norm_publishers(norm_publisher);

        CREATE INDEX IF NOT EXISTS productcodes_map_index ON productcodes_map(manifest, productcode);
        CREATE UNIQUE INDEX IF NOT EXISTS productcodes_pkindex ON productcodes(productcode);

        CREATE INDEX IF NOT EXISTS pfns_map_index ON pfns_map(manifest, pfn);
        CREATE UNIQUE INDEX IF NOT EXISTS pfns_pkindex ON pfns(pfn);

        CREATE INDEX IF NOT EXISTS upgradecodes_map_index ON upgradecodes_map(manifest, upgradecode);
        CREATE UNIQUE INDEX IF NOT EXISTS upgradecodes_pkindex ON upgradecodes(upgradecode);
        """)
        dst.commit()

    def _write_metadata(self, dst: sqlite3.Connection):
        now = int(time.time())
        db_id = f"{{{str(uuid.uuid4()).upper()}}}"

        dst.executemany(
            "INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)",
            [
                ("majorVersion", "1"),
                ("minorVersion", "7"),
                ("lastwritetime", str(now)),
                ("databaseIdentifier", db_id),
                ("mapDataFolded", "1.7"),
            ]
        )
        self._get_or_insert(dst, "channels", "channel", "", self._channels_cache)
        self._get_or_insert(dst, "versions", "version", "", self._versions_cache)

    def _migrate_packages(self, dst: sqlite3.Connection):
        with SQLiteDatabase() as src_db:
            packages = src_db.get_All_Packages()
            print(f"[WingetIndexBuilder] Verarbeite {len(packages)} Pakete ...")

            for pkg in packages:
                versions_rows = src_db.get_All_Versions_from_Package(pkg['PACKAGE_ID'])
                if not versions_rows:
                    print(f"  [SKIP] {pkg['PACKAGE_ID']} - keine Versionen")
                    continue

                seen_versions = {}
                for row in versions_rows:
                    row = dict(row)
                    key = (row["VERSION"], row.get("CHANNEL") or "")
                    if key not in seen_versions:
                        seen_versions[key] = []
                    seen_versions[key].append(row)

                for (version_str, channel_str), installers in seen_versions.items():
                    self._insert_manifest_entry(dst, pkg['PACKAGE_ID'], pkg['PACKAGE_NAME'], pkg['PACKAGE_PUBLISHER'], version_str, channel_str, installers)
                print(f"  [OK]   {pkg['PACKAGE_ID']} - {len(seen_versions)} Version(en)")

    def _insert_manifest_entry(self, dst: sqlite3.Connection, package_id: str, package_name: str, publisher: str, version: str, channel: str, installers: list) -> int:
        channel = channel or ""

        id_rowid      = self._get_or_insert(dst, "ids",      "id",      package_id,   self._ids_cache)
        name_rowid    = self._get_or_insert(dst, "names",    "name",    package_name, self._names_cache)
        moniker_str   = package_id.split(".")[-1].lower()
        moniker_rowid = self._get_or_insert(dst, "monikers", "moniker", moniker_str,  self._monikers_cache)
        version_rowid = self._get_or_insert(dst, "versions", "version", version,      self._versions_cache)
        channel_rowid = self._get_or_insert(dst, "channels", "channel", channel,      self._channels_cache)

        p_hash = hashlib.sha256(f"{package_id}_{version}_{channel}".encode('utf-8')).hexdigest().lower()

        path_segments  = ["manifest", package_id, version, channel,  p_hash[:4]]
        pathpart_rowid = self._get_or_insert_pathpart(dst, path_segments)

        data = generate_Installer_Manifest(package_id, version, channel, "", use_serializer=False)
        installer, installer_bytes = rest_response_to_manifests(data)

        cur = dst.execute("""INSERT INTO manifest (id, name, moniker, version, channel, pathpart, hash, arp_min_version, arp_max_version) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL)""",
                          (id_rowid, name_rowid, moniker_rowid, version_rowid, 1, pathpart_rowid, installer_bytes))
        manifest_rowid = cur.lastrowid

        norm_name = normalize_name(package_name)
        norm_pub  = normalize_name(publisher)

        if norm_name:
            nn_rowid = self._get_or_insert(dst, "norm_names", "norm_name", norm_name, self._norm_names_cache)
            dst.execute("INSERT OR IGNORE INTO norm_names_map (manifest, norm_name) VALUES (?, ?)",(manifest_rowid, nn_rowid))

        if norm_pub:
            np_rowid = self._get_or_insert(
                dst, "norm_publishers", "norm_publisher", norm_pub,
                self._norm_publishers_cache)
            dst.execute("INSERT OR IGNORE INTO norm_publishers_map (manifest, norm_publisher) VALUES (?, ?)",(manifest_rowid, np_rowid))

        seen_productcodes = set()
        seen_upgradecodes = set()
        seen_pfns         = set()
        for inst in installers:
            pc = (inst.get("PRODUCTCODE") or "").strip()
            if pc and pc not in seen_productcodes:
                pc_rowid = self._get_or_insert(
                    dst, "productcodes", "productcode", pc, self._productcodes_cache)
                dst.execute("INSERT OR IGNORE INTO productcodes_map (manifest, productcode) VALUES (?, ?)",(manifest_rowid, pc_rowid))
                seen_productcodes.add(pc)

            uc = (inst.get("UPGRADECODE") or "").strip()
            if uc and uc not in seen_upgradecodes:
                uc_rowid = self._get_or_insert(
                    dst, "upgradecodes", "upgradecode", uc, self._upgradecodes_cache)
                dst.execute("INSERT OR IGNORE INTO upgradecodes_map (manifest, upgradecode) VALUES (?, ?)",(manifest_rowid, uc_rowid))
                seen_upgradecodes.add(uc)

            pfn = (inst.get("PACKAGE_FAMILY_NAME") or "").strip()
            if pfn and pfn not in seen_pfns:
                pfn_rowid = self._get_or_insert(
                    dst, "pfns", "pfn", pfn, self._pfns_cache)
                dst.execute("INSERT OR IGNORE INTO pfns_map (manifest, pfn) VALUES (?, ?)",(manifest_rowid, pfn_rowid))
                seen_pfns.add(pfn)
        return manifest_rowid

    def _get_or_insert_pathpart(self, dst: sqlite3.Connection, segments: list) -> int:
        parent_rowid = None
        for segment in segments:
            key = (parent_rowid, segment)
            if key in self._pathparts_cache:
                parent_rowid = self._pathparts_cache[key]
                continue

            cur = dst.execute("INSERT INTO pathparts (parent, pathpart) VALUES (?, ?)",(parent_rowid, segment))
            new_rowid = cur.lastrowid
            self._pathparts_cache[key] = new_rowid
            parent_rowid = new_rowid
        return parent_rowid

    def _get_or_insert(self, dst: sqlite3.Connection, table: str, col: str, value: str, cache: dict) -> int:
        if value in cache:
            return cache[value]

        cur = dst.execute(f"INSERT INTO {table} ({col}) VALUES (?)", (value,))
        rowid = cur.lastrowid
        cache[value] = rowid
        return rowid
