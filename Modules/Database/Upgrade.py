import sqlite3

from settings import PATH_DATABASE


def get_tables_and_columns(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cur.fetchall() if row[0] != "sqlite_sequence"]

    schema = {}
    for table in tables:
        cur.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cur.fetchall()]
        schema[table] = columns

    conn.close()
    return schema


def migrate_db(old_db, new_db, update_tables=None, key_columns=None, skip_key_values=None):
    if update_tables is None:
        update_tables = []
    if key_columns is None:
        key_columns = {}
    if skip_key_values is None:
        skip_key_values = {}

    old_conn = sqlite3.connect(old_db)
    new_conn = sqlite3.connect(new_db)

    old_cur = old_conn.cursor()
    new_cur = new_conn.cursor()

    old_schema = get_tables_and_columns(old_db)
    new_schema = get_tables_and_columns(new_db)

    for table, old_cols in old_schema.items():
        if table not in new_schema:
            print(f"⚠️ Tabelle {table} existiert in neuer DB nicht – überspringe.")
            continue

        new_cols = new_schema[table]
        common_cols = [c for c in old_cols if c in new_cols]

        if not common_cols:
            print(f"⚠️ Keine gemeinsamen Spalten in {table} – überspringe.")
            continue

        col_str = ", ".join([f'"{c}"' for c in common_cols])
        placeholders = ", ".join(["?"] * len(common_cols))

        old_cur.execute(f'SELECT {col_str} FROM "{table}"')
        rows = old_cur.fetchall()

        if table in update_tables:
            key_col = key_columns.get(table)
            if not key_col:
                print(f"⚠️ Kein Schlüssel für Update-Tabelle {table} definiert – überspringe.")
                continue

            skipped = 0
            updated = 0

            for row in rows:
                data = dict(zip(common_cols, row))

                if table in skip_key_values and data[key_col] in skip_key_values[table]:
                    skipped += 1
                    continue

                set_clause = ", ".join([f'"{c}"=?' for c in common_cols if c != key_col])
                values = [data[c] for c in common_cols if c != key_col]
                values.append(data[key_col])
                new_cur.execute(f'UPDATE "{table}" SET {set_clause} WHERE "{key_col}" = ?', values)
                updated += 1
            print(f"🔄 {updated} Reihen in {table} aktualisiert (⏭ {skipped} übersprungen).")
        else:
            for row in rows:
                new_cur.execute(f'INSERT INTO "{table}" ({col_str}) VALUES ({placeholders})',row)
            print(f"✅ {len(rows)} Datensätze in {table} eingefügt.")

    new_conn.commit()
    old_conn.close()
    new_conn.close()


if __name__ == '__main__':
    old_db = PATH_DATABASE
    old_db = old_db.replace("Database.db", "Database_old.db")
    migrate_db(old_db, PATH_DATABASE, ["tbl_FIELDS", "tbl_PACKAGES_LOCALE", "tbl_SETTINGS", "tbl_TEXTS", "tbl_USER_RIGHTS"], {"tbl_FIELDS": "FIELD_ID", "tbl_PACKAGES_LOCALE": "LOCALE_ID", "tbl_SETTINGS": "SETTING_NAME", "tbl_TEXTS": "ID", "tbl_USER_RIGHTS": "ID"}, {"tbl_SETTINGS": ["VERSION_COUNTER"]} )