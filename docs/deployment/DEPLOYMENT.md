# OPAC eLibrary - Deployment Guide

## Production Deployment Checklist

### 1. Environment Setup

1. **Clone or copy the project** to your production server
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Linux/Mac
   venv\Scripts\activate     # On Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### 2. Environment Configuration

1. **Copy the environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file** and configure:
   - Generate a new `SECRET_KEY` (use Django's `get_random_secret_key()`)
   - Set `DEBUG=False`
   - Add your domain to `ALLOWED_HOSTS`
   - Configure database settings (PostgreSQL or MySQL recommended)
   - Set up email server credentials
   - Configure Redis connection for Celery

### 3. Database Setup

#### Option A: PostgreSQL (Recommended for Production)

1. **Install PostgreSQL** and create database:
   ```sql
   CREATE DATABASE elibrary_db;
   CREATE USER elibrary_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE elibrary_db TO elibrary_user;
   ```

2. **Update `.env`** with database credentials:
   ```
   DATABASE_ENGINE=django.db.backends.postgresql
   DATABASE_NAME=elibrary_db
   DATABASE_USER=elibrary_user
   DATABASE_PASSWORD=your_password
   DATABASE_HOST=localhost
   DATABASE_PORT=5432
   ```

3. **Install psycopg2**:
   ```bash
   pip install psycopg2-binary
   ```

#### Option B: MySQL

1. **Create MySQL database**:
   ```sql
   CREATE DATABASE elibrary_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'elibrary_user'@'localhost' IDENTIFIED BY 'your_password';
   GRANT ALL PRIVILEGES ON elibrary_db.* TO 'elibrary_user'@'localhost';
   ```

2. **Update `.env`** and install mysqlclient:
   ```bash
   pip install mysqlclient
   ```

### 4. Django Setup

1. **Update settings for production** (edit `elibrary/settings.py`):
   - Ensure `DEBUG = False`
   - Configure `STATIC_ROOT` and `MEDIA_ROOT`
   - Set up `ALLOWED_HOSTS` properly
   - Configure security settings (CSRF, HTTPS, etc.)

2. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

3. **Create superuser**:
   ```bash
   python manage.py createsuperuser
   ```

4. **Load initial data** (publication types, locations, etc.):
   ```bash
   python manage.py create_initial_data
   ```

5. **Collect static files**:
   ```bash
   python manage.py collectstatic --noinput
   ```

### 5. Security Configuration

#### Update `elibrary/settings.py`:

```python
# Security Settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HSTS
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Static files with WhiteNoise
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add this
    # ... other middleware
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### 6. Redis Setup

1. **Install Redis**:
   - Linux: `sudo apt-get install redis-server`
   - macOS: `brew install redis`
   - Windows: Use WSL or download from https://redis.io/download

2. **Start Redis**:
   ```bash
   redis-server
   ```

3. **Verify connection**:
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

### 7. Celery Setup

1. **Start Celery worker**:
   ```bash
   celery -A elibrary worker -l info
   ```

2. **Start Celery beat** (for scheduled tasks):
   ```bash
   celery -A elibrary beat -l info
   ```

3. **Production: Use supervisor or systemd** to manage Celery processes

#### Example systemd service (`/etc/systemd/system/celery.service`):

```ini
[Unit]
Description=Celery Service
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/path/to/OPAC_eLib
Environment="PATH=/path/to/OPAC_eLib/venv/bin"
ExecStart=/path/to/OPAC_eLib/venv/bin/celery -A elibrary worker --detach
ExecStop=/bin/kill -s TERM $MAINPID

[Install]
WantedBy=multi-user.target
```

### 8. Web Server Setup

#### Option A: Gunicorn + Nginx

1. **Install Gunicorn**:
   ```bash
   pip install gunicorn
   ```

2. **Test Gunicorn**:
   ```bash
   gunicorn elibrary.wsgi:application --bind 0.0.0.0:8000
   ```

3. **Create systemd service** (`/etc/systemd/system/gunicorn.service`):
   ```ini
   [Unit]
   Description=gunicorn daemon
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/path/to/OPAC_eLib
   ExecStart=/path/to/OPAC_eLib/venv/bin/gunicorn \
             --workers 3 \
             --bind unix:/path/to/OPAC_eLib/gunicorn.sock \
             elibrary.wsgi:application

   [Install]
   WantedBy=multi-user.target
   ```

4. **Configure Nginx** (`/etc/nginx/sites-available/elibrary`):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location /static/ {
           alias /path/to/OPAC_eLib/staticfiles/;
       }

       location /media/ {
           alias /path/to/OPAC_eLib/media/;
       }

       location / {
           proxy_pass http://unix:/path/to/OPAC_eLib/gunicorn.sock;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

5. **Enable site and restart Nginx**:
   ```bash
   sudo ln -s /etc/nginx/sites-available/elibrary /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

#### Option B: Apache + mod_wsgi

See Django documentation for Apache configuration.

### 9. SSL Certificate (HTTPS)

1. **Install Certbot**:
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   ```

2. **Obtain certificate**:
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

3. **Auto-renewal** is configured automatically by Certbot

### 10. Monitoring & Logging

1. **Configure Django logging** in `settings.py`
2. **Set up error monitoring** (e.g., Sentry)
3. **Monitor Celery tasks**
4. **Set up database backups**

### 11. Performance Optimization

1. **Enable caching** (Redis or Memcached)
2. **Optimize database queries**
3. **Use CDN for static files** (optional)
4. **Enable Gzip compression** (WhiteNoise handles this)

### 12. Backup Strategy

1. **Database backups**:
   ```bash
   # PostgreSQL
   pg_dump -U elibrary_user elibrary_db > backup_$(date +%Y%m%d).sql
   
   # MySQL
   mysqldump -u elibrary_user -p elibrary_db > backup_$(date +%Y%m%d).sql
   ```

2. **Media files backup**:
   ```bash
   tar -czf media_backup_$(date +%Y%m%d).tar.gz media/
   ```

3. **Automate with cron**:
   ```bash
   0 2 * * * /path/to/backup_script.sh
   ```

## Environment Variables Reference

| Variable | Description | Required |
|----------|-------------|----------|
| SECRET_KEY | Django secret key | Yes |
| DEBUG | Debug mode (False in production) | Yes |
| ALLOWED_HOSTS | Comma-separated list of allowed hosts | Yes |
| DATABASE_ENGINE | Database backend | Yes |
| DATABASE_NAME | Database name | Yes |
| DATABASE_USER | Database user | Yes |
| DATABASE_PASSWORD | Database password | Yes |
| EMAIL_HOST | SMTP server | Yes |
| EMAIL_PORT | SMTP port | Yes |
| EMAIL_HOST_USER | Email username | Yes |
| EMAIL_HOST_PASSWORD | Email password | Yes |
| CELERY_BROKER_URL | Redis URL for Celery | Yes |

## Troubleshooting

### Static files not loading
```bash
python manage.py collectstatic --clear
```

### Database connection errors
- Check database credentials in `.env`
- Verify database service is running
- Check firewall rules

### Celery tasks not running
- Verify Redis is running: `redis-cli ping`
- Check Celery worker logs
- Ensure `CELERY_BROKER_URL` is correct

### Email notifications not sending
- Verify SMTP credentials
- Check if less secure app access is enabled (Gmail)
- Review email backend configuration

## Production Checklist

- [ ] DEBUG = False
- [ ] SECRET_KEY is unique and secure
- [ ] Database is PostgreSQL or MySQL (not SQLite)
- [ ] All sensitive data in .env file
- [ ] Static files collected
- [ ] Media directory has proper permissions
- [ ] ALLOWED_HOSTS configured
- [ ] SSL certificate installed
- [ ] Firewall configured
- [ ] Backup strategy implemented
- [ ] Monitoring set up
- [ ] Email notifications tested
- [ ] Celery workers running
- [ ] Redis server running
- [ ] Security headers configured
- [ ] Error pages customized (404, 500)

## Support

For issues and questions, refer to:
- Django documentation: https://docs.djangoproject.com/
- Celery documentation: https://docs.celeryproject.org/
- Project README.md
