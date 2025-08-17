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

# Keycloak Configuration
KEYCLOAK_ENABLED = os.getenv('KEYCLOAK_ENABLED', 'false').lower() == 'true'
KEYCLOAK_SERVER_URL = os.getenv('KEYCLOAK_SERVER_URL', 'http://localhost:8080')
KEYCLOAK_REALM_NAME = os.getenv('KEYCLOAK_REALM_NAME', 'winget-repo')
KEYCLOAK_CLIENT_ID = os.getenv('KEYCLOAK_CLIENT_ID', 'winget-repo-client')
KEYCLOAK_CLIENT_SECRET = os.getenv('KEYCLOAK_CLIENT_SECRET', '')
KEYCLOAK_REDIRECT_URI = os.getenv('KEYCLOAK_REDIRECT_URI', 'http://localhost:5000/keycloak/callback')
KEYCLOAK_POST_LOGOUT_REDIRECT_URI = os.getenv('KEYCLOAK_POST_LOGOUT_REDIRECT_URI', 'http://localhost:5000/')
KEYCLOAK_DEFAULT_GROUP = os.getenv('KEYCLOAK_DEFAULT_GROUP', '')  # Default admin group


#------------------Sensitive Settings---------------
# load .env-file
load_dotenv()

# get values from .env-file
