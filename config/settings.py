"""
Django settings for hedgium_research.
Separate database from hedgium_backend trading stack.
"""

from datetime import timedelta
from pathlib import Path

from celery.schedules import crontab
from corsheaders.defaults import default_headers
from decouple import Config, RepositoryEnv, config as _default_config

BASE_DIR = Path(__file__).resolve().parent.parent

_env_file = BASE_DIR / ".env"
if _env_file.exists():
    config = Config(RepositoryEnv(_env_file))
else:
    config = _default_config

ENVIRONMENT = config("ENVIRONMENT", default="local")
SECRET_KEY = config("SECRET_KEY", default="dev-only-change-in-production")
DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = [
    host.strip()
    for host in config("ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "ninja_extra",
    "symbols.apps.SymbolsConfig",
    "market_data.apps.MarketDataConfig",
    "features.apps.FeaturesConfig",
    "analysis.apps.AnalysisConfig",
    "jobs.apps.JobsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Research DB — separate from hedgium_backend trading DB
DATABASE_URL = config("DATABASE_URL", default="")
if DATABASE_URL:
    import dj_database_url

    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "research.sqlite3",
            "OPTIONS": {"timeout": 30},
        }
    }

REDIS_URL = config("REDIS_URL", default="")

if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in config("CORS_ALLOWED_ORIGINS", default="http://localhost:3000").split(",")
    if origin.strip()
]
CORS_ALLOW_HEADERS = (
    *default_headers,
    "X-API-Key",
)

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Optional link to hedgium_backend for instrument sync / quotes
HEDGIUM_BACKEND_API_URL = config("HEDGIUM_BACKEND_API_URL", default="http://127.0.0.1:8000/api").rstrip("/")
HEDGIUM_BACKEND_API_KEY = config("HEDGIUM_BACKEND_API_KEY", default="")
HEDGIUM_INTERNAL_SERVICE_TOKEN = config("HEDGIUM_INTERNAL_SERVICE_TOKEN", default="")
RESEARCH_API_KEY = config("RESEARCH_API_KEY", default="")

# Kite (optional — otherwise fetched from hedgium_backend internal API)
KITE_API_KEY = config("KITE_API_KEY", default="")
KITE_ACCESS_TOKEN = config("KITE_ACCESS_TOKEN", default="")
KITE_REQUEST_DELAY_SEC = config("KITE_REQUEST_DELAY_SEC", default=0.35, cast=float)
NSE_REQUEST_DELAY_SEC = config("NSE_REQUEST_DELAY_SEC", default=0.5, cast=float)
OHLCV_BACKFILL_YEARS = config("OHLCV_BACKFILL_YEARS", default=5, cast=int)

# ML prediction (Phase 3)
ML_MODEL_DIR = config("ML_MODEL_DIR", default="")
ML_FORWARD_DAYS = config("ML_FORWARD_DAYS", default=30, cast=int)
ML_BULLISH_THRESHOLD = config("ML_BULLISH_THRESHOLD", default=0.03, cast=float)
ML_BEARISH_THRESHOLD = config("ML_BEARISH_THRESHOLD", default=-0.03, cast=float)

# AI agent layer (Phase 4)
AGENT_PROVIDER = config("AGENT_PROVIDER", default="openai")
OPENAI_API_KEY = config("OPENAI_API_KEY", default="")
OPENAI_MODEL = config("OPENAI_MODEL", default="gpt-4o-mini")
ANTHROPIC_API_KEY = config("ANTHROPIC_API_KEY", default="")
ANTHROPIC_MODEL = config("ANTHROPIC_MODEL", default="claude-3-5-sonnet-latest")
AGENT_TIMEOUT_SEC = config("AGENT_TIMEOUT_SEC", default=30, cast=int)
AGENT_MAX_TOKENS = config("AGENT_MAX_TOKENS", default=1200, cast=int)
AGENT_ENABLE = config("AGENT_ENABLE", default=True, cast=bool)
AGENT_PRECOMPUTE_ENABLED = config("AGENT_PRECOMPUTE_ENABLED", default=False, cast=bool)

# Celery — optional locally; required for scheduled ingestion jobs
if REDIS_URL:
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
else:
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_BROKER_URL = "memory://"
    CELERY_RESULT_BACKEND = "cache+memory://"
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_RESULT_EXPIRES = 300
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Kolkata"
CELERY_WORKER_HIJACK_ROOT_LOGGER = False

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "celery": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "celery.task": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "jobs": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "jobs.tasks": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

CELERY_BEAT_SCHEDULE = {
    "ingest-market-data-daily": {
        "task": "jobs.tasks.ingestion_tasks.ingest_ohlcv_daily",
        "schedule": crontab(hour=18, minute=30),
    },
    "compute-features-daily": {
        "task": "jobs.tasks.feature_tasks.compute_features_daily",
        "schedule": crontab(hour=19, minute=0),
    },
    "predict-universe-daily": {
        "task": "jobs.tasks.ml_tasks.predict_universe_daily",
        "schedule": crontab(hour=19, minute=15),
    },
    "train-prediction-model-weekly": {
        "task": "jobs.tasks.ml_tasks.train_prediction_model_weekly",
        "schedule": crontab(hour=20, minute=0, day_of_week="sun"),
    },
    "agent-precompute-daily": {
        "task": "jobs.tasks.agent_tasks.precompute_agent_reports_daily",
        "schedule": crontab(hour=19, minute=30),
    },
}
