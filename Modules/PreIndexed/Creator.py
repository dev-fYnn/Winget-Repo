import os
import platform

from datetime import datetime
from msix import MsixPacker

from Modules.Database.Database import SQLiteDatabase
from Modules.Encryption import decrypt_text
from Modules.Functions import get_file_edit_date
from Modules.PreIndexed.DB_Generator import WingetIndexBuilder
from Modules.PreIndexed.Functions import generate_appxmanifest, increment_appx_version
from settings import PATH_PREINDEXED_FILES, PATH_CERTIFICATES, PATH_PACKER_TOOL, PATH_SIGNING_TOOL


def generate_indexed_db_package(enc_key: bytes) -> tuple[str, str]:
    with SQLiteDatabase() as db:
        settings = db.get_winget_Settings()
        current_version = settings['INDEXED_DB_VERSION']
        version = increment_appx_version(current_version)
        db.update_wingetrepo_Setting("INDEXED_DB_VERSION", version)

    generate_appxmanifest(version, settings.get('SERVERNAME', 'Winget-Repo'))

    index_db = WingetIndexBuilder()
    index_db.build()

    if PATH_PACKER_TOOL.upper() == "DEFAULT" and PATH_SIGNING_TOOL.upper() == "DEFAULT":
        msi = MsixPacker()
    elif PATH_PACKER_TOOL.upper() != "DEFAULT" and PATH_SIGNING_TOOL.upper() == "DEFAULT":
        msi = MsixPacker(binary=PATH_PACKER_TOOL)
    elif PATH_PACKER_TOOL.upper() == "DEFAULT" and PATH_SIGNING_TOOL.upper() != "DEFAULT":
        msi = MsixPacker(sign_binary=PATH_SIGNING_TOOL)
    else:
        msi = MsixPacker(binary=PATH_PACKER_TOOL, sign_binary=PATH_SIGNING_TOOL)

    try:
        msi.pack(PATH_PREINDEXED_FILES, os.path.join(PATH_CERTIFICATES, "source.msix"))
    except Exception as e:
        print(e)
        return f"Dependencies for pymsix on {platform.system()} aren't configured.", "error"

    cert_path = os.path.join(PATH_CERTIFICATES, "preindexed.pfx")
    if os.path.exists(cert_path):
        try:
            if settings.get('INDEXED_DB_PW', '0') != "0":
                db_pw = decrypt_text(enc_key, settings.get('INDEXED_DB_PW', '0'))
                msi.sign(os.path.join(PATH_CERTIFICATES, "source.msix"), cert_path, pfx_password=db_pw)
            else:
                msi.sign(os.path.join(PATH_CERTIFICATES, "source.msix"), cert_path)
        except Exception as e:
            print(e)
            return "Error signing msix package!", "error"
        return "Successfully generated MSIX Package", "success"
    else:
        return "No certificate found!", "error"


def update_pre_indexed_source(enc_key: bytes, days: int = 2) -> str:
    file = os.path.join(PATH_CERTIFICATES, "source.msix")
    if not os.path.exists(file):
        return ""

    edit_date = get_file_edit_date(file)
    diff = datetime.now() - edit_date

    if diff.days >= days:
        generate_indexed_db_package(enc_key)
    return edit_date.strftime("%d.%m.%Y %H:%M")
