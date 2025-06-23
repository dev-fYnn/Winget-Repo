import ipaddress
import random
import string
import dns.resolver
import dns.reversename


def generate_random_string(length: int) -> string:
    letters = string.ascii_letters
    random_string = ''.join(random.choice(letters) for _ in range(length))
    return random_string


def select_to_dict(data: list, header_data: tuple) -> list:
    if len(data) > 0:
        header = []
        for item in header_data:
            header.extend(value for value in item if value is not None)
        data = [dict(zip(header, d)) for d in data]
        return data
    return []


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


def is_ip_address(text):
    try:
        ipaddress.ip_address(text)
        return True
    except ValueError:
        return False
