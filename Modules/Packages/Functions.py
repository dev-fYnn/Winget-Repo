import shutil

from pathlib import Path
from uuid import uuid4
from hashlib import sha256

from Modules.Database.Database import SQLiteDatabase
from Modules.Files.Functions import delete_File
from Modules.Functions import parse_version, process_package_logo
from settings import PATH_LOGOS, PATH_FILES


# ------------------------------
# PACKAGE MANAGEMENT
# ------------------------------
def add_package_service(data: dict, file=None):
    package_id = data.get("package_id", str(uuid4()))
    if len(package_id) == 0:
        package_id = str(uuid4())

    if file:
        logo_path = f"{package_id}.png"
        dest_path = Path(PATH_LOGOS) / logo_path
        process_package_logo(file, dest_path)
    else:
        logo_path = "dummy.png"

    db = SQLiteDatabase()
    status = db.add_Package(package_id, data.get("package_name", "")[:25], data.get("package_publisher", "")[:25], data.get("package_description", "")[:150], logo_path)
    db.db_commit()
    del db
    return status, package_id


def edit_package_service(package_id: str, data: dict, file=None):
    db = SQLiteDatabase()
    if not db.check_Package_exists(package_id):
        del db
        return False, "Package not found"

    package = db.get_Package_by_ID(package_id)
    if file:
        logo_path = f"{package_id}.png"
        dest_path = Path(PATH_LOGOS) / logo_path
        process_package_logo(file, dest_path)
    else:
        logo_path = package['PACKAGE_LOGO']

    status = db.add_Package(package_id, data.get("package_name", package['PACKAGE_NAME'])[:25], data.get("package_publisher", package['PACKAGE_PUBLISHER'])[:25], data.get("package_description", package['PACKAGE_DESCRIPTION'])[:150], logo_path, int(data.get("package_active", package['PACKAGE_ACTIVE'])))
    db.db_commit()
    del db
    return status, package_id


def delete_package_service(package_id: str):
    db = SQLiteDatabase()
    if not db.check_Package_exists(package_id):
        del db
        return False

    for f in db.get_All_Versions_from_Package(package_id):
        delete_File(f['INSTALLER_URL'])
        db.delete_Package_Version(f['UID'])

    delete_File(f"{package_id}.png", PATH_LOGOS)
    db.delete_Package(package_id)
    db.db_commit(True)
    del db
    return True


# ------------------------------
# PACKAGE VERSION MANAGEMENT
# ------------------------------
def add_package_version_service(package_id: str, data: dict, file=None):
    db = SQLiteDatabase()
    if not db.check_Package_exists(package_id):
        del db
        return False, "Package doesn't exist"

    version_uid = str(uuid4())
    filename = f"{version_uid}.{file.filename.split('.')[-1]}" if file else None
    file_type = data.get('file_type', 'msi').lower()

    if file and db.check_Package_Version_not_exists(package_id, data.get("package_version", "")[:25], data.get("package_local", 1), data.get("file_architect", ""), file_type, data.get("file_scope", "")):
        f_path = Path(PATH_FILES) / filename
        file_obj = getattr(file, "file", None)
        if file_obj is None:
            file_obj = getattr(file, "stream", None)
        if file_obj is None:
            file_obj = file

        with open(f_path, "wb") as out_file:
            shutil.copyfileobj(file_obj, out_file)

        try:
            file_obj.seek(0)
        except:
            pass

        with open(f_path, 'rb') as f:
            readable_hash = sha256(f.read()).hexdigest()

        p_locale = data.get("package_local", "en-US")
        if not str(p_locale).isnumeric():
            p_locale = db.get_Locale_ID_by_Value(p_locale)

        status = db.add_Package_Version(package_id, data.get("package_version", "")[:25], p_locale, data.get("file_architect", ""), file_type, filename, readable_hash, data.get("file_scope", ""), version_uid, data.get('file_type_nested', '').lower(), data.get('productcode', ""), data.get('upgradecode', ""), data.get('package_family_name', ""), data.get('channel', "stable").lower())

        if status and file_type == "zip" and len(data.get('file_nested_path', '')) > 0:
            db.add_Nested_Installer(version_uid, 'RelativeFilePath', data.get('file_nested_path', ''))

        switches = {key.replace("switch_", ""): value for key, value in data.items() if key.startswith('switch_')}
        for s in ["Silent", "SilentWithProgress", "Interactive", "InstallLocation", "Log", "Upgrade", "Custom", "Repair"]:
            if s in switches and switches[s] != "":
                db.add_Package_Version_Switch(version_uid, s, switches[s])
        db.db_commit()
        del db
        return status, version_uid
    else:
        del db
        return False, "Package version already exists or file missing"


def delete_package_versions_service(version_ids: list):
    db = SQLiteDatabase()
    for vid in version_ids:
        url = db.get_specfic_Versions_from_Package(vid)
        if url:
            delete_File(url['INSTALLER_URL'])
            db.delete_Package_Version(vid)
    db.db_commit(True)
    del db
    return True


# ------------------------------
# GETTER Functions
# ------------------------------
def get_package_service(package_id: str):
    db = SQLiteDatabase()
    package = db.get_Package_by_ID(package_id) if db.check_Package_exists(package_id) else None
    del db
    return package


def get_all_packages_and_locales_service():
    db = SQLiteDatabase()
    packages = db.get_All_Packages()
    locales = db.get_All_Locales()
    del db
    return packages, locales


def get_package_versions_service(package_id: str):
    db = SQLiteDatabase()
    if not db.check_Package_exists(package_id):
        del db
        return []
    versions = db.get_All_Versions_from_Package(package_id)
    versions = sorted(versions, key=lambda x: parse_version(x["VERSION"]), reverse=True)
    for v in versions:
        v['SWITCHES'] = db.get_Package_Switche(v['UID'])
    del db
    return versions
