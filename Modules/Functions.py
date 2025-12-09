import ipaddress
import configparser
import json
import os
import random
import socket
import string
import dns.resolver
import dns.reversename
import zlib

from datetime import datetime
from pathlib import Path
from werkzeug.datastructures import headers
from io import StringIO, BytesIO
from settings import PATH_FILES, PATH_LOGOS, PATH_DATABASE
from itsdangerous import base64_decode


def generate_random_string(length: int) -> string:
    letters = string.ascii_letters
    random_string = ''.join(random.choice(letters) for _ in range(length))
    return random_string


def all_to_dict(data: list, header_data: tuple) -> list:
    if len(data) > 0:
        header = []
        for item in header_data:
            header.extend(value for value in item if value is not None)
        data = [dict(zip(header, d)) for d in data]
        return data
    return []


def row_to_dict(row: tuple, header_data: tuple) -> dict:
    if row is not None and len(row) > 0:
        return {desc[0]: val for desc, val in zip(header_data, row)}
    else:
        return {}


def get_ip_from_hostname(hostname: str, suffix: str, dns_server: str) -> str:
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [dns_server]

    try:
        answers = resolver.resolve(hostname, 'A')
        for rdata in answers:
            return rdata.address
    except Exception:
        pass

    if suffix and not hostname.endswith(suffix):
        fqdn = f"{hostname}.{suffix}".rstrip(".")
        try:
            answers = resolver.resolve(fqdn, 'A')
            for rdata in answers:
                return rdata.address
        except Exception:
            pass
    return ""


def get_hostname_from_ip_dns(ip_address: str, dns_server: str) -> str:
    try:
        rev_name = dns.reversename.from_address(ip_address)
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [dns_server]
        answer = resolver.resolve(rev_name, "PTR")
        full_hostname = str(answer[0]).rstrip(".")
        short_hostname = full_hostname.split(".")[0]
        return short_hostname
    except Exception:
        return ""


def is_ip_address(text: str) -> bool:
    try:
        ipaddress.ip_address(text)
        return True
    except ValueError:
        return False


def check_Internet_Connection() -> bool:
    try:
        socket.setdefaulttimeout(3)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        return True
    except socket.error:
        return False


def get_Auth_Token_from_Header(header: headers) -> str:
    try:
        client_auth_token = json.loads(header.get('Windows-Package-Manager').replace("'", '"'))
        client_auth_token = client_auth_token.get("Token")
    except:
        client_auth_token = ""
    return client_auth_token


def parse_version(version_str: str) -> tuple:
    parts = version_str.split('.')
    numeric_parts = []

    for p in parts:
        try:
            numeric_parts.append(int(p))
        except ValueError:
            break

    if not numeric_parts:
        return (-1,)

    while len(numeric_parts) < 3:
        numeric_parts.append(0)
    return tuple(numeric_parts)


def generate_Client_INI(token: str, host: str) -> BytesIO:
    config = configparser.ConfigParser()
    config['Settings'] = {
        'URL': f'https://{host}',
        'Token': token,
        'Repo': 'Winget-Repo'
    }

    ini_stream = BytesIO()
    temp_stream = StringIO()
    config.write(temp_stream)
    data = temp_stream.getvalue().encode('utf-8')

    ini_stream.write(data)
    ini_stream.seek(0)
    return ini_stream


def get_file_edit_date(path: str) -> datetime:
    file = Path(path)
    mtime = file.stat().st_mtime
    return datetime.fromtimestamp(mtime)


def start_up_check():
    # Ensure user-uploaded files directory exists
    if not os.path.exists(PATH_FILES):
        os.makedirs(PATH_FILES, exist_ok=True)
    
    # Ensure logos directory exists
    if not os.path.exists(PATH_LOGOS):
        os.makedirs(PATH_LOGOS, exist_ok=True)
    
    # Ensure database parent directory exists (SQLite creates the file but not the directory)
    db_dir = os.path.dirname(PATH_DATABASE)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)


def decode_flask_cookie(cookie) -> dict:
    try:
        compressed = False
        payload = cookie

        if payload.startswith('.'):
            compressed = True
            payload = payload[1:]

        data = payload.split(".")[0]

        data = base64_decode(data)
        if compressed:
            data = zlib.decompress(data)

        return json.loads(data.decode("utf-8"))
    except Exception as e:
        return {}
