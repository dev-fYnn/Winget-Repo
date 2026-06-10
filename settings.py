import os
import sys


BASE_DIR = sys.path[0]

# Paths / Settings
URL_PACKAGE_DOWNLOAD = "DEFAULT"
PATH_FILES = os.path.join(BASE_DIR, "Files")
PATH_LOGOS = os.path.join(PATH_FILES, "Logos")
PATH_DATABASE = os.path.join(BASE_DIR, "Modules", "Database", "Database.db")

# Paths Store
PATH_WINGET_REPOSITORY = os.path.join(BASE_DIR, "Winget_DB")
PATH_WINGET_REPOSITORY_DB = os.path.join(PATH_WINGET_REPOSITORY, "Public", "index.db")
URL_WINGET_REPOSITORY = "https://cdn.winget.microsoft.com/cache/"

#Pre Indexed
PATH_PREINDEXED_FILES = os.path.join(PATH_FILES, "PreIndexed_Files")
PATH_CERTIFICATES = os.path.join(PATH_FILES, "PreIndexed")
PATH_PACKER_TOOL = "DEFAULT"
PATH_SIGNING_TOOL = "DEFAULT"

#Plugins
PATH_PLUGINS = os.path.join(BASE_DIR, "Plugins")
