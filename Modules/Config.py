import os
import secrets

from dotenv import load_dotenv, set_key
from cryptography.fernet import Fernet
from pathlib import Path

from settings import BASE_DIR

SECRETS_FILE = os.path.join(BASE_DIR, ".env")


def _ensure_keys():
    Path(SECRETS_FILE).touch(exist_ok=True)
    load_dotenv(SECRETS_FILE)

    required_keys = {
        "SECRET_KEY": lambda: secrets.token_hex(32),
        "DOWNLOAD_KEY": lambda: secrets.token_hex(32),
        "ENCRYPTION_KEY": lambda: Fernet.generate_key().decode(),
    }

    for key, generator in required_keys.items():
        if not os.environ.get(key):
            value = generator()
            set_key(SECRETS_FILE, key, value)
            os.environ[key] = value


class Config:
    @classmethod
    def init(cls):
        _ensure_keys()

        cls.SECRET_KEY = os.environ["SECRET_KEY"]
        cls.DOWNLOAD_KEY = os.environ["DOWNLOAD_KEY"]
        cls.ENCRYPTION_KEY = os.environ["ENCRYPTION_KEY"].encode()
