import os
import sqlite3

from settings import PATH_DATABASE

# Current database version
APP_DB_VERSION = "1.0"


def init_database():
    """
    Initialize the database if it doesn't exist, or check version and upgrade if needed.
    """
    db_exists = os.path.exists(PATH_DATABASE)
    
    if not db_exists:
        # Database doesn't exist, create it
        _create_database()
    else:
        # Database exists, check version
        db_version = _get_database_version()
        
        if db_version is None:
            # VERSION table doesn't exist, need to upgrade
            print("⚠️ Database version table not found. Upgrade required.")
            _upgrade_database(None)
        elif db_version != APP_DB_VERSION:
            # Version mismatch, need to upgrade
            print(f"⚠️ Database version mismatch. Current: {db_version}, Required: {APP_DB_VERSION}. Upgrade required.")
            _upgrade_database(db_version)
        else:
            # Version matches, continue
            print(f"✅ Database version {db_version} is up to date.")


def _create_database():
    """
    Create a new database using the SQL script.
    """
    print("📦 Creating new database...")
    
    # Ensure parent directory exists
    db_dir = os.path.dirname(PATH_DATABASE)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    # Get the path to the SQL script
    sql_script_path = os.path.join(os.path.dirname(__file__), "SQL", "create-database.sql")
    
    if not os.path.exists(sql_script_path):
        raise FileNotFoundError(f"SQL script not found: {sql_script_path}")
    
    # Read and execute the SQL script
    conn = sqlite3.connect(PATH_DATABASE)
    cursor = conn.cursor()
    
    with open(sql_script_path, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    # Execute the script
    cursor.executescript(sql_script)
    conn.commit()
    conn.close()
    
    print("✅ Database created successfully.")


def _get_database_version():
    """
    Get the current database version from the VERSION table.
    Returns None if the table doesn't exist or has no data.
    """
    try:
        conn = sqlite3.connect(PATH_DATABASE)
        cursor = conn.cursor()
        
        # Check if VERSION table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='VERSION'
        """)
        
        if cursor.fetchone() is None:
            conn.close()
            return None
        
        # Get version from table
        cursor.execute("SELECT VERSION FROM VERSION LIMIT 1")
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
        return None
        
    except sqlite3.Error as e:
        print(f"⚠️ Error reading database version: {e}")
        return None


def _upgrade_database(current_version):
    """
    Upgrade the database from current_version to CURRENT_DB_VERSION.
    This is a placeholder for future upgrade logic.
    
    Args:
        current_version: The current database version (None if version table doesn't exist)
    """
    # TODO: Implement database upgrade logic
    print(f"⚠️ Database upgrade from {current_version} to {APP_DB_VERSION} is not yet implemented.")
    print("⚠️ Please backup your database before upgrading manually.")
    # raise NotImplementedError("Database upgrade functionality is not yet implemented")

