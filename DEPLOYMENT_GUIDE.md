# Production Deployment Guide

This guide provides step-by-step instructions for deploying TS_OPAC_eLibrary to production using Docker and Docker Compose.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (Docker Compose)](#quick-start-docker-compose)
3. [Manual Deployment (Traditional Server)](#manual-deployment-traditional-server)
4. [SSL/TLS Configuration](#ssltls-configuration)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Troubleshooting](#troubleshooting)
7. [Security Checklist](#security-checklist)

---

## Prerequisites

### For Docker Deployment

- **Docker** 20.10+
- **Docker Compose** 1.29+
- **Git** (for cloning the repository)
- **Domain name** (with DNS pointing to your server)
- **Server specs** (minimum):
  - CPU: 2 cores
  - RAM: 4GB
  - Disk: 50GB
  - OS: Ubuntu 20.04 LTS or similar

### For Traditional Deployment

- **Linux server** (Ubuntu 20.04 LTS recommended)
- **Python** 3.14+
- **PostgreSQL** 13+
- **Redis** 6+
- **Nginx** 1.18+
- **Systemd** (for service management)

---

## Quick Start (Docker Compose)

### 1. Clone and Prepare

```bash
# Clone repository
git clone https://github.com/your-org/TS_OPAC_eLibrary.git
cd TS_OPAC_eLibrary

# Create .env file from template
cp .env.production.template .env.production

# Edit with your production values
nano .env.production
```

### 2. Configure Environment Variables

**Critical variables** (must be set):

```bash
ELIBRARY_SECRET_KEY=<generate-secure-key>
ELIBRARY_PRODUCTION=True
ELIBRARY_DEBUG=False
ELIBRARY_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DB_PASSWORD=<strong-random-password>
REDIS_PASSWORD=<strong-random-password>
```

**Generate secure keys:**

```bash
# In Python 3
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Generate database password
openssl rand -base64 32

# Generate Redis password
openssl rand -base64 32
```

### 3. Build and Start Services

```bash
# Build Docker images
docker-compose build

# Start all services (background)
docker-compose up -d

# View logs
docker-compose logs -f

# Check service health
docker-compose ps
```

### 4. Initialize Database

```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser (admin account)
docker-compose exec web python manage.py createsuperuser

# Load initial data (if needed)
docker-compose exec web python manage.py create_initial_data
```

### 5. Configure Nginx and SSL

```bash
# Update nginx.conf with your domain
sed -i 's/yourdomain.com/your-actual-domain.com/g' nginx.conf

# Restart Nginx to apply changes
docker-compose restart nginx

# Set up SSL with Let's Encrypt (see SSL section below)
```

### 6. Verify Deployment

```bash
# Check application is running
curl http://yourdomain.com

# Check admin panel
curl http://yourdomain.com/admin/

# View logs for errors
docker-compose logs -f web

# Run health checks
docker-compose exec web python manage.py check --deploy
```

---

## Manual Deployment (Traditional Server)

### 1. System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.14 python3.14-venv python3-pip \
    postgresql postgresql-contrib redis-server nginx git \
    certbot python3-certbot-nginx

# Create application user
sudo useradd -m -s /bin/bash elibrary
sudo usermod -aG sudo elibrary
```

### 2. Clone Application

```bash
# Clone repository
sudo -u elibrary git clone https://github.com/your-org/TS_OPAC_eLibrary.git /home/elibrary/app
cd /home/elibrary/app
sudo chown -R elibrary:elibrary .
```

### 3. Set Up Python Environment

```bash
# Create virtual environment
python3.14 -m venv venv
source venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install gunicorn psycopg2-binary redis

# Deactivate venv (we'll use it via systemd)
deactivate
```

### 4. Configure PostgreSQL

```bash
# Switch to postgres user
sudo -u postgres psql

# In psql prompt:
CREATE DATABASE elibrary_db;
CREATE USER elibrary_user WITH PASSWORD 'your_secure_password';
ALTER ROLE elibrary_user SET client_encoding TO 'utf8';
ALTER ROLE elibrary_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE elibrary_user SET default_transaction_deferrable TO on;
ALTER ROLE elibrary_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE elibrary_db TO elibrary_user;
\q
```

### 5. Configure Django

```bash
# Create .env file
sudo -u elibrary cp .env.production.template /home/elibrary/app/.env.production

# Edit configuration
sudo -u elibrary nano /home/elibrary/app/.env.production

# Set proper permissions
sudo chmod 600 /home/elibrary/app/.env.production
sudo chown elibrary:elibrary /home/elibrary/app/.env.production
```

### 6. Run Django Setup

```bash
# Switch to elibrary user
sudo -u elibrary bash
cd /home/elibrary/app
source venv/bin/activate

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Verify system checks
python manage.py check --deploy
```

### 7. Configure Gunicorn Service

**Create `/etc/systemd/system/elibrary.service`:**

```ini
[Unit]
Description=TS_OPAC_eLibrary Gunicorn Application
After=network.target postgresql.service redis-server.service

[Service]
Type=notify
User=elibrary
Group=www-data
WorkingDirectory=/home/elibrary/app
Environment="PATH=/home/elibrary/app/venv/bin"
EnvironmentFile=/home/elibrary/app/.env.production

ExecStart=/home/elibrary/app/venv/bin/gunicorn \
    --workers 4 \
    --worker-class sync \
    --bind unix:/home/elibrary/app/gunicorn.sock \
    --timeout 120 \
    --access-logfile /var/log/elibrary/access.log \
    --error-logfile /var/log/elibrary/error.log \
    elibrary.wsgi:application

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**

```bash
sudo mkdir -p /var/log/elibrary
sudo chown elibrary:www-data /var/log/elibrary
sudo systemctl daemon-reload
sudo systemctl enable elibrary
sudo systemctl start elibrary
sudo systemctl status elibrary
```

### 8. Configure Celery Worker

**Create `/etc/systemd/system/elibrary-celery.service`:**

```ini
[Unit]
Description=TS_OPAC_eLibrary Celery Worker
After=network.target redis-server.service

[Service]
Type=forking
User=elibrary
Group=www-data
WorkingDirectory=/home/elibrary/app
Environment="PATH=/home/elibrary/app/venv/bin"
EnvironmentFile=/home/elibrary/app/.env.production

ExecStart=/home/elibrary/app/venv/bin/celery -A elibrary worker \
    --loglevel=info \
    --logfile=/var/log/elibrary/celery.log \
    --pidfile=/var/run/celery.pid

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable elibrary-celery
sudo systemctl start elibrary-celery
sudo systemctl status elibrary-celery
```

### 9. Configure Nginx

```bash
# Create Nginx configuration
sudo cp nginx.conf /etc/nginx/sites-available/elibrary

# Enable site
sudo ln -s /etc/nginx/sites-available/elibrary /etc/nginx/sites-enabled/elibrary

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

**Or use included nginx.conf template:**

```bash
# Update server_name in nginx.conf
sed -i 's/yourdomain.com/your-actual-domain.com/g' nginx.conf

# Copy to system
sudo cp nginx.conf /etc/nginx/nginx.conf

# Test and restart
sudo nginx -t && sudo systemctl restart nginx
```

---

## SSL/TLS Configuration

### Option 1: Let's Encrypt with Certbot (Recommended)

```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Certbot will save certificates to: /etc/letsencrypt/live/yourdomain.com/

# Update nginx.conf with certificate paths:
# ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
# ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

# Test renewal
sudo certbot renew --dry-run

# Automatic renewal (runs daily via cron)
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### Option 2: Self-Signed Certificate (Development Only)

```bash
# Generate self-signed certificate (valid 365 days)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/privkey.pem \
    -out /etc/nginx/ssl/fullchain.pem

# Update nginx.conf to use these files
# Reload Nginx
sudo systemctl reload nginx
```

### Option 3: Paid SSL Certificate

1. Purchase certificate from provider (DigiCert, Comodo, etc.)
2. Download certificate and key files
3. Upload to server:
   ```bash
   scp certificate.crt user@server:/etc/nginx/ssl/
   scp private.key user@server:/etc/nginx/ssl/
   ```
4. Update nginx.conf with paths
5. Reload Nginx

---

## Monitoring & Maintenance

### Health Checks

```bash
# Check application status
curl https://yourdomain.com/health

# Check Django system
ssh user@server
cd /home/elibrary/app
source venv/bin/activate
python manage.py check --deploy

# Check service status
systemctl status elibrary
systemctl status elibrary-celery
systemctl status nginx
systemctl status postgresql
systemctl status redis-server
```

### Logs

```bash
# Application logs
tail -f /var/log/elibrary/access.log
tail -f /var/log/elibrary/error.log

# Celery logs
tail -f /var/log/elibrary/celery.log

# System logs
sudo journalctl -u elibrary -f
sudo journalctl -u elibrary-celery -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Database Backups

```bash
# Manual backup
pg_dump -U elibrary_user -h localhost elibrary_db > backup-$(date +%Y%m%d_%H%M%S).sql

# Automated backup (add to crontab)
# 0 2 * * * pg_dump -U elibrary_user -h localhost elibrary_db | gzip > /backups/elibrary-$(date +\%Y\%m\%d).sql.gz

# Restore from backup
psql -U elibrary_user -h localhost elibrary_db < backup.sql
```

### Update Application

```bash
# Pull latest code
sudo -u elibrary git -C /home/elibrary/app pull origin main

# Install new dependencies (if needed)
source /home/elibrary/app/venv/bin/activate
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart services
sudo systemctl restart elibrary
sudo systemctl restart elibrary-celery
```

---

## Troubleshooting

### Application Won't Start

```bash
# Check logs
sudo journalctl -u elibrary -n 50

# Check Gunicorn socket
ls -l /home/elibrary/app/gunicorn.sock

# Test manually
source /home/elibrary/app/venv/bin/activate
cd /home/elibrary/app
gunicorn --bind 127.0.0.1:8000 elibrary.wsgi:application

# Check environment variables
cat /home/elibrary/app/.env.production
```

### Database Connection Error

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -U elibrary_user -h localhost -d elibrary_db

# Check DATABASE_URL in .env.production
cat /home/elibrary/app/.env.production | grep DATABASE_URL
```

### Celery Not Processing Tasks

```bash
# Check Redis is running
sudo systemctl status redis-server

# Test Redis connection
redis-cli ping

# Check Celery worker logs
sudo journalctl -u elibrary-celery -f

# Verify CELERY_BROKER_URL
echo $CELERY_BROKER_URL
```

### SSL Certificate Issues

```bash
# Check certificate expiration
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/fullchain.pem -text -noout | grep -A 2 Validity

# Test SSL configuration
openssl s_client -connect yourdomain.com:443

# Force renewal
sudo certbot renew --force-renewal
```

### High CPU/Memory Usage

```bash
# Check processes
top -p $(pgrep -d',' gunicorn)

# Check for stuck tasks in Celery
celery -A elibrary inspect active

# Increase Gunicorn workers (in elibrary.service)
# Change: --workers 4 to --workers 8

# Restart service
sudo systemctl restart elibrary
```

---

## Security Checklist

Before going live:

- [ ] Generate and configure secure `ELIBRARY_SECRET_KEY`
- [ ] Set `ELIBRARY_PRODUCTION=True` in environment
- [ ] Set `ELIBRARY_DEBUG=False`
- [ ] Configure `ELIBRARY_ALLOWED_HOSTS` with your domain(s)
- [ ] Set strong database password
- [ ] Set strong Redis password
- [ ] Configure SSL/TLS certificate (Let's Encrypt recommended)
- [ ] Enable HSTS in nginx.conf (test first with lower max-age)
- [ ] Set up database backups (automated daily)
- [ ] Configure email backend for password resets
- [ ] Set up logging and monitoring (Sentry recommended)
- [ ] Create and secure superuser account
- [ ] Disable SSH password authentication (use keys)
- [ ] Configure firewall (allow only 80, 443, 22)
- [ ] Run `python manage.py check --deploy` and address warnings
- [ ] Test SSL with [SSL Labs](https://www.ssllabs.com/)
- [ ] Test security headers with [Security Headers](https://securityheaders.com/)
- [ ] Set up uptime monitoring
- [ ] Document admin procedures (backup, update, recovery)
- [ ] Create incident response plan
- [ ] Schedule regular security audits

---

## Support

For issues:

1. Check logs: `journalctl -u elibrary -f`
2. Verify configuration: `python manage.py check --deploy`
3. Test connectivity: `curl -v https://yourdomain.com`
4. Review Django docs: https://docs.djangoproject.com/en/4.2/howto/deployment/

---

**Last Updated:** 2024
**Django Version:** 4.2+
**Python Version:** 3.14+
