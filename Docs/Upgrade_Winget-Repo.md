# 📖 Winget-Repo Upgrade Guide

Follow these steps to upgrade your Winget-Repo database and server files
safely:

------------------------------------------------------------------------

### 1. Stop the Winget-Repo server

Before performing any changes, make sure the running server process is
stopped.\
If the server is running as a service or in a console, shut it down
gracefully.

------------------------------------------------------------------------

### 2. Backup the old database

Navigate to the folder where your current database is located.\
Rename the existing database file to keep a backup:

``` bash
mv Database.db Database_old.db
```

(Use Windows Explorer or `ren Database.db Database_old.db` on Windows.)

------------------------------------------------------------------------

### 3. Replace the old server files

Download the latest Winget-Repo server files.\
Replace the old server files with the new ones you just downloaded.

⚠️ **Important:** Do **not** overwrite your `settings.py` file unless
you intentionally want to reset your configuration.\
If you made custom changes (database paths, API keys, ports, etc.), make
sure to copy those settings over to the new version.

------------------------------------------------------------------------

### 4. Run the migration script

The migration script will read data from `Database_old.db` and write it
into the new `Database.db` with the updated schema.

Run it from the project root:

``` bash
python Modules/Database/Upgrade.py
```

This will: - Copy data from the old database into the new one\
- Update configuration tables where needed\
- Skip protected rows like `VERSION_COUNTER`

------------------------------------------------------------------------

### 5. Restart the Winget-Repo server

Once migration completes successfully, start the server again with the
new files and the upgraded database.\
Verify that: - The server runs without errors\
- Data is available as expected\
- Configuration values (settings, version counter, etc.) are correct

------------------------------------------------------------------------

✅ Done! Your Winget-Repo server is now upgraded with the migrated
database.
