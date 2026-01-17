# Raspberry Pi Deployment Manual
## TS_OPAC eLibrary System

**Version:** 1.0  
**Date:** January 17, 2026  
**Target:** Raspberry Pi 4/5 (4GB RAM minimum)  
**OS:** Raspberry Pi OS (Debian-based)

---

## Table of Contents
1. [Hardware Requirements](#hardware-requirements)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Operating System Setup](#operating-system-setup)
4. [Dependencies Installation](#dependencies-installation)
5. [Database Setup](#database-setup)
6. [Application Deployment](#application-deployment)
7. [Service Configuration](#service-configuration)
8. [Performance Tuning](#performance-tuning)
9. [Monitoring & Maintenance](#monitoring--maintenance)

---

## Hardware Requirements

### Minimum Specifications
- **Device:** Raspberry Pi 4 (4GB RAM) or Raspberry Pi 5
- **Storage:** 64GB SD Card (UHS-II Class 3 recommended)
- **Power:** 5.1V/3A USB-C power supply
- **Cooling:** Heat sink and fan (for Pi 5 or heavy use)
- **Network:** Gigabit Ethernet adapter

### Recommended Specifications
- **Device:** Raspberry Pi 5 (8GB RAM)
- **Storage:** 128GB NVMe SSD with USB adapter
- **Power:** 5.1V/5A USB-C power supply
- **Cooling:** Active cooling/fan
- **Network:** Gigabit Ethernet with PoE

### Additional Hardware
- 2x USB 3.0 hubs (for external storage if needed)
- Network cable (Cat6 or better)
- HDMI cable (for initial setup, optional for headless)

---

## Pre-Deployment Checklist

- [ ] Raspberry Pi OS installed and updated
- [ ] Network connectivity configured (Ethernet preferred)
- [ ] SSH enabled and credentials secured
- [ ] Storage space verified (20GB minimum free space)
- [ ] Backup of current system created
- [ ] PostgreSQL server accessible and configured
- [ ] SSL certificates prepared
- [ ] Environment variables documented
- [ ] Port availability verified (80, 443, 5432)

---

## Operating System Setup

### 1. Flash Raspberry Pi OS

```bash
# On your computer, download Raspberry Pi Imager
# Available at: https://www.raspberrypi.com/software/

# Flash to SD Card:
1. Insert SD card into card reader
2. Open Raspberry Pi Imager
3. Select "Raspberry Pi OS (64-bit)"
4. Choose SD card as storage
5. Click Write
6. Wait for completion (~10-15 minutes)
```

### 2. Initial Boot Configuration

```bash
# Connect to network and power on Raspberry Pi
# SSH from another machine:
ssh pi@raspberrypi.local

# Or use IP address if hostname doesn't resolve:
ssh pi@<raspberry_pi_ip>

# Default password: raspberry (CHANGE IMMEDIATELY)
passwd
```

### 3. System Update

```bash
sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y

# Set timezone
sudo timedatectl set-timezone UTC
# or: sudo timedatectl set-timezone Asia/Manila

# Verify time sync
timedatectl

# Enable SSH
sudo systemctl enable ssh
sudo systemctl start ssh
```

### 4. Configure Swap (Important for Pi performance)

```bash
# Check current swap
free -h

# Increase swap to 2GB (default is 100MB)
sudo nano /etc/dphys-swapfile

# Change: CONF_SWAPSIZE=2048
# Save: Ctrl+X, Y, Enter

# Restart swap service
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### 5. Network Configuration

```bash
# For static IP (Ethernet):
sudo nano /etc/dhcpcd.conf

# Add to end of file:
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=8.8.8.8 8.8.4.4

# Restart networking
sudo systemctl restart dhcpcd
```

---

## Dependencies Installation

### 1. Install System Dependencies

```bash
sudo apt install -y \
  python3.11 \
  python3.11-venv \
  python3.11-dev \
  python3-pip \
  build-essential \
  libssl-dev \
  libffi-dev \
  libpq-dev \
  postgresql-client \
  curl \
  wget \
  git \
  nano \
  htop \
  nginx \
  supervisor
```

### 2. Create Application User

```bash
# Create dedicated user for application
sudo useradd -m -s /bin/bash opac

# Create application directory
sudo mkdir -p /srv/opac-elibrary
sudo chown opac:opac /srv/opac-elibrary
sudo chmod 755 /srv/opac-elibrary

# Switch to app user
sudo su - opac
```

### 3. Set Up Python Virtual Environment

```bash
cd /srv/opac-elibrary

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Verify Python version
python --version
```

### 4. Clone Project Repository

```bash
# Clone from GitHub (as opac user)
git clone https://github.com/Dang62899/TS_OPAC_eLibrary.git .

# Alternative: Copy from compressed backup
# tar -xzf opac-backup.tar.gz -C /srv/opac-elibrary

# Verify clone
ls -la
```

### 5. Install Python Dependencies

```bash
# Activate venv if not active
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Verify key packages
pip list | grep -E "Django|psycopg2|gunicorn|nginx"
```

---

## Database Setup

### 1. PostgreSQL Remote Connection

```bash
# Test connection to remote PostgreSQL server
psql -h <postgres_server_ip> -U opac_user -d opac_db -c "SELECT 1;"

# If prompted for password, add to ~/.pgpass
nano ~/.pgpass
# Format: hostname:port:database:username:password
# Example: 192.168.1.50:5432:opac_db:opac_user:your_password
chmod 600 ~/.pgpass
```

### 2. Django Database Migration

```bash
cd /srv/opac-elibrary

# Activate venv
source venv/bin/activate

# Test database connection
python manage.py dbshell

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
# Follow prompts for username, email, password

# Load sample data (optional)
python manage.py create_sample_books

# Verify
python manage.py shell
>>> from django.contrib.auth.models import User
>>> User.objects.count()  # Should show user count
>>> exit()
```

### 3. Collect Static Files

```bash
python manage.py collectstatic --noinput

# Verify collection
ls -la static/
```

---

## Application Deployment

### 1. Gunicorn Configuration

```bash
# Create Gunicorn service file
sudo nano /etc/systemd/system/opac-gunicorn.service
```

```ini
[Unit]
Description=TS OPAC eLibrary Gunicorn Service
After=network.target postgresql.service

[Service]
Type=notify
User=opac
Group=opac
WorkingDirectory=/srv/opac-elibrary
Environment="PATH=/srv/opac-elibrary/venv/bin"
ExecStart=/srv/opac-elibrary/venv/bin/gunicorn \
    --workers 2 \
    --worker-class sync \
    --bind unix:/srv/opac-elibrary/gunicorn.sock \
    --timeout 60 \
    --access-logfile /var/log/opac/gunicorn-access.log \
    --error-logfile /var/log/opac/gunicorn-error.log \
    elibrary.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
# Create log directory
sudo mkdir -p /var/log/opac
sudo chown opac:opac /var/log/opac

# Enable and start service
sudo systemctl enable opac-gunicorn.service
sudo systemctl start opac-gunicorn.service

# Check status
sudo systemctl status opac-gunicorn.service
```

### 2. Nginx Configuration

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/opac-elibrary
```

```nginx
upstream opac_app {
    server unix:/srv/opac-elibrary/gunicorn.sock fail_timeout=0;
}

server {
    listen 80;
    server_name raspberrypi.local 192.168.1.100;

    client_max_body_size 50M;

    location / {
        proxy_pass http://opac_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    location /static/ {
        alias /srv/opac-elibrary/static/;
        expires 7d;
    }

    location /media/ {
        alias /srv/opac-elibrary/media/;
        expires 7d;
    }
}
```

```bash
# Enable Nginx site
sudo ln -s /etc/nginx/sites-available/opac-elibrary \
    /etc/nginx/sites-enabled/opac-elibrary

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Enable and start Nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 3. Environment Variables

```bash
# Create .env file in app directory
nano /srv/opac-elibrary/.env
```

```bash
# Django settings
DEBUG=False
SECRET_KEY=your_secret_key_here
ALLOWED_HOSTS=raspberrypi.local,192.168.1.100

# Database
DATABASE_URL=postgresql://opac_user:password@192.168.1.50:5432/opac_db

# Email configuration (optional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Security
SECURE_SSL_REDIRECT=False  # Set to True if using HTTPS
SESSION_COOKIE_SECURE=False  # Set to True if using HTTPS
CSRF_COOKIE_SECURE=False  # Set to True if using HTTPS
```

```bash
# Update Django settings to load from .env
# Edit elibrary/settings.py to include:
# import os
# from dotenv import load_dotenv
# load_dotenv()
# SECRET_KEY = os.getenv('SECRET_KEY')
```

---

## Service Configuration

### 1. Supervisor Configuration (for automatic restarts)

```bash
sudo nano /etc/supervisor/conf.d/opac-elibrary.conf
```

```ini
[program:opac-gunicorn]
command=/srv/opac-elibrary/venv/bin/gunicorn \
    --workers 2 \
    --bind unix:/srv/opac-elibrary/gunicorn.sock \
    elibrary.wsgi:application
directory=/srv/opac-elibrary
user=opac
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/opac/supervisor.log
environment=PATH="/srv/opac-elibrary/venv/bin"
```

```bash
# Update supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status
```

### 2. Cron Jobs for Maintenance

```bash
# Edit opac user crontab
crontab -e
```

```bash
# Daily database backup at 2 AM
0 2 * * * /srv/opac-elibrary/scripts/backup_db.sh

# Weekly cache cleanup at Sunday 3 AM
0 3 * * 0 python /srv/opac-elibrary/manage.py clearcache

# Monitor system resources every hour
0 * * * * /srv/opac-elibrary/scripts/check_resources.sh
```

---

## Performance Tuning

### 1. Raspberry Pi Overclocking (Optional, for Pi 4+)

```bash
# Edit boot configuration
sudo nano /boot/firmware/config.txt

# Add or modify (for Pi 4):
[pi4]
over_voltage=6
arm_freq=2000
gpu_freq=600

# For Pi 5 (note: different overclocking approach):
# Pi 5 doesn't support traditional overclocking but has thermal management
# Enable active cooling in firmware if available
```

### 2. Memory Optimization

```bash
# Disable unnecessary services
sudo systemctl disable bluetooth.service
sudo systemctl disable wpa_supplicant.service

# Reduce GPU memory (if not using display)
sudo nano /boot/firmware/config.txt
# Add: gpu_mem=64

# Reboot to apply
sudo reboot
```

### 3. Disk I/O Optimization

```bash
# Enable write caching for Nginx
sudo nano /etc/nginx/nginx.conf

# Add to http block:
# proxy_buffering on;
# proxy_buffer_size 128k;
# proxy_buffers 4 256k;
```

### 4. Database Connection Pooling

```bash
# In Django settings, configure connection pooling
# Add to elibrary/settings.py:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}
```

---

## Monitoring & Maintenance

### 1. System Monitoring

```bash
# Check system resources
free -h              # Memory usage
df -h                # Disk usage
top -b -n 1          # CPU usage
vcgencmd measure_temp # CPU temperature (Raspberry Pi specific)
```

### 2. Application Logs

```bash
# Gunicorn logs
tail -f /var/log/opac/gunicorn-error.log
tail -f /var/log/opac/gunicorn-access.log

# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Django logs (if configured)
tail -f /srv/opac-elibrary/logs/django.log
```

### 3. Service Health Checks

```bash
# Check all services
sudo systemctl status opac-gunicorn.service
sudo systemctl status nginx.service

# Verify Gunicorn socket
ls -la /srv/opac-elibrary/gunicorn.sock

# Test application endpoint
curl http://raspberrypi.local/
curl http://192.168.1.100/
```

### 4. Backup Strategy

```bash
# Database backup
pg_dump -h 192.168.1.50 -U opac_user opac_db | \
  gzip > /srv/opac-elibrary/backups/db_$(date +%Y%m%d).sql.gz

# Application backup
tar -czf /srv/opac-elibrary/backups/app_$(date +%Y%m%d).tar.gz \
  --exclude='venv' --exclude='.git' \
  /srv/opac-elibrary

# Keep last 7 days of backups
find /srv/opac-elibrary/backups -name "*.gz" -mtime +7 -delete
```

### 5. Troubleshooting Commands

```bash
# Restart all services
sudo systemctl restart opac-gunicorn.service nginx.service

# Check for port conflicts
sudo netstat -tlnp | grep -E ':80|:443|:8000'

# Verify database connection
python /srv/opac-elibrary/manage.py dbshell

# Clear Django cache
python /srv/opac-elibrary/manage.py flush_cache

# Check disk health (if using SSD)
sudo apt install smartmontools
sudo smartctl -a /dev/sda  # For external storage
```

---

## Post-Deployment Validation

### Checklist

- [ ] Gunicorn service running (`systemctl status opac-gunicorn.service`)
- [ ] Nginx service running (`systemctl status nginx.service`)
- [ ] Application accessible at `http://raspberrypi.local`
- [ ] Admin panel accessible at `/admin`
- [ ] Database queries responding normally
- [ ] Static files serving correctly
- [ ] Log files being created and updated
- [ ] Backup scripts executing on schedule
- [ ] System resources stable (CPU <60%, Memory <80%)
- [ ] Network connectivity stable

---

## Emergency Procedures

### Service Recovery

```bash
# If Gunicorn crashes:
sudo systemctl restart opac-gunicorn.service
sudo systemctl status opac-gunicorn.service

# If Nginx crashes:
sudo systemctl restart nginx.service
sudo nginx -t  # Test config before restart

# If database connection fails:
# Check PostgreSQL server is running
# Verify network connectivity
# Check credentials in .env file
```

### Rollback Procedure

```bash
# Restore from backup
tar -xzf /srv/opac-elibrary/backups/app_$(date +%Y%m%d).tar.gz

# Restart services
sudo systemctl restart opac-gunicorn.service

# Verify application
curl http://raspberrypi.local/
```

---

## References

- Raspberry Pi Documentation: https://www.raspberrypi.com/documentation/
- Django Deployment: https://docs.djangoproject.com/en/5.0/howto/deployment/
- Gunicorn: https://gunicorn.org/
- Nginx: https://nginx.org/en/
- PostgreSQL: https://www.postgresql.org/docs/

---

**Last Updated:** January 17, 2026  
**Support:** Contact system administrator or refer to TROUBLESHOOTING.md for common issues.
