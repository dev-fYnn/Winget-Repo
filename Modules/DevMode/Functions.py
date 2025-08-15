import os
import sys

from datetime import datetime, timezone, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend


def generate_dev_certificate(cert_file: str = r"SSL\cert.pem", key_file: str = r"SSL\key.pem") -> bool:
    path = sys.path[0]
    cert_file = os.path.join(path, cert_file)
    key_file = os.path.join(path, key_file)

    os.makedirs(os.path.dirname(cert_file), exist_ok=True)
    if os.path.exists(cert_file) and os.path.exists(key_file):
        return True

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"EN"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u""),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u""),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Winget-Repo"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
    ])

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
    cert = x509.CertificateBuilder().subject_name(subject).issuer_name(issuer).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.now(timezone.utc)
    ).not_valid_after(
        datetime.now(timezone.utc) + timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
        critical=False,
    ).sign(key, hashes.SHA256(), default_backend())

    with open(cert_file, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    with open(key_file, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    if os.path.exists(cert_file) and os.path.exists(key_file):
        return True
    return False
