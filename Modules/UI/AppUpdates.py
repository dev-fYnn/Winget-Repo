import re
import threading
import time
import requests

from Modules.Functions import check_Internet_Connection
from settings import RELEASE_API_URL, CONTAINER_URL, RELEASES_URL


_cache_lock = threading.Lock()
_cached_version = None
_next_check = 0


def _version_parts(version):
    match = re.fullmatch(r"v?(\d+(?:\.\d+)*)", version.strip(), re.IGNORECASE)
    return tuple(map(int, match.group(1).split("."))) if match else None


def get_update(current_version, is_docker):
    global _cached_version, _next_check

    with _cache_lock:
        if time.monotonic() >= _next_check:
            if not check_Internet_Connection():
                _cached_version = None
                _next_check = time.monotonic() + 3600
            else:
                try:
                    response = requests.get(
                        RELEASE_API_URL,
                        headers={"Accept": "application/vnd.github+json", "User-Agent": "Winget-Repo"},
                        timeout=3,
                    )
                    response.raise_for_status()
                    _cached_version = response.json().get("tag_name")
                    _next_check = time.monotonic() + 3600
                except (requests.RequestException, ValueError, AttributeError):
                    _next_check = time.monotonic() + 3600

        cached_version = _cached_version
        latest = _version_parts(cached_version) if isinstance(cached_version, str) else None
        current = _version_parts(current_version)

    if latest and current:
        length = max(len(latest), len(current))
        latest += (0,) * (length - len(latest))
        current += (0,) * (length - len(current))

    if latest and current and latest > current:
        return {
            "version": cached_version,
            "url": CONTAINER_URL if is_docker else RELEASES_URL,
        }
    return None
