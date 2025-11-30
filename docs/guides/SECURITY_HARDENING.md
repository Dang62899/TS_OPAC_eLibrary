# Security Hardening & Production Deployment Guide

**Last Updated:** November 29, 2025  
**Project:** TS_OPAC_eLibrary  
**Status:** Ready for Production Hardening

---

## Overview

The TS_OPAC_eLibrary Django project includes production-ready security settings that activate when deployed. This guide covers:
1. **Environment Configuration** for production
2. **Security Settings** activation
3. **Deployment Checklist**
4. **Monitoring & Maintenance**

---

## Current Security Status

### ✅ Code Quality
- Flake8: 0 violations
- Syntax: No errors
- Imports: All clean

### ⚠️ Security Warnings (Development Mode)
These warnings are **expected in development** and automatically resolve when configured for production:

| Warning | Current | Fix |
|---------|---------|-----|
| `W004` - HSTS | Not set | Set via `ELIBRARY_HSTS_SECONDS` |
| `W008` - SSL Redirect | Disabled | Set via `ELIBRARY_PRODUCTION=True` |
| `W009` - SECRET_KEY | Insecure | Generate via `python manage.py shell` |
| `W012` - Session Cookie | Not secure | Enabled in production mode |
| `W016` - CSRF Cookie | Not secure | Enabled in production mode |
| `W020` - ALLOWED_HOSTS | Empty | Set via `ELIBRARY_ALLOWED_HOSTS` |

---

## Production Deployment Steps

### 1. Generate Secure SECRET_KEY

The current development key is insecure. Generate a production key:

```bash
python manage.py shell
```

Then in the shell:
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

Copy the output and save securely.

### 2. Set Environment Variables

Create a `.env` file or configure your deployment platform with:

```bash
# Security
ELIBRARY_SECRET_KEY=<your-generated-secret-key>
ELIBRARY_PRODUCTION=True
ELIBRARY_DEBUG=False

# Network
ELIBRARY_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com

# HTTPS/SSL
ELIBRARY_HSTS_SECONDS=31536000  # 1 year (recommended)

# Referrer Policy
ELIBRARY_REFERRER_POLICY=strict-origin-when-cross-origin

# Database (if not using SQLite)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Celery (if using async tasks)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 3. Verify Security Configuration

Test that production settings are applied:

```bash
ELIBRARY_PRODUCTION=True ELIBRARY_ALLOWED_HOSTS=localhost python manage.py check --deploy
```

**Expected output:** All security warnings resolved, only info/debug messages.

### 4. Create Superuser

```bash
python manage.py createsuperuser
```

### 5. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 6. Run Migrations

```bash
python manage.py migrate
```

### 7. Load Initial Data (Optional)

```bash
python manage.py create_initial_data
```

---

## Security Features Enabled in Production

### Session & CSRF Security
```python
SECURE_SSL_REDIRECT = True              # Force HTTPS
SESSION_COOKIE_SECURE = True            # HTTPS-only cookies
SESSION_COOKIE_HTTPONLY = True          # No JS access to session
CSRF_COOKIE_SECURE = True               # HTTPS-only CSRF token
CSRF_COOKIE_HTTPONLY = True             # No JS access to CSRF token
```

### HTTP Strict Transport Security (HSTS)
```python
SECURE_HSTS_SECONDS = 31536000          # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True   # Include subdomains
SECURE_HSTS_PRELOAD = True              # Allow preload list
```

### XSS & Clickjacking Protection
```python
SECURE_BROWSER_XSS_FILTER = True        # X-XSS-Protection header
SECURE_CONTENT_SECURITY_POLICY = {
    "default-src": ["'self'"],
    "script-src": ["'self'", "'unsafe-inline'"],
    "style-src": ["'self'", "'unsafe-inline'"],
}
X_FRAME_OPTIONS = 'DENY'                # Prevent clickjacking
```

### Referrer Policy
```python
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
```

---

## Database Configuration

### SQLite (Development/Testing)
Already configured, but not suitable for production.

### PostgreSQL (Recommended for Production)

1. **Install postgres client:**
   ```bash
   pip install psycopg2-binary
   ```

2. **Set DATABASE_URL:**
   ```bash
   DATABASE_URL=postgresql://user:password@localhost:5432/elibrary
   ```

3. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

### MySQL Alternative
```bash
pip install mysqlclient
DATABASE_URL=mysql://user:password@localhost:3306/elibrary
```

---

## Celery & Background Tasks

If using async tasks (currently configured):

### Redis Setup
```bash
# Install Redis
# macOS: brew install redis
# Ubuntu: sudo apt-get install redis-server
# Docker: docker run -d -p 6379:6379 redis

