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


def fetch_json(path: str) -> dict:
    # Only network-level failures fail over to the next host. HTTP errors
    # (4xx/5xx) raise immediately: a healthy host saying "bad request" or
    # "not found" won't answer differently on a mirror.
    last_error: requests.RequestException | None = None

    for host in API_HOSTS:
        try:
            r = requests.get(f"{host}{path}", timeout=TIMEOUT, headers=HEADERS)
            r.raise_for_status()
            return r.json()
        except (requests.ConnectionError, requests.Timeout) as e:
            last_error = e

    if last_error is None:
        raise RuntimeError("API_HOSTS is empty")
    raise last_error
