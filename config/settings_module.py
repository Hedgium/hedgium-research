"""
Resolve DJANGO_SETTINGS_MODULE from ENVIRONMENT.
Set ENVIRONMENT in .env or Railway: local | dev | prod (default: local).
"""
from decouple import config

_SETTINGS_MAP = {
    "local": "config.settings_local",
    "dev": "config.settings_dev",
    "prod": "config.settings_prod",
}


def get_django_settings_module() -> str:
    env = (config("ENVIRONMENT", default="local") or "local").strip().lower()
    return _SETTINGS_MAP.get(env, _SETTINGS_MAP["local"])
