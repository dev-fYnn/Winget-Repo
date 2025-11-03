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


def generate_Installer_Manifest(package_id: str, version: str, channel: str, auth_token: str = "") -> dict | list:
    db = SQLiteDatabase()
    package = db.get_specific_Package(package_id, version, channel)
    blacklist = db.get_Blacklist_for_client(auth_token)

    if len(package) > 0 and package[0]['PACKAGE_ID'] not in blacklist:
        data = {
                    "PackageIdentifier": package[0]['PACKAGE_ID'],
                    "Versions": [{
                        "PackageVersion": package[0]['VERSION'],
                        #"Channel": package[0]['CHANNEL'],
                        "DefaultLocale": {
                            "PackageLocale": package[0]['LOCALE'],
                            "Publisher": package[0]['PACKAGE_PUBLISHER'],
                            "PackageName": package[0]['PACKAGE_NAME'],
                            "ShortDescription": package[0]['PACKAGE_DESCRIPTION'],
                        },
                        "Installers": []
                    }]
                }
        for p in package:
            key = (p['INSTALLER_TYPE'], p['ARCHITECTURE'], p['INSTALLER_SCOPE'])
            if key in data['Versions'][0]['Installers']:
                continue

            dum_data = {
                    "Architecture": p['ARCHITECTURE'],
                    "InstallerType": p['INSTALLER_TYPE'],
                    "InstallerUrl": url_for("winget_routes.download", package_name=p['INSTALLER_URL'], _external=True),
                    "InstallerSha256": p['INSTALLER_SHA256'],
                    "Scope": p['INSTALLER_SCOPE'],
                    "InstallerSwitches": db.get_Package_Switche(p['UID'])
                }

            if len(p['PACKAGE_FAMILY_NAME']) > 0:
                dum_data["PackageFamilyName"] = p['PACKAGE_FAMILY_NAME']

            if len(p['PRODUCTCODE']) > 0:
                dum_data["ProductCode"] = p['PRODUCTCODE']

                if len(p['UPGRADECODE']) > 0:
                    dum_data["AppsAndFeaturesEntries"] = [
                        {
                            "ProductCode": p['PRODUCTCODE'],
                            "UpgradeCode": p['UPGRADECODE'],
                        }
                    ]

            if p['INSTALLER_TYPE'] == "zip":
                dum_data["NestedInstallerType"] = p['INSTALLER_NESTED_TYPE']
                dum_data["NestedInstallerFiles"] = db.get_Nested_Installer(p['UID'])

            data['Versions'][0]['Installers'].append(dum_data)
        output = {"Data": data}
    else:
        output = {}

    del db
    return output


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
