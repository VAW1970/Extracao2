"""
WSGI config for config project.
Vercel detects this project as Django via manage.py and WSGI_APPLICATION.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
