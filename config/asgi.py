"""
ASGI config for hedgium_research.
"""

import os

from django.core.asgi import get_asgi_application

from config.settings_module import get_django_settings_module

os.environ.setdefault("DJANGO_SETTINGS_MODULE", get_django_settings_module())

application = get_asgi_application()