# Set environment variables
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Run Celery Worker (Production)
```bash
celery -A elibrary worker -l info --concurrency=4
```

### Run Celery Beat (Scheduler)
```bash
celery -A elibrary beat -l info
```

---

## Web Server Configuration

### Gunicorn (Recommended)

1. **Install:**
   ```bash
   pip install gunicorn
   ```

2. **Run:**
   ```bash
   gunicorn --bind 0.0.0.0:8000 --workers 4 --worker-class sync elibrary.wsgi:application
   ```

3. **Production with supervisor/systemd:**
   ```bash
   # Create /etc/systemd/system/elibrary.service
   [Unit]
   Description=TS_OPAC_eLibrary Django Application
   After=network.target

   [Service]
   Type=notify
   User=www-data
   WorkingDirectory=/var/www/elibrary
   ExecStart=/var/www/elibrary/venv/bin/gunicorn --bind unix:/var/run/gunicorn.sock --workers 4 elibrary.wsgi:application
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

### Nginx (Reverse Proxy)

```nginx
upstream elibrary {
    server unix:/var/run/gunicorn.sock;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL Certificates (from Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    location / {
        proxy_pass http://elibrary;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/elibrary/static/;
    }

    location /media/ {
        alias /var/www/elibrary/media/;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## SSL/TLS Certificate Setup

### Let's Encrypt (Free & Automated)

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
sudo systemctl enable certbot.timer
```

### Manual Certificate (Self-signed for testing)
```bash
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```

---

## Monitoring & Logging

### Django Logging Configuration

Update `elibrary/settings.py` to add production logging:

```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "django.log"),
            "maxBytes": 1024 * 1024 * 15,  # 15MB
            "backupCount": 10,
            "formatter": "verbose",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["file", "console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["file", "console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}
```

### Create logs directory:
```bash
mkdir -p logs
chmod 755 logs
```

---

## Backup Strategy

### Database Backups

**PostgreSQL:**
```bash
# Daily backup
pg_dump -U user -h localhost elibrary > /backups/elibrary_$(date +%Y%m%d).sql

# Automated via cron
0 2 * * * pg_dump -U user -h localhost elibrary > /backups/elibrary_$(date +\%Y\%m\%d).sql
```

**MySQL:**
```bash
mysqldump -u user -p elibrary > /backups/elibrary_$(date +%Y%m%d).sql
```

### Media/Static Files
```bash
# Backup every week
0 3 * * 0 tar -czf /backups/elibrary_media_$(date +%Y%m%d).tar.gz /var/www/elibrary/media/
```

---

## Performance Optimization

### Caching

Add to `settings.py`:

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "elibrary",
        "TIMEOUT": 300,  # 5 minutes
    }
}

# Cache session backend for performance
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
```

### Database Optimization

```python
# Connection pooling
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "CONN_MAX_AGE": 600,  # 10 minute connections
        "ATOMIC_REQUESTS": True,  # Transactions per request
    }
}
```

---

## Security Checklist for Deployment

- [ ] Generate and set `ELIBRARY_SECRET_KEY`
- [ ] Set `ELIBRARY_PRODUCTION=True`
- [ ] Set `ELIBRARY_DEBUG=False`
- [ ] Configure `ELIBRARY_ALLOWED_HOSTS` with your domain(s)
- [ ] Install and configure PostgreSQL/MySQL
- [ ] Set up SSL/TLS certificates
- [ ] Configure Nginx/Apache reverse proxy
- [ ] Set up Gunicorn/uWSGI application server
- [ ] Configure Celery and Redis (if using async tasks)
- [ ] Set up logging to `/logs` directory
- [ ] Configure automated backups
- [ ] Set up monitoring (e.g., Sentry, New Relic)
- [ ] Enable 2FA for Django admin
- [ ] Disable admin at non-standard URL
- [ ] Run `python manage.py check --deploy` with exit code 0
- [ ] Load initial data and verify functionality
- [ ] Set up SSL certificate auto-renewal

---

## Quick Start for Local Development

No changes needed! Development settings are already configured:
- `DEBUG=True` by default
- `ALLOWED_HOSTS=['*']` in development
- SQLite database
- Static files auto-served

Just run:
```bash
python manage.py runserver
```

---

## Further Resources

- [Django Deployment Checklist](https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Let's Encrypt](https://letsencrypt.org/)
- [HSTS Preload List](https://hstspreload.org/)
- [SecurityHeaders.com](https://securityheaders.com/)

---

## Support

For security issues or vulnerabilities, please report privately to the development team.

