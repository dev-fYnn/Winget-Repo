import os
import sys

PATH_LOGOS = fr"{sys.path[0]}\static\images\Logos"
PATH_FILES = fr"{sys.path[0]}\Files"
PATH_DATABASE = rf"{sys.path[0]}\Modules\Database\Database.db"

PATH_WINGET_REPOSITORY = fr"{sys.path[0]}\Winget_DB"
PATH_WINGET_REPOSITORY_DB = os.path.join(PATH_WINGET_REPOSITORY, "Public", "index.db")
URL_WINGET_REPOSITORY = "https://cdn.winget.microsoft.com/cache/"
