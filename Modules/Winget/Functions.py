from flask import request

from Modules.Database.Database import SQLiteDatabase


def generate_search_Manifest(search_text: str, match_typ: str, match_field: str) -> list:
    db = SQLiteDatabase()
    packages = db.search_packages(search_text, match_typ, match_field)

    data = []
    for p in packages:
        temp = {
            "PackageIdentifier": p[0],
            "PackageName": p[1],
            "Publisher": p[2],
            "Versions": [{"PackageVersion": d['Version']} for d in db.get_All_Verions_from_Package(p[0])]
        }
        data.append(temp)

    del db
    return data


def generate_Installer_Manifest(package_id: str, version: str) -> dict:
    db = SQLiteDatabase()
    package = db.get_specific_Package(package_id, version)

    if len(package) > 0:
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
    else:
        data = {}

    del db
    return data


def filter_entries_by_package_match_field(data: list[dict]):
    filtered_data = [entry for entry in data if 'PackageMatchField' in entry and entry['PackageMatchField'] in ["PackageName", "NormalizedPackageNameAndPublisher", "PackageIdentifier"]]
    return filtered_data


def get_winget_Settings(s: bool = False) -> dict:
    db = SQLiteDatabase()
    data = db.get_winget_Settings(s)
    del db
    return data
