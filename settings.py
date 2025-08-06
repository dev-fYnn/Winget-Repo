import os
import sys

from dotenv import load_dotenv


#------------------Normal Settings----------------------
BASE_DIR = sys.path[0]

# Paths / Settings
URL_PACKAGE_DOWNLOAD = "DEFAULT"
PATH_LOGOS = os.path.join(BASE_DIR, "static", "images", "Logos")
PATH_FILES = os.path.join(BASE_DIR, "Files")
PATH_DATABASE = os.path.join(BASE_DIR, "Modules", "Database", "Database.db")

# Paths Store
PATH_WINGET_REPOSITORY = os.path.join(BASE_DIR, "Winget_DB")
PATH_WINGET_REPOSITORY_DB = os.path.join(PATH_WINGET_REPOSITORY, "Public", "index.db")
URL_WINGET_REPOSITORY = "https://cdn.winget.microsoft.com/cache/"


#------------------Sensitive Settings---------------
# load .env-file
load_dotenv()

# get values from .env-file
