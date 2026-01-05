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

# Parse allowed hosts from environment variable
ALLOWED_HOSTS_ENV = os.environ.get("ELIBRARY_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1],testserver")
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_ENV.split(",")]

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
    # REST Framework & API
    "rest_framework",
    "rest_framework.authtoken",
    "drf_spectacular",
    "django_filters",
    "corsheaders",
    # Local apps
    "catalog",
    "circulation",
    "accounts",
    "api",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # CORS must be early in middleware
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Custom security middleware
    "elibrary.security.SecurityHeadersMiddleware",
    "elibrary.security.SecurityLoggingMiddleware",
    # Metrics collection middleware
    "elibrary.metrics.MetricsMiddleware",
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
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
# Supports DATABASE_URL environment variable for flexible database configuration

import dj_database_url

# Default to SQLite for development
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///db.sqlite3")

DATABASES = {
    "default": dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,  # Persistent database connections
        conn_health_checks=True,  # Health checks for connections
    )
}

# Ensure SQLite uses WAL mode for better concurrency
if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
    DATABASES["default"]["OPTIONS"] = {
        "init_command": "PRAGMA journal_mode=WAL;",
    }

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
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

# Comprehensive Logging Configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(name)s %(process)d %(thread)d %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "%(levelname)s %(name)s: %(message)s",
        },
    },
    "filters": {
        "suppress_well_known": {
            "()": "elibrary.settings.WellKnownFilter",
        },
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG" if DEBUG else "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "filters": ["suppress_well_known"],
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "elibrary.log"),
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 10,
            "formatter": "verbose",
        },
        "api_file": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "api.log"),
            "maxBytes": 5 * 1024 * 1024,  # 5MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "error_file": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "errors.log"),
            "maxBytes": 5 * 1024 * 1024,  # 5MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "filters": ["require_debug_false"],
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file", "error_file"],
            "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "django.server": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console", "error_file", "mail_admins"],
            "level": "INFO",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "WARNING",
            "propagate": False,
        },
        "api": {
            "handlers": ["console", "api_file"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        "catalog": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "circulation": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "accounts": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": os.environ.get("LOG_LEVEL", "INFO"),
    },
}

# Create logs directory if it doesn't exist
_LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(_LOGS_DIR, exist_ok=True)

# Sentry Error Tracking Configuration (Optional)
SENTRY_DSN = os.environ.get("SENTRY_DSN")
if SENTRY_DSN and ELIBRARY_PRODUCTION:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration()],
            traces_sample_rate=0.1,
            send_default_pii=False,
            environment="production" if ELIBRARY_PRODUCTION else "development",
        )
    except ImportError:
        pass

# REST Framework Configuration with Enhanced Security
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": int(os.environ.get("API_PAGE_SIZE", "20")),
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.environ.get("API_ANON_RATE_LIMIT", "50/hour"),  # Stricter for anonymous
        "user": os.environ.get("API_USER_RATE_LIMIT", "1000/day"),  # Generous for users
    },
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.NamespaceVersioning",
    # Security settings
    "EXCEPTION_HANDLER": "api.exceptions.custom_exception_handler",
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",  # Only JSON, no browsable API in production
    ],
    "COERCE_DECIMAL_TO_STRING": False,
    "NUM_PROXIES": 1,  # For rate limiting behind proxy
    "TEST_REQUEST_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.MultiPartRenderer",
    ],
}

# CORS Configuration - Allow cross-origin requests from frontend apps
CORS_ALLOWED_ORIGINS = [
    origin.strip() for origin in os.environ.get(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8080"
    ).split(",")
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# drf-spectacular configuration for OpenAPI/Swagger docs
SPECTACULAR_SETTINGS = {
    "TITLE": "TS OPAC eLibrary API",
    "DESCRIPTION": "Production-grade REST API for library management system",
    "VERSION": "1.0.0",
    "SERVE_PERMISSIONS": ["rest_framework.permissions.IsAuthenticated"],
    "SCHEMA_PATH_PREFIX": "/api/v1/",
    "CONTACT": {
        "name": "TS OPAC eLibrary Support",
        "email": "support@eLibrary.local",
    },
}