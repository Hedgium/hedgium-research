"""HTTP client for NSE India endpoints (bhavcopy, FII/DII, corporate actions)."""

from __future__ import annotations

import logging
import time
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

NSE_HOME = "https://www.nseindia.com"
NSE_ARCHIVES = "https://nsearchives.nseindia.com"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
}


class NSEClient:
    """Session-aware client — NSE requires cookies from the homepage first."""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self._warmed = False

    def _warm_session(self) -> None:
        if self._warmed:
            return
        try:
            self.session.get(NSE_HOME, timeout=30)
            self._warmed = True
        except requests.RequestException as exc:
            logger.warning("NSE session warm-up failed: %s", exc)

    def _throttle(self) -> None:
        delay = getattr(settings, "NSE_REQUEST_DELAY_SEC", 0.5)
        if delay > 0:
            time.sleep(delay)

    def get_json(self, path: str, *, base: str = NSE_HOME) -> Any:
        self._warm_session()
        self._throttle()
        url = f"{base.rstrip('/')}/{path.lstrip('/')}"
        response = self.session.get(url, timeout=60)
        response.raise_for_status()
        return response.json()

    def get_bytes(self, url: str) -> bytes:
        self._warm_session()
        self._throttle()
        response = self.session.get(url, timeout=120)
        response.raise_for_status()
        return response.content

    def get_text(self, url: str) -> str:
        return self.get_bytes(url).decode("utf-8", errors="replace")
