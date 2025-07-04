from flask import request
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
        temp = {
            "PackageIdentifier": p['PACKAGE_ID'],
            "PackageName": p['PACKAGE_NAME'],
            "Publisher": p['PACKAGE_PUBLISHER'],
            "Versions": [{"PackageVersion": d['VERSION']} for d in db.get_All_Versions_from_Package(p['PACKAGE_ID'])]
        }

        if len(temp["Versions"]) > 0:
            data.append(temp)
    del db
    return data


def generate_Installer_Manifest(package_id: str, version: str, auth_token: str = "") -> dict | list:
    db = SQLiteDatabase()
    package = db.get_specific_Package(package_id, version)
    blacklist = db.get_Blacklist_for_client(auth_token)

    if len(package) > 0 and package[0][0] not in blacklist:
        data = {
                    "PackageIdentifier": package[0][0],
                    "Versions": [{
                        "PackageVersion": package[0][5],
                        "DefaultLocale": {
                            "PackageLocale": package[0][4],
                            "Publisher": package[0][2],
                            "PackageName": package[0][1],
                            "ShortDescription": package[0][3],
                        },
                        "Installers": []
                    }]
                }
        for p in package:
            dum_data = {
                    "Architecture": p[6],
                    "InstallerType": p[7],
                    "InstallerUrl": f"https://{request.host}/api/download/{p[8]}",
                    "InstallerSha256": p[9],
                    "Scope": p[10],
                    "InstallerSwitches": db.get_Package_Switche(p[11])
                }

            #ToDo if p[7] == "zip":
            #    data["NestedInstallerType"] =
            #    data["NestedInstallerFiles"] =

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


def authenticate_Client(token: str, ip: str, settings: dict) -> bool:
    db = SQLiteDatabase()
    data = db.authenticate_client(token)

    if data:
        hostname = get_hostname_from_ip_dns(ip, settings.get('DNS_SERVER', '192.168.1.1'))
        if hostname.upper() == data['NAME'] and data['ENABLED'] == 1:
            db.update_Client_Informations(ip, datetime.now().strftime("%d.%m.%Y %H:%M:%S"), data['UID'])
            del db
            return True
    del db
    return False

def write_log(client_ip: str, package_name: str, log_type: str):
    db = SQLiteDatabase()
    client = db.get_Client_by_IP(client_ip)
    package = db.get_specfic_Versions_from_Package(package_name.split(".")[0])

    if len(client) == 0:
        client = {"UID": "EXTERN", "NAME": request.remote_addr}

    match log_type:
        case "INSTALLATION/UPDATE":
            text = f"Client: {client['NAME']} downloaded the following package: {package['PACKAGE_ID']} - {package['VERSION']}"
        case _:
            text = f"Client: {client['NAME']} did something unknown!"

    db.insert_Log(client['UID'], log_type, text, datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
    del db
