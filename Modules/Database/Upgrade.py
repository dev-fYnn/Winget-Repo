import sqlite3
import sys
import os

from datetime import datetime

CUSTOM_CONFLICT_COLS: dict[str, list[str]] = {
    "tbl_SETTINGS": ["SETTING_NAME"],
}


def get_tables(conn: sqlite3.Connection) -> list[str]:
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    return [row[0] for row in cursor.fetchall()]


def get_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    cursor = conn.execute(f"PRAGMA table_info('{table}')")
    return [row[1] for row in cursor.fetchall()]


def get_primary_keys(conn: sqlite3.Connection, table: str) -> list[str]:
    cursor = conn.execute(f"PRAGMA table_info('{table}')")
    return [row[1] for row in cursor.fetchall() if row[5] > 0]  # row[5] = pk index


def get_row_count(conn: sqlite3.Connection, table: str) -> int:
    cursor = conn.execute(f"SELECT COUNT(*) FROM '{table}'")
    return cursor.fetchone()[0]


def has_existing_data(conn: sqlite3.Connection, table: str) -> bool:
    return get_row_count(conn, table) > 0


def migrate_table(old_conn: sqlite3.Connection, new_conn: sqlite3.Connection, table: str, batch_size: int = 500,
                  conflict_cols: list[str] | None = None) -> dict:
    update_sql = None
    update_idx = 0
    conflict_idx = 0
    where_clause = ""

    old_cols = get_columns(old_conn, table)
    new_cols = get_columns(new_conn, table)
    pk_cols = get_primary_keys(new_conn, table)

    common_cols = [col for col in new_cols if col in old_cols]
    removed_cols = [col for col in old_cols if col not in new_cols]
    added_cols = [col for col in new_cols if col not in old_cols]

    if not common_cols:
        return {
            "status": "skipped",
            "reason": "No common columns found between old and new table",
            "rows_migrated": 0,
            "rows_updated": 0,
            "removed_cols": removed_cols,
            "added_cols": added_cols,
            "had_existing_data": False,
        }

    existing_rows = get_row_count(new_conn, table)
    table_had_data = existing_rows > 0

    col_list = ", ".join(f'"{c}"' for c in common_cols)
    placeholders = ", ".join("?" for _ in common_cols)
    select_sql = f"SELECT {col_list} FROM '{table}'"

    if conflict_cols:
        update_cols = [c for c in common_cols if c not in conflict_cols]
        where_clause = " AND ".join(f'"{c}"=?' for c in conflict_cols)

        if update_cols:
            set_clause = ", ".join(f'"{c}"=?' for c in update_cols)
            update_sql = f"UPDATE '{table}' SET {set_clause} WHERE {where_clause}"

        insert_sql = f"INSERT OR IGNORE INTO '{table}' ({col_list}) VALUES ({placeholders})"

        col_idx = {c: i for i, c in enumerate(common_cols)}
        update_idx = [col_idx[c] for c in update_cols]
        conflict_idx = [col_idx[c] for c in conflict_cols]
        mode = "upsert"
    elif table_had_data and pk_cols:
        insert_sql = f"INSERT OR REPLACE INTO '{table}' ({col_list}) VALUES ({placeholders})"
        mode = "upsert"
    else:
        insert_sql = f"INSERT OR IGNORE INTO '{table}' ({col_list}) VALUES ({placeholders})"
        mode = "insert"

    total_rows = get_row_count(old_conn, table)
    migrated = 0

    old_cursor = old_conn.execute(select_sql)

    while True:
        rows = old_cursor.fetchmany(batch_size)
        if not rows:
            break

        if conflict_cols:
            for row in rows:
                if update_sql:
                    update_params = tuple(row[i] for i in update_idx) + tuple(row[i] for i in conflict_idx)
                    cur = new_conn.execute(update_sql, update_params)
                    if cur.rowcount == 0:
                        new_conn.execute(insert_sql, row)
                else:
                    cur = new_conn.execute(
                        f"SELECT 1 FROM '{table}' WHERE {where_clause}",
                        tuple(row[i] for i in conflict_idx),
                    )
                    if cur.fetchone() is None:
                        new_conn.execute(insert_sql, row)
        else:
            new_conn.executemany(insert_sql, rows)

        migrated += len(rows)
        print(f"    {migrated}/{total_rows} rows ...", end="\r")

    new_conn.commit()

    new_row_count = get_row_count(new_conn, table)
    rows_inserted = new_row_count - existing_rows if mode == "upsert" else migrated
    rows_updated = migrated - rows_inserted if mode == "upsert" else 0
    print(f"    {migrated}/{total_rows} rows processed.   ")

    return {
        "status": "ok",
        "mode": mode,
        "rows_migrated": migrated,
        "rows_inserted": rows_inserted,
        "rows_updated": rows_updated,
        "removed_cols": removed_cols,
        "added_cols": added_cols,
        "had_existing_data": table_had_data,
    }


