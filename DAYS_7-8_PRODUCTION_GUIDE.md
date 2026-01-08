# Days 7-8: Production Deployment & Monitoring Guide

## Overview
Transform the development application into a production-ready system with:
- SSL/TLS encryption
- Security hardening
- Email configuration
- Backup strategy
- Error tracking (Sentry)
- Performance monitoring

---

## Day 7: Production Deployment

### Phase 1: Django Settings for Production

Create `elibrary/settings_production.py`:

```python
from .settings import *
import os

# Security
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com', 'localhost']

# Secret Key (use environment variable)
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'change-me-in-production')

# HTTPS/SSL
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@yourlibrary.com')

# Database SSL (optional but recommended)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'elibrary'),
        'USER': os.environ.get('DB_USER', 'elibrary'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'db'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'sslmode': 'require',  # Enable SSL for database
        } if os.environ.get('DB_SSL', 'False') == 'True' else {}
    }
}

# Caching
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Logging for Production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.environ.get('LOG_FILE', '/var/log/elibrary/django.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'security': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.environ.get('SECURITY_LOG_FILE', '/var/log/elibrary/security.log'),
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# Sentry Error Tracking
if os.environ.get('SENTRY_DSN'):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    
    sentry_sdk.init(
        dsn=os.environ.get('SENTRY_DSN'),
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,  # 10% of transactions
        send_default_pii=False,
        environment=os.environ.get('ENVIRONMENT', 'production'),
    )

# Static Files with WhiteNoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

---

### Phase 2: Production Environment Variables

Create `.env.production`:

```bash
# Django
DJANGO_SETTINGS_MODULE=elibrary.settings_production
DJANGO_SECRET_KEY=your-super-secret-key-here-min-50-chars
ENVIRONMENT=production

# Database
DB_NAME=elibrary
DB_USER=elibrary
DB_PASSWORD=your-db-password-here
DB_HOST=db
DB_PORT=5432
DB_SSL=False

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourlibrary.com

# Redis (for caching)
REDIS_URL=redis://redis:6379/1

# Logging
LOG_FILE=/var/log/elibrary/django.log
SECURITY_LOG_FILE=/var/log/elibrary/security.log
DJANGO_LOG_LEVEL=WARNING

# Sentry (Error Tracking)
SENTRY_DSN=https://your-key@sentry.io/your-project-id

# SSL Certificates
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem

# Allowed Hosts
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Admin URL (change from /admin/ for security)
ADMIN_URL=hidden-admin-url-123456/

# API Settings
API_RATE_LIMIT=100/hour
API_PAGINATION_SIZE=20
```

---

### Phase 3: Updated docker-compose.yml for Production

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: elibrary_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - elibrary_network

  redis:
    image: redis:7-alpine
    container_name: elibrary_redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - elibrary_network

  web:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: elibrary_web
    env_file:
      - .env.production
    command: >
      sh -c "python manage.py migrate &&
             python manage.py collectstatic --noinput &&
             gunicorn -w 4 -b 0.0.0.0:8000 --timeout 60 
             --access-logfile - --error-logfile - 
             elibrary.wsgi:application"
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - ./logs:/var/log/elibrary
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    restart: unless-stopped
    networks:
      - elibrary_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    container_name: elibrary_nginx
    volumes:
      - ./nginx_production.conf:/etc/nginx/nginx.conf
      - static_volume:/app/staticfiles:ro
      - media_volume:/app/media:ro
      - ./ssl:/etc/nginx/ssl:ro
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web
    restart: unless-stopped
    networks:
      - elibrary_network
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/health/"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
    driver: local
  static_volume:
    driver: local
  media_volume:
    driver: local

networks:
  elibrary_network:
    driver: bridge
```

---

### Phase 4: Production Nginx Configuration

Create `nginx_production.conf`:

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    # Performance optimizations
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 20M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss 
               application/rss+xml font/truetype font/opentype 
               application/vnd.ms-fontobject image/svg+xml;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=general:10m rate=100r/m;
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    # SSL session caching
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;

    # Upstream
    upstream django_app {
        server web:8000;
    }

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name _;
        return 301 https://$host$request_uri;
    }

    # HTTPS Server
    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        # SSL Certificates
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # SSL Configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;
        ssl_stapling on;
        ssl_stapling_verify on;

        # Security Headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-Frame-Options "DENY" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
        add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; img-src 'self' data: https:;" always;

        # Static files
        location /static/ {
            alias /app/staticfiles/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        # Media files
        location /media/ {
            alias /app/media/;
            expires 7d;
            add_header Cache-Control "public";
        }

        # Health check endpoint (no rate limiting)
        location /health/ {
            proxy_pass http://django_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            access_log off;
        }

        # API endpoints (strict rate limiting)
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://django_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # General rate limiting
        location / {
            limit_req zone=general burst=10 nodelay;
            proxy_pass http://django_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Deny access to sensitive files
        location ~ /\. {
            deny all;
            access_log off;
            log_not_found off;
        }

        location ~ ~$ {
            deny all;
            access_log off;
            log_not_found off;
        }
    }
}
```

---

### Phase 5: SSL Certificate Setup

#### Option 1: Let's Encrypt (Free, Recommended)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Copy to ssl directory
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./ssl/key.pem
sudo chmod 644 ./ssl/cert.pem
sudo chmod 600 ./ssl/key.pem

# Auto-renewal (runs daily)
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

#### Option 2: Self-Signed Certificate (Development)

```bash
openssl req -x509 -newkey rsa:4096 -nodes -out ./ssl/cert.pem -keyout ./ssl/key.pem -days 365
```

---

### Phase 6: Production Deployment Commands

```bash
# 1. Generate secrets
python -c "import secrets; print(secrets.token_urlsafe(50))"  # Copy as DJANGO_SECRET_KEY

