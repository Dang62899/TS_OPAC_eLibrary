# Days 3-4: Production Deployment Setup Guide

## Overview
This guide covers containerizing the TS OPAC eLibrary application with Docker, setting up Nginx as a reverse proxy, and configuring Systemd services for production deployment on Ubuntu and Raspberry Pi.

---

## Phase 1: Docker Setup

### 1.1 Prerequisites
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### 1.2 Build Docker Image
```bash
cd /home/elibrary/app
docker build -t elibrary:latest .
```

### 1.3 Run with Docker Compose
```bash
# Create .env file
cp .env.production .env

# Edit .env with your settings
nano .env

# Start services
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f web
```

### 1.4 Initial Database Setup
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic --noinput
```

---

## Phase 2: Nginx Configuration

### 2.1 Install Nginx
```bash
sudo apt update
sudo apt install nginx

# Copy nginx configuration
sudo cp nginx.conf /etc/nginx/nginx.conf

# Test configuration
sudo nginx -t

# Enable and start
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 2.2 SSL/TLS Setup
```bash
# Generate self-signed certificate (for testing)
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/key.pem \
  -out /etc/nginx/ssl/cert.pem

# For production, use Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot certonly --standalone -d your-domain.com
# Update nginx.conf with Let's Encrypt paths
```

### 2.3 Verify Nginx
```bash
sudo systemctl status nginx
curl http://localhost
```

---

## Phase 3: Systemd Services Setup

### 3.1 Create Gunicorn Service
```bash
# Copy service file
sudo cp elibrary-gunicorn.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start
sudo systemctl enable elibrary-gunicorn
sudo systemctl start elibrary-gunicorn

# Check status
sudo systemctl status elibrary-gunicorn
```

### 3.2 Create Nginx Service
```bash
# Copy service file
sudo cp elibrary-nginx.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start
sudo systemctl enable elibrary-nginx
sudo systemctl start elibrary-nginx

# Check status
sudo systemctl status elibrary-nginx
```

### 3.3 View Logs
```bash
# Gunicorn logs
sudo journalctl -u elibrary-gunicorn -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Application logs
sudo tail -f /var/log/elibrary/django.log
```

---

## Phase 4: Production Deployment

### 4.1 Ubuntu Server Setup
```bash
# Create application user
sudo useradd -m -s /bin/bash elibrary

# Create application directory
sudo mkdir -p /home/elibrary/app
sudo chown -R elibrary:elibrary /home/elibrary/app

# Create log directory
sudo mkdir -p /var/log/elibrary
sudo chown -R elibrary:www-data /var/log/elibrary
sudo chmod 750 /var/log/elibrary

# Create virtual environment
sudo -u elibrary python3 -m venv /home/elibrary/venv
sudo -u elibrary /home/elibrary/venv/bin/pip install --upgrade pip setuptools wheel
sudo -u elibrary /home/elibrary/venv/bin/pip install -r requirements.txt

# Copy application
sudo cp -r ./* /home/elibrary/app/
sudo chown -R elibrary:elibrary /home/elibrary/app
```

### 4.2 Database Setup
```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql <<EOF
CREATE DATABASE elibrary;
CREATE USER elibrary_user WITH PASSWORD 'secure_password';
ALTER ROLE elibrary_user SET client_encoding TO 'utf8';
ALTER ROLE elibrary_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE elibrary_user SET default_transaction_deferrable TO on;
ALTER ROLE elibrary_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE elibrary TO elibrary_user;
\q
EOF

# Run migrations
cd /home/elibrary/app
sudo -u elibrary /home/elibrary/venv/bin/python manage.py migrate
```

### 4.3 Static Files and Media
```bash
# Create directories
sudo mkdir -p /home/elibrary/app/static
sudo mkdir -p /home/elibrary/app/media
sudo chown -R elibrary:www-data /home/elibrary/app/static
sudo chown -R elibrary:www-data /home/elibrary/app/media

# Collect static files
cd /home/elibrary/app
sudo -u elibrary /home/elibrary/venv/bin/python manage.py collectstatic --noinput
```

