import re
import unicodedata
import os

from datetime import datetime

from settings import PATH_PREINDEXED_FILES


def increment_appx_version(current_version: str) -> str:
    now = datetime.now()
    year, month, day = now.year, now.month, now.day

    v_parts = current_version.split('.')
    if len(v_parts) != 4:
        return f"{year}.{month}.{day}.1"

    old_year = int(v_parts[0])
    old_month = int(v_parts[1])
    old_day = int(v_parts[2])
    old_rev = int(v_parts[3])

    if old_year == year and old_month == month and old_day == day:
        new_rev = old_rev + 1
    else:
        new_rev = 1
    return f"{year}.{month}.{day}.{new_rev}"


def normalize_name(name: str) -> str:
    if not name:
        return ""
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^a-zA-Z0-9]+", " ", ascii_str)
    return cleaned.strip().lower()


def generate_appxmanifest(version: str, servername: str):
    manifest = f"""<?xml version="1.0" encoding="utf-8"?>
<Package xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
         xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
         xmlns:uap3="http://schemas.microsoft.com/appx/manifest/uap/windows10/3"
         IgnorableNamespaces="uap uap3">

  <Identity Name="WingetRepo.Indexed.Source"
            ProcessorArchitecture="neutral"
            Publisher="CN=Winget-Repo"
            Version="{version}" />

  <Properties>
    <DisplayName>{servername} Indexed Source</DisplayName>
    <PublisherDisplayName>Winget-Repo</PublisherDisplayName>
    <Logo>Assets\AppPackageStoreLogo.png</Logo>
  </Properties>

  <Dependencies>
    <TargetDeviceFamily Name="Windows.Universal" MinVersion="10.0.16299.0" MaxVersionTested="10.0.18287.0" />
  </Dependencies>

  <Applications>
    <Application Id="SourceData">
      <uap:VisualElements DisplayName="{servername} Indexed Source"
                          Square150x150Logo="Assets\AppPackageStoreLogo.scale-150.png"
                          Square44x44Logo="Assets\AppPackageStoreLogo.scale-100.png"
                          Description="{servername} Indexed Source"
                          BackgroundColor="#FFFFFF"
                          AppListEntry="none" />
      <Extensions>
        <uap3:Extension Category="windows.appExtension">
          <uap3:AppExtension Name="com.microsoft.winget.source"
                             Id="IndexDB"
                             DisplayName="{servername} Indexed Source"
                             Description="{servername} Indexed Source"
                             PublicFolder="Public">
          </uap3:AppExtension>
        </uap3:Extension>
      </Extensions>
    </Application>
  </Applications>

  <Resources>
    <Resource Language="und" />
  </Resources>

</Package>"""

    with open(os.path.join(PATH_PREINDEXED_FILES, "AppxManifest.xml"), "w", encoding="utf-8") as f:
        f.write(manifest)
