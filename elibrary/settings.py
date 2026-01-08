"""
Django settings for elibrary project.
"""

from pathlib import Path
import os
import logging

# Load environment variables from .env or .env.production
try:
    from dotenv import load_dotenv
    
    # For development, ALWAYS load .env (not .env.production)
    # .env.production is for production servers only
    base_dir = Path(__file__).resolve().parent.parent
    env_dev = base_dir / ".env"
    env_production = base_dir / ".env.production"
    
    # Load .env if it exists (development), otherwise ignore
    # Never auto-load .env.production to prevent security issues in development
    if env_dev.exists():
        load_dotenv(env_dev)
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

# SECURITY: load sensitive settings from environment
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-your-secret-key-here-change-in-production")

# DEBUG controlled by env var. Default True for development, False for production
# Force True for development server access
DEBUG = True

# Parse allowed hosts from environment variable
ALLOWED_HOSTS_ENV = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1,[::1],testserver")
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_ENV.split(",")]

# Determine production mode: DEBUG=False means production (overrides ENVIRONMENT variable)
# When DEBUG=True, production security settings are always disabled
ELIBRARY_PRODUCTION = (not DEBUG) and os.environ.get("ENVIRONMENT", "") == "production"

# Production security settings (applied only in production mode)
if ELIBRARY_PRODUCTION:
    # Secure cookies and SSL
    SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "True") == "True"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "True") == "True"
    CSRF_COOKIE_SECURE = os.environ.get("CSRF_COOKIE_SECURE", "True") == "True"
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Strict"
    CSRF_COOKIE_SAMESITE = "Strict"

    # HSTS (HTTP Strict Transport Security)
    SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Restrict referrer and XSS protections
    SECURE_REFERRER_POLICY = os.environ.get("SECURE_REFERRER_POLICY", "strict-origin-when-cross-origin")
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_SECURITY_POLICY = True
    X_FRAME_OPTIONS = os.environ.get("X_FRAME_OPTIONS", "DENY")
else:
    # Development mode - disable all production security settings
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = False
    CSRF_COOKIE_HTTPONLY = False
    SESSION_COOKIE_SAMESITE = "Lax"
    CSRF_COOKIE_SAMESITE = "Lax"
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
    SECURE_REFERRER_POLICY = "no-referrer-when-downgrade"
    SECURE_BROWSER_XSS_FILTER = False
    SECURE_CONTENT_SECURITY_POLICY = False
    X_FRAME_OPTIONS = "ALLOW"



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
]

# Add security middleware only in production
if ELIBRARY_PRODUCTION:
    MIDDLEWARE.extend([
        "django.middleware.security.SecurityMiddleware",
        # Custom security middleware - production only
        "elibrary.security.SecurityHeadersMiddleware",
        "elibrary.security.SecurityLoggingMiddleware",
    ])
else:
    # Development mode: add a middleware to explicitly remove HSTS headers
    # (in case they're set anywhere else)
    MIDDLEWARE.extend([
        "elibrary.security.DevNoHSTSMiddleware",
    ])

MIDDLEWARE.extend([
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Metrics collection middleware (always enabled)
    "elibrary.metrics.MetricsMiddleware",
])

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
# Flexible database configuration supporting SQLite and PostgreSQL

import dj_database_url  # type: ignore[import] - package in requirements.txt

# Get database URL from environment or use SQLite default
# For SQLite: sqlite:///db.sqlite3 (default)
# For PostgreSQL: postgresql://user:password@localhost:5432/dbname
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///db.sqlite3")

# Parse DATABASE_URL and create database config
DATABASES = {
    "default": dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,  # Persistent database connections (seconds)
        conn_health_checks=True,  # Enable connection health checks
    )
}

# Database-specific optimizations
if DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql":
    # PostgreSQL-specific optimizations
    DATABASES["default"]["CONN_MAX_AGE"] = 600
    DATABASES["default"]["OPTIONS"] = {
        "connect_timeout": 10,
    }
    # Add SSL requirement in production if not disabled
    if ELIBRARY_PRODUCTION and os.environ.get("POSTGRES_SSL_MODE", "require") == "require":
        DATABASES["default"]["OPTIONS"]["sslmode"] = "require"
    
elif DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
    # SQLite optimizations for development
    DATABASES["default"]["OPTIONS"] = {
        "init_command": "PRAGMA journal_mode=WAL;",  # Write-Ahead Logging for better concurrency
    }

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

# Get minimum password length from environment (production: 12, development: 8)
PASSWORD_MIN_LENGTH = int(os.environ.get("PASSWORD_MIN_LENGTH", "12" if ELIBRARY_PRODUCTION else "8"))

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": PASSWORD_MIN_LENGTH},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# ================================================================
# SECURITY HARDENING - OWASP Top 10 Coverage
# ================================================================

# API Rate Limiting Configuration
API_RATE_LIMIT = int(os.environ.get("API_RATE_LIMIT", "1000"))
API_RATE_LIMIT_AUTHENTICATED = int(os.environ.get("API_RATE_LIMIT_AUTHENTICATED", "10000"))

# Clickjacking Protection
X_FRAME_OPTIONS = "DENY"

# Content Security Policy (basic - can be extended)
SECURE_CONTENT_SECURITY_POLICY = {
    "default-src": ("'self'",),
    "script-src": ("'self'", "'unsafe-inline'", "cdn.jsdelivr.net", "cdnjs.cloudflare.com"),
    "style-src": ("'self'", "'unsafe-inline'", "cdn.jsdelivr.net", "fonts.googleapis.com", "cdnjs.cloudflare.com"),
    "font-src": ("'self'", "fonts.gstatic.com", "cdn.jsdelivr.net", "cdnjs.cloudflare.com"),
    "img-src": ("'self'", "data:", "https:"),
    "frame-ancestors": ("'none'",),
}

# CORS Configuration (Restrict to trusted domains)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]

# Add production domains from environment
CORS_ALLOWED_ORIGINS.extend(
    [domain.strip() for domain in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",") if domain.strip()]
)

# CSRF Protection
CSRF_TRUSTED_ORIGINS = [
    "http://localhost",
    "http://127.0.0.1",
]

# Add production domains from environment
CSRF_TRUSTED_ORIGINS.extend(
    [domain.strip() for domain in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if domain.strip()]
)

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
    CSRF_COOKIE_SECURE = False

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
        import sentry_sdk  # type: ignore[import] - package in requirements.txt
        from sentry_sdk.integrations.django import DjangoIntegration  # type: ignore[import]

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