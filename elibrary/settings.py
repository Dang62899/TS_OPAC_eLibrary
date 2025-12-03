"""
Django settings for elibrary project.
"""

from pathlib import Path
import os
import logging

# Optionally load a .env file in development for convenience
try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(Path(__file__).resolve().parent.parent, ".env"))
except Exception:
    # python-dotenv not installed or .env missing; ignore silently
    pass


# Filter to suppress .well-known requests
class WellKnownFilter(logging.Filter):
    """Filter out .well-known requests from logs"""
    def filter(self, record):
        return "/.well-known/" not in record.getMessage()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY: load sensitive settings from environment in production
SECRET_KEY = os.environ.get("ELIBRARY_SECRET_KEY", "django-insecure-your-secret-key-here-change-in-production")

# DEBUG controlled by env var. Default True for development, False for production
DEBUG = os.environ.get("ELIBRARY_DEBUG", "True") == "True"

ALLOWED_HOSTS = []
# Allow configuring allowed hosts via environment variable (comma-separated)
# Check both ELIBRARY_ALLOWED_HOSTS and ALLOWED_HOSTS for flexibility
env_allowed = os.environ.get("ELIBRARY_ALLOWED_HOSTS") or os.environ.get("ALLOWED_HOSTS", "")
if env_allowed:
    ALLOWED_HOSTS = [h.strip() for h in env_allowed.split(",") if h.strip()]
else:
    # In development (DEBUG=True), allow localhost by default
    if DEBUG:
        ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]", "testserver", "*.onrender.com"]
    else:
        # Production: allow render.com domains
        ALLOWED_HOSTS = ["*.onrender.com", "onrender.com", "ts-opac-elibrary.onrender.com"]

# Determine production mode: explicit env var only
# Set `ELIBRARY_PRODUCTION=True` in the environment when running in production.
ELIBRARY_PRODUCTION = os.environ.get("ELIBRARY_PRODUCTION", "") == "True"

# Production security settings (applied only in production mode)
if ELIBRARY_PRODUCTION:
    # Secure cookies and SSL
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # HSTS
    SECURE_HSTS_SECONDS = int(os.environ.get("ELIBRARY_HSTS_SECONDS", "3600"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Restrict referrer and XSS protections
    SECURE_REFERRER_POLICY = os.environ.get("ELIBRARY_REFERRER_POLICY", "no-referrer-when-downgrade")
    SECURE_BROWSER_XSS_FILTER = True



# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "crispy_forms",
    "crispy_bootstrap4",
    "django_celery_beat",
    # Local apps
    "catalog",
    "circulation",
    "accounts",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "elibrary.urls"

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
                "circulation.context_processors.unread_notifications",
                "elibrary.context_processors.feature_flags",
            ],
        },
    },
]

WSGI_APPLICATION = "elibrary.wsgi.application"

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap4"
CRISPY_TEMPLATE_PACK = "bootstrap4"

# Custom User Model
AUTH_USER_MODEL = "accounts.User"

# Login settings
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "catalog:index"
LOGOUT_REDIRECT_URL = "catalog:index"

# Ensure logout only works with POST
LOGOUT_ALLOWED_NEXT_URL = "catalog:index"

# Session Configuration
# Use database sessions with inactivity timeout
SESSION_ENGINE = "django.contrib.sessions.backends.db"
# Session timeout: 2 minutes (120 seconds) for testing - change to 1800 (30 min) for production
SESSION_COOKIE_AGE = 120
# Invalidate session when user closes browser (optional - set to False for persistent sessions)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
# Set session cookie to secure in production only
if ELIBRARY_PRODUCTION:
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SECURE = True
else:
    # Development: allow non-secure cookies for testing
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True

# Email settings
# For development: Console backend (emails printed to console)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# For production with Gmail (uncomment and configure):
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'your-email@gmail.com'  # Your Gmail address
# EMAIL_HOST_PASSWORD = 'your-app-password'  # Gmail App Password (NOT your regular password)

# For other email providers (SendGrid, Mailgun, etc.):
# See respective provider documentation for SMTP settings

DEFAULT_FROM_EMAIL = "noreply@elibrary.com"
ADMINS = [("Admin", "admin@elibrary.com")]

# Celery Configuration
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# Library Settings
LIBRARY_NAME = "Digital e-Library"
MAX_ITEMS_PER_BORROWER = 5
LOAN_PERIOD_DAYS = 14
RENEWAL_LIMIT = 2
PRE_DUE_NOTICE_DAYS = 3  # Send "due soon" notification 3 days before
OVERDUE_GRACE_PERIOD_DAYS = 7
# Feature flags
# When False, barcode scanner-based transactions are disabled and ISBN is used instead
BARCODE_ENABLED = False

# Basic logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"},
    },
    "filters": {
        "suppress_well_known": {
            "()": "elibrary.settings.WellKnownFilter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "filters": ["suppress_well_known"],
        },
    },
    "loggers": {
        "django.server": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO"),
    },
}

# Optional file logging when environment requests it
if os.environ.get("ELIBRARY_LOG_TO_FILE", "False") == "True":
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, os.environ.get("ELIBRARY_LOG_FILE", "elibrary.log"))
    LOGGING["handlers"]["file"] = {
        "class": "logging.handlers.RotatingFileHandler",
        "filename": log_file,
        "maxBytes": 10 * 1024 * 1024,  # 10MB
        "backupCount": 5,
        "formatter": "verbose",
    }
    LOGGING["root"]["handlers"].append("file")
