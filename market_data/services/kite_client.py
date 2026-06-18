"""Kite Connect client for historical OHLCV."""

from __future__ import annotations

import logging
from typing import Any

import requests
from django.conf import settings
from kiteconnect import KiteConnect

logger = logging.getLogger(__name__)

KITE_INSTRUMENTS_URL = "https://api.kite.trade/instruments"


def _credentials_from_env() -> dict[str, str] | None:
    api_key = (getattr(settings, "KITE_API_KEY", "") or "").strip()
    access_token = (getattr(settings, "KITE_ACCESS_TOKEN", "") or "").strip()
    if api_key and access_token:
        return {"api_key": api_key, "access_token": access_token}
    return None


def _credentials_from_backend() -> dict[str, str] | None:
    base_url = settings.HEDGIUM_BACKEND_API_URL
    token = (getattr(settings, "HEDGIUM_INTERNAL_SERVICE_TOKEN", "") or "").strip()
    if not base_url or not token:
        return None

    url = f"{base_url}/internal/stream/credentials"
    try:
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        logger.warning("Failed to fetch Kite credentials from backend: %s", exc)
        return None

    if data.get("error"):
        logger.warning("Backend credentials error: %s", data["error"])
        return None

    api_key = data.get("api_key", "")
    access_token = data.get("access_token", "")
    if api_key and access_token:
        return {"api_key": api_key, "access_token": access_token}
    return None


def get_kite_credentials() -> dict[str, str]:
    creds = _credentials_from_env() or _credentials_from_backend()
    if not creds:
        raise RuntimeError(
            "Kite credentials not configured. Set KITE_API_KEY + KITE_ACCESS_TOKEN "
            "or HEDGIUM_BACKEND_API_URL + HEDGIUM_INTERNAL_SERVICE_TOKEN."
        )
    return creds


def get_kite_client() -> KiteConnect:
    creds = get_kite_credentials()
    kite = KiteConnect(api_key=creds["api_key"])
    kite.set_access_token(creds["access_token"])
    return kite


def download_instruments_csv() -> str:
    """Kite instruments master is public — no auth required."""
    response = requests.get(KITE_INSTRUMENTS_URL, timeout=120)
    response.raise_for_status()
    return response.text


def fetch_historical_daily(
    kite: KiteConnect,
    instrument_token: int,
    from_date,
    to_date,
) -> list[dict[str, Any]]:
    return kite.historical_data(
        instrument_token,
        from_date,
        to_date,
        interval="day",
        continuous=False,
        oi=False,
    )
