# ⚙️ Winget-Repo URL and Path Configuration via `settings.py`

This document outlines configuration options available exclusively through the `settings.py` file located in the root directory of the Winget-Repo project.

> ⚠️ Changes made to these settings require a **restart** of the repository/server to take effect.

---

## 🔧 Configuration Options

| **Variable**                | **Description**                                                                                         |
|-----------------------------|---------------------------------------------------------------------------------------------------------|
| `PATH_LOGOS`                | File path to logo images used in the repository.                                                        |
| `PATH_FILES`                | Directory path where uploaded or served files are stored.                                               |
| `PATH_DATABASE`             | Location of the internal application database.                                                          |
| `URL_PACKAGE_DOWNLOAD`      | Base URL for downloading packages. `"DEFAULT"` uses internal logic.                                     |
| `PATH_WINGET_REPOSITORY`    | File path to the local Winget repository root directory. (Package Store)                                |
| `PATH_WINGET_REPOSITORY_DB` | Path to the Winget public `index.db` used for the package store. (Package Store)                        |
| `URL_WINGET_REPOSITORY`     | External URL used to download the newest index.db from the winget community repository (Package Store). |

---

## 🔁 Restart Requirement

All changes to `settings.py` require a full **restart of the Winget-Repo server** to be applied. Make sure to save your changes and reboot the service after editing.

---

## 📁 Change Package Download URL

To use an external URL for package downloads, modify the `URL_PACKAGE_DOWNLOAD` setting in `settings.py`.

Default = Build in file serving 

The URL should follow this format:  
`https://your-domain.com/PACKAGE_NAME + FILE_EXTENSION`  
For example: `https://example.com/installer.exe`

> 🔁 **Note:** If you change the download URL, you may also need to adjust the `PATH_FILES` setting to reflect the new file storage location, especially if you're no longer serving files from the local machine.