def migrate(old_db_path: str, new_db_path: str):
    if not os.path.exists(old_db_path):
        print(f"[ERROR] Old database not found: {old_db_path}")
        sys.exit(1)

    if not os.path.exists(new_db_path):
        print(f"[ERROR] New database not found: {new_db_path}")
        sys.exit(1)

    print("=" * 60)
    print(f"  SQLite Migration – {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print(f"  Old: {old_db_path}")
    print(f"  New: {new_db_path}")
    print("=" * 60)

    old_conn = sqlite3.connect(old_db_path)
    new_conn = sqlite3.connect(new_db_path)

    old_tables = set(get_tables(old_conn))
    new_tables = set(get_tables(new_conn))

    tables_to_migrate = old_tables & new_tables
    only_in_old = old_tables - new_tables
    only_in_new = new_tables - old_tables

    print(f"\nTables in old DB:    {len(old_tables)}")
    print(f"Tables in new DB:    {len(new_tables)}")
    print(f"Tables to migrate:   {len(tables_to_migrate)}")

    if only_in_old:
        print(f"\n  [WARNING] Only in old DB (will be skipped):")
        for t in sorted(only_in_old):
            print(f"    - {t}")

    if only_in_new:
        print(f"\n  [INFO] Only in new DB (will remain untouched):")
        for t in sorted(only_in_new):
            print(f"    - {t}")

    print()

    results = {}
    for table in sorted(tables_to_migrate):
        existing = get_row_count(new_conn, table)
        custom_cc = CUSTOM_CONFLICT_COLS.get(table)

        if custom_cc:
            mode_hint = f"  [conflict key: {', '.join(custom_cc)}]"
        elif existing > 0:
            mode_hint = f"  [has {existing} existing rows → upsert]"
        else:
            mode_hint = ""

        print(f"  Table: {table}{mode_hint}")

        result = migrate_table(old_conn, new_conn, table, conflict_cols=custom_cc)
        results[table] = result

        if result["status"] == "skipped":
            print(f"    [SKIPPED] {result['reason']}")
        else:
            if result["had_existing_data"] or custom_cc:
                print(f"    Mode:                        upsert (update + insert)")
                print(f"    Rows updated:                {result['rows_updated']}")
                print(f"    Rows newly inserted:         {result['rows_inserted']}")
            if result["removed_cols"]:
                print(f"    Removed columns (ignored):   {result['removed_cols']}")
            if result["added_cols"]:
                print(f"    New columns (left empty):    {result['added_cols']}")
        print()

    print("=" * 60)
    print(f"  {'SUMMARY':<34} {'ROWS':>6}  {'UPDATED':>8}  {'INSERTED':>9}")
    print("=" * 60)
    total_rows = total_updated = total_inserted = 0

    for table, result in results.items():
        status = "✓" if result["status"] == "ok" else "–"
        rows = result["rows_migrated"]
        updated = result.get("rows_updated", 0)
        inserted = result.get("rows_inserted", rows)
        total_rows += rows
        total_updated += updated
        total_inserted += inserted
        print(f"  {status}  {table:<32} {rows:>6}  {updated:>8}  {inserted:>9}")

    print("-" * 60)
    print(f"     {'TOTAL':<32} {total_rows:>6}  {total_updated:>8}  {total_inserted:>9}")
    print("=" * 60)
    print("  Migration complete.")
    print()

    old_conn.close()
    new_conn.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage:   python migrate_sqlite.py <old_db> <new_db>")
        print("Example: python migrate_sqlite.py old.db new.db")
        sys.exit(1)

    migrate(sys.argv[1], sys.argv[2])
