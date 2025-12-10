import os
import sys

from dotenv import load_dotenv

# Load .env-file
load_dotenv()

#------------------Normal Settings----------------------
# BASE_DIR can be overridden via environment variable, defaults to sys.path[0]
BASE_DIR = os.getenv("BASE_DIR", sys.path[0])

# Paths / Settings
URL_PACKAGE_DOWNLOAD = os.getenv("URL_PACKAGE_DOWNLOAD", "DEFAULT")
PATH_LOGOS = os.getenv("PATH_LOGOS", os.path.join(BASE_DIR, "static", "images", "Logos"))
PATH_FILES = os.getenv("PATH_FILES", os.path.join(BASE_DIR, "Files"))
PATH_DATABASE = os.getenv("PATH_DATABASE", os.path.join(BASE_DIR, "Modules", "Database", "Database.db"))

# Paths Store
PATH_WINGET_REPOSITORY = os.getenv("PATH_WINGET_REPOSITORY", os.path.join(BASE_DIR, "Winget_DB"))
PATH_WINGET_REPOSITORY_DB = os.getenv("PATH_WINGET_REPOSITORY_DB", os.path.join(PATH_WINGET_REPOSITORY, "Public", "index.db"))
URL_WINGET_REPOSITORY = os.getenv("URL_WINGET_REPOSITORY", "https://cdn.winget.microsoft.com/cache/")

# SSL Certificate Paths (for development mode)
PATH_SSL_CERT = os.getenv("PATH_SSL_CERT", os.path.join(BASE_DIR, "SSL", "cert.pem"))
PATH_SSL_KEY = os.getenv("PATH_SSL_KEY", os.path.join(BASE_DIR, "SSL", "key.pem"))

# Network Settings
BIND_ADDRESS = os.getenv("BIND_ADDRESS", "127.0.0.1")

#--------------------------------Not Configurable Variables--------------------------------
# Fallback Logo if no logo is found in the PATH_LOGOS
PATH_STATIC_DUMMY_LOGO = os.path.join(BASE_DIR, "static", "images", "Logos", "dummy.png")