### 4.4 Gunicorn Socket Configuration
```bash
# Create socket directory
sudo mkdir -p /run/gunicorn
sudo chown elibrary:www-data /run/gunicorn
sudo chmod 755 /run/gunicorn
```

---

## Phase 5: Raspberry Pi Specific Setup

### 5.1 ARM Compatibility
```bash
# Install ARM-compatible packages
sudo apt install python3-pip python3-venv postgresql postgresql-contrib nginx

# Create virtual environment (slower on RPi)
python3 -m venv ~/elibrary_venv
source ~/elibrary_venv/bin/activate

# Install with precompiled wheels
pip install --only-binary :all: -r requirements.txt
```

### 5.2 Performance Optimization for Raspberry Pi
```bash
# Edit /etc/systemd/system/elibrary-gunicorn.service
# Change:
# ExecStart=/home/elibrary/venv/bin/gunicorn \
#     --workers 2 \          # Reduced from 4
#     --worker-class sync \
#     --bind unix:/run/gunicorn.sock \
#     --max-requests 1000 \  # Recycle workers
#     --timeout 30 \         # Reduced timeout
#     elibrary.wsgi:application
```

### 5.3 Memory Management
```bash
# Add swap (for 512MB RPi)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## Monitoring & Maintenance

### Health Checks
```bash
# Check application
curl https://your-domain.com/health/

# Monitor resources
watch -n 1 'ps aux | grep gunicorn'
top -p $(pgrep -f gunicorn | tr '\n' ',')

# Check database
psql -U elibrary_user -d elibrary -c "SELECT version();"
```

### Backup and Restore
```bash
# Backup database
sudo -u postgres pg_dump elibrary > backup_$(date +%Y%m%d).sql

# Backup media files
tar -czf media_backup_$(date +%Y%m%d).tar.gz /home/elibrary/app/media

# Restore database
psql -U elibrary_user -d elibrary < backup_20260107.sql
```

### Update and Maintenance
```bash
# Update dependencies
cd /home/elibrary/app
/home/elibrary/venv/bin/pip install --upgrade -r requirements.txt

# Restart services
sudo systemctl restart elibrary-gunicorn
sudo systemctl restart elibrary-nginx

# Check logs
sudo journalctl -u elibrary-gunicorn -n 50
```

---

## Troubleshooting

### Common Issues

**Permission Denied Errors**
```bash
sudo chown -R elibrary:www-data /home/elibrary/app
sudo chmod 755 /home/elibrary/app
```

**Port Already in Use**
```bash
sudo lsof -i :8000
sudo lsof -i :80
sudo kill -9 <PID>
```

**Database Connection Issues**
```bash
sudo -u postgres psql -c "\du"
sudo -u postgres psql -c "\l"
pg_isready -h localhost -U elibrary_user
```

**Nginx Not Serving Static Files**
```bash
sudo chown -R www-data:www-data /home/elibrary/app/static
sudo chmod 755 /home/elibrary/app/static
```

---

## Production Checklist

- [ ] Set `DEBUG=False` in production settings
- [ ] Update `ALLOWED_HOSTS` with your domain
- [ ] Generate strong `SECRET_KEY`
- [ ] Set up SSL/TLS certificates
- [ ] Configure database backups
- [ ] Set up monitoring and alerts
- [ ] Configure email for notifications
- [ ] Test disaster recovery procedure
- [ ] Set up log rotation
- [ ] Document admin procedures
- [ ] Create deployment runbook
- [ ] Set up automated updates

---

## Security Hardening

### Firewall Configuration
```bash
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw status
```

### SSL/TLS Best Practices
```bash
# Test SSL configuration
curl -I https://your-domain.com

# Check certificate validity
openssl x509 -in /etc/nginx/ssl/cert.pem -text -noout
```

### Regular Updates
```bash
# Enable automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## Next Steps

1. **Test the deployment** - Verify all services are running
2. **Set up monitoring** - Use tools like Prometheus, Grafana
3. **Configure CI/CD** - Automate deployments with GitHub Actions
4. **Plan scaling** - Load balancing, caching strategies
5. **Document procedures** - Create runbooks for operations

---

**Days 3-4 Complete!** Your application is now production-ready and deployed with proper containerization, reverse proxy, and process management.
