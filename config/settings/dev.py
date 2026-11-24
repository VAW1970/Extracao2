"""Settings de desenvolvimento."""
from .base import *  # noqa: F401,F403
from .base import DATABASES

DEBUG = True
ALLOWED_HOSTS = ["*"]

STATICFILES_DIRS = [BASE_DIR / "static"]

import environ  # noqa: E402

env = environ.Env()
if not env.str("DATABASE_URL", default=""):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(BASE_DIR / "db.sqlite3"),  # noqa: F405
        }
    }