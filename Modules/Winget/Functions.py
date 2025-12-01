from flask import url_for
from datetime import datetime

from Modules.Database.Database import SQLiteDatabase
from Modules.Functions import get_hostname_from_ip_dns


def generate_search_Manifest(search_text: str, match_typ: str, match_field: str, auth_token: str = "") -> list:
    db = SQLiteDatabase()
    packages = db.search_packages(search_text, match_typ, match_field)

    if auth_token != "":
        blacklist = db.get_Blacklist_for_client(auth_token)
        packages = [p for p in packages if p['PACKAGE_ID'] not in blacklist]

    data = []
    for p in packages:
        versions = []

        for d in db.get_All_Versions_from_Package(p['PACKAGE_ID']):
            version_info = {
                "PackageVersion": d['VERSION'],
                #"Channel": d['CHANNEL'],
                "PackageFamilyNames": [],
                "ProductCodes": [],
                "UpgradeCodes": [],
                "AppsAndFeaturesEntryVersions": []
            }

            if len(d['PRODUCTCODE']) > 0:
                version_info["ProductCodes"] = [d['PRODUCTCODE']]

            if len(d['UPGRADECODE']) > 0:
                version_info["UpgradeCodes"] = [d['UPGRADECODE']]

            if len(d['PACKAGE_FAMILY_NAME']) > 0:
                version_info["PackageFamilyNames"] = [d['PACKAGE_FAMILY_NAME']]

            versions.append(version_info)

        temp = {
            "PackageIdentifier": p['PACKAGE_ID'],
            "PackageName": p['PACKAGE_NAME'],
            "Publisher": p['PACKAGE_PUBLISHER'],
            "Versions": versions
        }

        if len(temp["Versions"]) > 0:
            data.append(temp)
    del db
    return data


def generate_Installer_Manifest(package_id: str, version: str = None, channel: str = None, auth_token: str = "") -> dict:
    db = SQLiteDatabase()
    package = db.get_specific_Package(package_id, version, channel)
    blacklist = db.get_Blacklist_for_client(auth_token)

    versions = []
    if package and package['PACKAGE_ID'] not in blacklist:
        for version_group in package['VERSIONS']:
            version_info = _build_version_info(version_group, package, db)
            if version_info:
                versions.append(version_info)
    del db

    if package:
        r_data = {
            "Data": {
                "PackageIdentifier": package['PACKAGE_ID'],
                "Versions": versions
            }
        }
    else:
        r_data = {}
    return r_data


def _build_version_info(version_group: list, package: dict, db: SQLiteDatabase) -> dict:
    first_installer = version_group[0]

    installers = []
    for installer_data in version_group:
        installer = _build_installer_entry(installer_data, db)
        if installer:
            installers.append(installer)

    return {
        "PackageVersion": first_installer.get('VERSION', '0.0.0.0'),
        # "Channel": first_installer.get('CHANNEL', 'stable')
        "DefaultLocale": {
            "PackageLocale": first_installer.get('LOCALE', 'en-US'),
            "Publisher": package.get('PACKAGE_PUBLISHER', ''),
            "PackageName": package.get('PACKAGE_NAME', ''),
            "ShortDescription": package.get('PACKAGE_DESCRIPTION', ''),
        },
        "Installers": installers
    }


def _build_installer_entry(installer_data: dict, db: SQLiteDatabase) -> dict:
    installer = {
        "Architecture": installer_data.get('ARCHITECTURE', 'x64'),
        "InstallerType": installer_data.get('INSTALLER_TYPE', ''),
        "InstallerUrl": url_for("winget_routes.download", package_name=installer_data.get('INSTALLER_URL', ''), _external=True),
        "InstallerSha256": installer_data.get('INSTALLER_SHA256', ''),
        "Scope": installer_data.get('INSTALLER_SCOPE', 'machine'),
        "InstallerSwitches": db.get_Package_Switche(installer_data.get('UID'))
    }

    package_family_name = installer_data.get('PACKAGE_FAMILY_NAME', '')
    if package_family_name:
        installer["PackageFamilyName"] = package_family_name

    product_code = installer_data.get('PRODUCTCODE', '')
    if product_code:
        installer["ProductCode"] = product_code

        upgrade_code = installer_data.get('UPGRADECODE', '')
        if upgrade_code:
            installer["AppsAndFeaturesEntries"] = [{
                "ProductCode": product_code,
                "UpgradeCode": upgrade_code,
            }]

    if installer_data['INSTALLER_TYPE'] == "zip":
        installer["NestedInstallerType"] = installer_data['INSTALLER_NESTED_TYPE']
        installer["NestedInstallerFiles"] = db.get_Nested_Installer(installer_data['UID'])
    return installer


def filter_entries_by_package_match_field(data: list[dict]):
    filtered_data = [entry for entry in data if 'PackageMatchField' in entry and entry['PackageMatchField'] in ["PackageName", "NormalizedPackageNameAndPublisher", "PackageIdentifier"]]
    return filtered_data


def get_winget_Settings(s: bool = False) -> dict:
    db = SQLiteDatabase()
    data = db.get_winget_Settings(s)
    del db
    return data


def authenticate_Client(token: str, ip: str, settings: dict, client: int = 0) -> bool:
    db = SQLiteDatabase()
    data = db.authenticate_client(token)

    if data:
        hostname = get_hostname_from_ip_dns(ip, settings.get('DNS_SERVER', '192.168.1.1'))
        if hostname.upper() == data['NAME'] and data['ENABLED'] == 1:
            db.update_Client_Informations(ip, datetime.now().strftime("%d.%m.%Y %H:%M:%S"), data['UID'], client)
            del db
            return True
    del db
    return False


def ip_to_int(ip):
    parts = ip.strip().split('.')
    if len(parts) != 4:
        raise ValueError("Invalid IPv4")
    return (int(parts[0]) << 24) | (int(parts[1]) << 16) | \
           (int(parts[2]) << 8) | int(parts[3])


def authorize_IP_Range(ip: str) -> bool:
    if ":" in ip:
        return False

    db = SQLiteDatabase()
    settings = db.get_winget_Settings()
    del db

    ip_ranges = settings.get('IP_RESTRICTION', 'DEFAULT').upper()
    if ip_ranges.upper() == "DEFAULT":
        return True

    if ";" in ip_ranges:
        ip_ranges = ip_ranges.split(";")
    elif "," in ip_ranges:
        ip_ranges = ip_ranges.split(",")
    else:
        ip_ranges = [ip_ranges]

    try:
        ip_int = ip_to_int(ip)
    except ValueError:
        return False

    for ip_range in ip_ranges:
        ip_range = ip_range.strip()
        if '-' in ip_range:
            start, end = [x.strip() for x in ip_range.split('-')]
            if ip_to_int(start) <= ip_int <= ip_to_int(end):
                return True
        else:
            if ip_int == ip_to_int(ip_range):
                return True
    return False


def write_log(client_ip: str, package_name: str, log_type: str):
    db = SQLiteDatabase()
    client = db.get_Client_by_IP(client_ip)
    package = db.get_specfic_Versions_from_Package(package_name.split(".")[0])

    if len(package) == 0:
        package = {"PACKAGE_ID": package_name, "VERSION": "Unknown"}

    if len(client) == 0:
        client = {"UID": "EXTERN", "NAME": client_ip}

    match log_type:
        case "INSTALLATION/UPDATE":
            text = f"Client: {client['NAME']} downloaded the following package: {package['PACKAGE_ID']} - {package['VERSION']}"
        case _:
            text = f"Client: {client['NAME']} did something unknown!"

    db.insert_Log(client['UID'], log_type, text, datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
    del db
