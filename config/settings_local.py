import os

from config.settings import *

# Local development — permissive hosts/CORS; SQLite fallback remains in base when DATABASE_URL unset.
DEBUG = config("DJANGO_DEBUG", default=True, cast=bool)

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
ALLOWED_HOSTS = ["*"]

_railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "").strip()
if _railway_domain:
    CSRF_TRUSTED_ORIGINS = [f"https://{_railway_domain}"]
