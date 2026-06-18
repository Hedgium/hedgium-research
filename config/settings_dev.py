import os

import dj_database_url

from config.settings import *

DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)

DATABASES = {
    "default": dj_database_url.config(
        default=config("DATABASE_URL"),
        conn_max_age=600,
    )
}

REDIS_URL = config("REDIS_URL")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TASK_ALWAYS_EAGER = False

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in config(
        "CORS_ALLOWED_ORIGINS",
        default="https://hedgium-dev.vercel.app,http://localhost:3000",
    ).split(",")
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = True

ALLOWED_HOSTS = [
    host.strip()
    for host in config("ALLOWED_HOSTS", default="localhost").split(",")
    if host.strip()
]
_railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "").strip()
if _railway_domain:
    ALLOWED_HOSTS.append(_railway_domain)

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in config(
        "CSRF_TRUSTED_ORIGINS",
        default="https://hedgium-research-dev.up.railway.app",
    ).split(",")
    if origin.strip()
]
if _railway_domain:
    CSRF_TRUSTED_ORIGINS.append(f"https://{_railway_domain}")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
