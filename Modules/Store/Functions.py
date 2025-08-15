import os
import time
import zipfile
import yaml
import requests
import datetime

from pathlib import Path

from Modules.Database.Database import SQLiteDatabase
from Modules.Database.Store_DB import StoreDB
from Modules.Functions import parse_version, get_file_edit_date
from settings import PATH_WINGET_REPOSITORY, PATH_WINGET_REPOSITORY_DB, URL_WINGET_REPOSITORY, PATH_FILES


#SQL-DB
def get_All_Packages_from_DB(search: str = "") -> list:
    download_source_msix()

    db = StoreDB()
    packages = db.get_All_Packages_from_DB(search)
    del db
    return packages


def check_for_new_Version(packages: list) -> tuple[list[dict], bool]:
    download_source_msix()

    db = StoreDB()
    ddb = SQLiteDatabase()

    update_status = False
    for p in packages:
        a_v = db.get_Package_Versions(p['PACKAGE_ID'])
        c_v = [v['VERSION'] for v in ddb.get_All_Versions_from_Package(p['PACKAGE_ID'])]
        available_versions = sorted(a_v, key=parse_version, reverse=True)
        current_versions = sorted(c_v, key=parse_version, reverse=True)

        if current_versions and available_versions:
            available = parse_version(available_versions[0])
            current = parse_version(current_versions[0])
            if available > current:
                p['NEW_VERSION'] = [True, current_versions[0], available_versions[0]]
                update_status = True
            else:
                p['NEW_VERSION'] = [False, current_versions[0], available_versions[0]]
        else:
            p['NEW_VERSION'] = [False, "", ""]

    del db, ddb
    return packages, update_status


def get_package_path(package_id: str, version: str) -> tuple[str, str]:
    db = StoreDB()
    p_path = db.get_Package_Path(package_id, version)
    del db
    return "/".join(p_path), f'{"_".join(p_path)}.yaml'


#Requests, etc.
def download_source_msix(update: bool = False) -> bool:
    if not os.path.exists(PATH_WINGET_REPOSITORY_DB) or update:
        try:
            response = requests.get(f"{URL_WINGET_REPOSITORY}/source.msix", stream=True)
            if response.status_code == 200:
                if not os.path.exists(PATH_WINGET_REPOSITORY):
                    os.makedirs(PATH_WINGET_REPOSITORY)

                f_path = os.path.join(PATH_WINGET_REPOSITORY, "source.msix")
                with open(f_path, "wb") as f:
                    f.write(response.content)

                time.sleep(1)

                with zipfile.ZipFile(f_path, "r") as zip_ref:
                    zip_ref.extractall(PATH_WINGET_REPOSITORY)
                time.sleep(1.5)
                return True
            return False
        except:
            return False
    return False


def get_All_InstallerInfos_from_Manifest(p_path: str, manifest_name: str) -> dict:
    manifest = {}
    m_path = os.path.join(PATH_WINGET_REPOSITORY, "Manifests", manifest_name)

    if os.path.exists(m_path):
        with open(m_path, 'r', encoding='utf-8') as f:
            manifest = yaml.safe_load(f)
    else:
        r = requests.get(f"{URL_WINGET_REPOSITORY}{p_path}")
        if r.status_code == 200:
            manifest = yaml.safe_load(r.text)

            os.makedirs(os.path.join(PATH_WINGET_REPOSITORY, "Manifests"), exist_ok=True)
            with open(m_path, "w", encoding="utf-8") as f:
                yaml.dump(manifest, f, default_flow_style=False, allow_unicode=True)

    if manifest:
        installer = manifest.get("Installers", [])
        for i in installer:
            if i.get("InstallerType", '') == '':
                i["InstallerType"] = manifest.get("InstallerType", '')
            if i.get("InstallerSwitches", '') == '':
                i["InstallerSwitches"] = manifest.get("InstallerSwitches", {})

        p_infos = {"Packagename": manifest.get("PackageName", ""), "Author": manifest.get("Author", ""),
                   "Description": manifest.get("ShortDescription", ""), "Locale": manifest.get("PackageLocale", "en-US"),
                   "Scope": manifest.get("Scope", "machine"), "Installers": installer}
        return p_infos
    return manifest


def download_file(url: str, filename: str) -> bool:
    response = requests.get(url)

    if response.status_code == 200:
        with open(Path(PATH_FILES) / filename, 'wb') as f:
            f.write(response.content)
        return True
    else:
        return False


#Update
def update_store_db(days: int = 2):
    if not os.path.exists(PATH_WINGET_REPOSITORY_DB):
        return

    edit_date = get_file_edit_date(PATH_WINGET_REPOSITORY_DB)
    diff = datetime.datetime.now() - edit_date

    if diff.days >= days:
        download_source_msix(True)
