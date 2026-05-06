from cryptography.fernet import Fernet


def encrypt_text(enc_key: bytes, password: str) -> str:
    f = Fernet(enc_key)
    return f.encrypt(password.encode()).decode()


def decrypt_text(enc_key: bytes, encrypted: str) -> str:
    f = Fernet(enc_key)
    return f.decrypt(encrypted.encode()).decode()
