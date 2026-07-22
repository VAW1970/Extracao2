"""
Django settings for extracao_contabil project.
Configured for deployment on Vercel with Neon PostgreSQL.
"""

import os
from pathlib import Path
import environ

# ============================================================
# PATHS
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# ENVIRONMENT VARIABLES (django-environ)
# ============================================================
env = environ.Env(
    DJANGO_DEBUG=(bool, True),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    LLM_PROVIDER=(str, "ollama"),
    OLLAMA_HOST=(str, "http://localhost:11434"),
    OLLAMA_MODEL=(str, "llama3"),
    EXTRACTION_MAX_RETRIES=(int, 2),
    CONN_MAX_AGE=(int, 0),
)

# Read .env file if it exists (local development)
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))

# ============================================================
# SECURITY
# ============================================================
SECRET_KEY = env("DJANGO_SECRET_KEY", default="django-insecure-change-me-in-production")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

# Allow iframes from same origin for PDF preview
X_FRAME_OPTIONS = "SAMEORIGIN"

# ============================================================
# APPLICATION DEFINITION
# ============================================================
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "storages",
]

LOCAL_APPS = [
    "apps.usuarios",
    "apps.documentos",
    "apps.validacao",
    "apps.dashboard",
    "apps.llm_service",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
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
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ============================================================
# CUSTOM USER MODEL
# ============================================================
# MUST be defined before first migration.
AUTH_USER_MODEL = "usuarios.Usuario"

# ============================================================
# DATABASE — Neon PostgreSQL (pooled for app traffic)
# ============================================================
# In production on Vercel, DATABASE_URL is the pooled connection string.
# For local dev, use SQLite or a local Postgres.
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    ),
}

# For migrations/admin that need unpooled connection, use DATABASE_URL_UNPOOLED.
# Access via: DJANGO_DATABASE_URL_UNPOOLED env var in management commands.

# Conservative CONN_MAX_AGE for serverless (Vercel Fluid Compute).
# Connections are ephemeral between invocations.
DATABASES["default"]["CONN_MAX_AGE"] = env("CONN_MAX_AGE", default=0)

# Disable server-side cursors if the pooler operates in transaction mode
if os.environ.get("PGSSLMODE") == "require" or "neon.tech" in DATABASES["default"].get("HOST", ""):
    DATABASES["default"]["OPTIONS"] = {
        **DATABASES["default"].get("OPTIONS", {}),
        "connect_timeout": 10,
    }

# ============================================================
# PASSWORD VALIDATION
# ============================================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ============================================================
# INTERNATIONALIZATION
# ============================================================
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# Date/time formats for Brazilian Portuguese
DATE_INPUT_FORMATS = ["%d/%m/%Y"]
DATETIME_INPUT_FORMATS = ["%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"]
DATE_FORMAT = "d/m/Y"
DATETIME_FORMAT = "d/m/Y H:i:s"
TIME_FORMAT = "H:i:s"

# ============================================================
# STATIC FILES
# ============================================================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# WhiteNoise serves static files directly from STATICFILES_DIRS in production,
# so we don't need collectstatic. STATIC_ROOT is kept for dev fallback.
IS_SUPABASE_CONFIGURED = bool(
    os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
)

if IS_SUPABASE_CONFIGURED:
    # Production: Supabase Storage via REST API (serverless-friendly)
    STORAGES = {
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
        },
        "default": {
            "BACKEND": "apps.storage_backends.SupabaseStorage",
        },
    }
else:
    # Development: local filesystem
    STORAGES = {
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
        },
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
    }

# Tell WhiteNoise to serve files from STATICFILES_DIRS directly.
WHITENOISE_ROOT = BASE_DIR / "static"
# Disable AppDirectoriesFinder — only use explicit STATICFILES_DIRS.
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
]

# ============================================================
# MEDIA FILES (document uploads)
# ============================================================
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ============================================================
# AUTHENTICATION
# ============================================================
LOGIN_URL = "/usuarios/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/usuarios/login/"

# ============================================================
# LOGGING — Structured, no sensitive data leakage
# ============================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
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
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        "apps.llm_service": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# ============================================================
# LLM CONFIGURATION
# ============================================================
LLM_PROVIDER = env("LLM_PROVIDER")  # "ollama" or "api"
OLLAMA_HOST = env("OLLAMA_HOST")
OLLAMA_MODEL = env("OLLAMA_MODEL")
LLM_API_KEY = env("LLM_API_KEY", default="")
LLM_MODEL = env("LLM_MODEL", default="llama-3.3-70b-versatile")
LLM_BASE_URL = env("LLM_BASE_URL", default="https://api.groq.com/openai/v1")
EXTRACTION_MAX_RETRIES = env("EXTRACTION_MAX_RETRIES")

# ============================================================
# VERCEL-SPECIFIC
# ============================================================
# Vercel sets this env var automatically in production.
IS_VERCEL = os.environ.get("VERCEL", False)

if IS_VERCEL:
    # In production, force non-debug and restrict allowed hosts
    DEBUG = False
    # Allow Vercel deployment URLs
    ALLOWED_HOSTS = ALLOWED_HOSTS + [".vercel.app"]

    # Security — Vercel uses HTTPS
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS if host != "*"]
    SECURE_SSL_REDIRECT = False  # Vercel handles HTTPS termination
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
