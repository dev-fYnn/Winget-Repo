from enum import Enum
from typing import Optional, Annotated
from fastapi import Form
from pydantic import BaseModel


#Add Package Version
class Locale(str, Enum):
    en_US = "en-US"
    de_DE = "de-DE"
    de_AT = "de-AT"
    de_CH = "de-CH"
    en_GB = "en-GB"
    en_CA = "en-CA"
    en_AU = "en-AU"
    fr_FR = "fr-FR"
    fr_CA = "fr-CA"
    fr_BE = "fr-BE"
    es_ES = "es-ES"
    es_MX = "es-MX"
    it_IT = "it-IT"
    it_CH = "it-CH"
    pt_PT = "pt-PT"
    pt_BR = "pt-BR"
    ja_JP = "ja-JP"
    ko_KR = "ko-KR"
    zh_CN = "zh-CN"
    zh_TW = "zh-TW"


class Architecture(str, Enum):
    x64 = "x64"
    x86 = "x86"
    neutral = "neutral"


class FileType(str, Enum):
    EXE = "EXE"
    MSI = "MSI"
    MSIX = "MSIX"
    APPX = "APPX"
    ZIP = "ZIP"
    INNO = "INNO"
    NULLSOFT = "NULLSOFT"
    WIX = "WIX"
    BURN = "BURN"


class NestedFileType(str, Enum):
    EXE = "EXE"
    MSI = "MSI"
    MSIX = "MSIX"
    APPX = "APPX"
    INNO = "INNO"
    NULLSOFT = "NULLSOFT"
    WIX = "WIX"
    BURN = "BURN"
    FONT = "FONT"


class Scope(str, Enum):
    machine = "machine"
    user = "user"


class Upgrades(str, Enum):
    install = "install"
    uninstallPrevious = "uninstallPrevious"
    deny = "deny"


async def package_version_form_data(
    package_version: Annotated[str, Form(max_length=25)],
    file_architect: Annotated[Architecture, Form()],
    file_type: Annotated[FileType, Form()],
    file_scope: Annotated[Scope, Form()],
    upgrades: Annotated[Upgrades, Form()],
    package_locale: Annotated[Locale, Form()] = Locale.en_US,
    channel: Annotated[str, Form()] = "stable",
    installer_url: Annotated[Optional[str], Form()] = None,
    file_type_nested: Annotated[Optional[NestedFileType], Form()] = None,
    file_nested_path: Annotated[Optional[list[str]], Form()] = [],
    productcode: Annotated[Optional[str], Form()] = "",
    upgradecode: Annotated[Optional[str], Form()] = "",
    package_family_name: Annotated[Optional[str], Form()] = "",
    switch_Silent: Annotated[Optional[str], Form()] = "",
    switch_SilentWithProgress: Annotated[Optional[str], Form()] = "",
    switch_Interactive: Annotated[Optional[str], Form()] = "",
    switch_InstallLocation: Annotated[Optional[str], Form()] = "",
    switch_Log: Annotated[Optional[str], Form()] = "",
    switch_Upgrade: Annotated[Optional[str], Form()] = "",
    switch_Custom: Annotated[Optional[str], Form()] = "",
    switch_Repair: Annotated[Optional[str], Form()] = "",
    dep_windows_features: Annotated[Optional[list[str]], Form()] = [],
    dep_windows_libraries: Annotated[Optional[list[str]], Form()] = [],
    dep_external: Annotated[Optional[list[str]], Form()] = [],
    dep_pkg_identifier: Annotated[Optional[list[str]], Form()] = [],
    dep_pkg_min_version: Annotated[Optional[list[str]], Form()] = [],
):
    data = {
        "package_version": package_version,
        "package_local": package_locale,
        "file_architect": file_architect,
        "file_type": file_type,
        "file_scope": file_scope,
        "upgrades": upgrades,
        "channel": channel,
        "file_type_nested": file_type_nested,
        "file_nested_path": file_nested_path,
        "productcode": productcode,
        "upgradecode": upgradecode,
        "package_family_name": package_family_name,
        "installer_url": installer_url or "",
    }
    switches = {
        "switch_Silent": switch_Silent,
        "switch_SilentWithProgress": switch_SilentWithProgress,
        "switch_Interactive": switch_Interactive,
        "switch_InstallLocation": switch_InstallLocation,
        "switch_Log": switch_Log,
        "switch_Upgrade": switch_Upgrade,
        "switch_Custom": switch_Custom,
        "switch_Repair": switch_Repair,
    }
    switches = {k: v for k, v in switches.items() if v}
    data.update(switches)

    data["dep_windows_features"]  = [v for v in (dep_windows_features or [])  if v.strip()]
    data["dep_windows_libraries"] = [v for v in (dep_windows_libraries or []) if v.strip()]
    data["dep_external"]          = [v for v in (dep_external or [])          if v.strip()]
    data["dep_package_dependencies"] = [
        {"PackageIdentifier": ident, "MinimumVersion": ver.strip() or None}
        for ident, ver in zip(dep_pkg_identifier or [], dep_pkg_min_version or [])
        if ident.strip()
    ]

    data = {k: ("" if v is None else v) for k, v in data.items()}
    return data


#Login
class LoginResponse(BaseModel):
    Bearer_Token: str


#Client Version
class ClientVersionResponse(BaseModel):
    Version: str


#Get Packages
class Package(BaseModel):
    PACKAGE_ID: int
    PACKAGE_NAME: str
    PACKAGE_PUBLISHER: str
    PACKAGE_DESCRIPTION: str
    PACKAGE_LOGO: str
    PACKAGE_ACTIVE: str
    VERSIONS: list[str]
    VERSIONS_UID: list[str]



#Get Package Version
class Package_Version(BaseModel):
    PACKAGE_ID: str
    VERSION: str
    LOCALE: str
    ARCHITECTURE: str
    INSTALLER_TYPE: str
    INSTALLER_URL: str
    INSTALLER_SHA256: str
    INSTALLER_SCOPE: str
    UID: str
    INSTALLER_NESTED_TYPE: str
    PRODUCTCODE: str
    UPGRADECODE: str
    PACKAGE_FAMILY_NAME: str
    CHANNEL: str
    NESTED_INSTALLER_PATHS: list[dict]
