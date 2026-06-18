"""
WSGI config for hedgium_research.
"""

import os

from django.core.wsgi import get_wsgi_application

from config.settings_module import get_django_settings_module

os.environ.setdefault("DJANGO_SETTINGS_MODULE", get_django_settings_module())

application = get_wsgi_application()
