"""Settings de produção para servidor doméstico (Docker + Ollama)."""
from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False

# SSL/Proxy settings — no HTTPS on home server without reverse proxy
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=False)

# CSRF trusted origins for home server access
CSRF_TRUSTED_ORIGINS = [
    "http://192.168.2.122:8001",
    "http://100.65.34.33:8001",
    "http://samsung:8001",
    "http://samsung.tailfc8a1a.ts.net:8001",
]

# Static files for production with WhiteNoise
STATICFILES_DIRS = [BASE_DIR / "static"]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Media files served by Django in production (or nginx proxy)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Ensure allowed hosts include home server IPs
# This is set via .env.prod ALLOWED_HOSTS