# 2. Create environment file
cp .env.production.example .env.production
# Edit .env.production with your values

# 3. Create log directory
mkdir -p logs
chmod 755 logs

# 4. Create SSL directory
mkdir -p ssl
chmod 700 ssl

# 5. Setup SSL certificates (see Phase 5)
# Place cert.pem and key.pem in ssl/ directory

# 6. Start production stack
COMPOSE_FILE=docker-compose.yml \
ENVIRONMENT=production \
docker-compose up -d

# 7. Run initial setup
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic --noinput

# 8. Verify deployment
docker-compose ps
docker-compose logs web
```

---

### Phase 7: Database Backup Strategy

Create `backup_database.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/elibrary_backup_$TIMESTAMP.sql"

# Create backup
docker-compose exec -T db pg_dump -U elibrary elibrary > "$BACKUP_FILE"

# Compress backup
gzip "$BACKUP_FILE"

# Keep only last 30 days of backups
find "$BACKUP_DIR" -name "elibrary_backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: ${BACKUP_FILE}.gz"
```

```bash
# Make executable
chmod +x backup_database.sh

# Add to crontab (daily at 2 AM)
0 2 * * * /path/to/backup_database.sh
```

---

### Phase 8: Health Check Endpoint

Add to `catalog/views.py`:

```python
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import connection

@require_http_methods(["GET"])
def health_check(request):
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'database': 'connected'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=503)
```

Add to `catalog/urls.py`:

```python
path('health/', views.health_check, name='health_check'),
```

---

## Day 8: Monitoring & Error Tracking

### Phase 1: Sentry Setup

```bash
# 1. Create Sentry account
# Visit: https://sentry.io/signup/

# 2. Create new project (Django)
# Copy your DSN

# 3. Install Sentry SDK
pip install sentry-sdk

# 4. Add to .env.production
SENTRY_DSN=https://your-key@sentry.io/your-project-id

# 5. Update requirements.txt
echo "sentry-sdk==1.40.0" >> requirements.txt
```

---

### Phase 2: Prometheus Monitoring

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'django'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics/'
```

---

### Phase 3: Production Verification Checklist

```bash
# Test HTTPS
curl -I https://yourdomain.com

# Check security headers
curl -I https://yourdomain.com | grep -E "Strict-Transport|X-Content-Type"

# Test API
curl https://yourdomain.com/api/search/advanced/

# Verify database backup
ls -lah backups/

# Check logs
docker-compose logs web --tail 50

# Test health endpoint
curl https://yourdomain.com/health/

# Verify Sentry integration
# Create a test error to confirm Sentry receives it
```

---

## Production Checklist

```
Security:
- [ ] SSL/TLS configured and working
- [ ] DEBUG = False
- [ ] ALLOWED_HOSTS updated
- [ ] SECRET_KEY is strong (>50 chars)
- [ ] Email configured and tested
- [ ] Security headers verified
- [ ] Rate limiting active
- [ ] CORS properly configured

Infrastructure:
- [ ] Database backups automated
- [ ] Logs directory created
- [ ] SSL certificates renewed automatically
- [ ] Health check endpoint working
- [ ] Container restart policies set
- [ ] Volume mounts persistent

Monitoring:
- [ ] Sentry DSN configured
- [ ] Error notifications working
- [ ] Log aggregation active
- [ ] Health checks passing
- [ ] Metrics collection enabled
- [ ] Alerting rules configured

Testing:
- [ ] HTTPS working (all endpoints)
- [ ] Database queries responding
- [ ] Email sending working
- [ ] Static files serving
- [ ] API rate limiting working
- [ ] Admin panel accessible

Documentation:
- [ ] Environment variables documented
- [ ] Deployment process documented
- [ ] Backup/restore procedure documented
- [ ] SSL renewal process documented
- [ ] Troubleshooting guide created
```

---

**Status**: Ready for implementation
**Estimated Time**: 6-8 hours for Days 7-8
**Next**: Execute Day 7 production deployment
