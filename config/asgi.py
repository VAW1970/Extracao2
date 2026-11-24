"""
ASGI config for config project.
Production uses DJANGO_SETTINGS_MODULE=config.settings.prod via environment variable.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

application = get_asgi_application()