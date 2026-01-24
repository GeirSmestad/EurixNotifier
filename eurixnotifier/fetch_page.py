from __future__ import annotations

import requests


def fetch_html(url: str, *, timeout_s: float = 20.0) -> str:
    resp = requests.get(
        url,
        timeout=timeout_s,
        headers={
            "User-Agent": "eurixnotifier/0.1 (+https://github.com/; cron job)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    resp.raise_for_status()
    # requests will decode based on headers / apparent encoding
    return resp.text

