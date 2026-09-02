import requests

API_HOSTS = (
    "https://api.tcgdex.net",
    "https://api.na1.tcgdex.net",
    "https://api.na2.tcgdex.net",
    "https://api.eu1.tcgdex.net",
    "https://api.eu2.tcgdex.net",
    "https://api.eu3.tcgdex.net",
    "https://api.as1.tcgdex.net",
)

HEADERS = {
    "User-Agent": "topdeck (+https://github.com/HighDesertCode/topdeck)",
    "Accept": "application/json",
}

TIMEOUT = (5, 45)

_current_host = 0


def fetch_json(path: str) -> dict:
    global _current_host

    last_error: requests.RequestException | None = None

    # Only unreachable hosts fail over; HTTP errors raise immediately.
    for offset in range(len(API_HOSTS)):
        i = (_current_host + offset) % len(API_HOSTS)

        try:
            r = requests.get(f"{API_HOSTS[i]}{path}", timeout=TIMEOUT, headers=HEADERS)
            r.raise_for_status()
            _current_host = i

            return r.json()
        
        except (requests.ConnectionError, requests.Timeout) as e:
            last_error = e

    if last_error is None:
        raise RuntimeError("API_HOSTS is empty")
    raise last_error
