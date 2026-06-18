import os

from celery import Celery

from config.settings_module import get_django_settings_module

os.environ.setdefault("DJANGO_SETTINGS_MODULE", get_django_settings_module())

app = Celery("hedgium_research")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
