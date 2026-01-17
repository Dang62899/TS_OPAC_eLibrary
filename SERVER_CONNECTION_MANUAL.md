# Server Connection & Remote Deployment Manual
## TS_OPAC eLibrary System

**Version:** 1.0  
**Date:** January 17, 2026  
**Purpose:** Guide for connecting Raspberry Pi to remote PostgreSQL server and cloud deployment

---

## Table of Contents
1. [Network Architecture](#network-architecture)
2. [SSH Configuration](#ssh-configuration)
3. [Remote Database Connection](#remote-database-connection)
4. [VPN Setup (Optional)](#vpn-setup-optional)
5. [Cloud Deployment](#cloud-deployment)
6. [Remote Monitoring](#remote-monitoring)
7. [Failover & Disaster Recovery](#failover--disaster-recovery)

---

## Network Architecture

### Recommended Setup

```
┌─────────────────────────────────────────────────────────┐
│                    INTERNET                             │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
    ┌───┴────┐               ┌───────┴──────┐
    │  ISP   │               │  Cloud/VPS   │
    │ Router │               │   Provider   │
    └───┬────┘               └───────┬──────┘
        │                           │
        │                    [PostgreSQL DB]
        │                    [Backups Server]
        │                    [DNS Records]
        │
   ┌────┴────────────────────────┐
   │   Local Network             │
   │   (192.168.1.0/24)          │
   │                             │
   │  ┌──────────────────────┐   │
   │  │  Raspberry Pi        │   │
   │  │  (192.168.1.100)     │   │
   │  │                      │   │
   │  │ ▪ Nginx             │   │
   │  │ ▪ Gunicorn          │   │
   │  │ ▪ Django App        │   │
   │  │ ▪ Local Cache       │   │
   │  └──────────────────────┘   │
   │                             │
   └─────────────────────────────┘
```

---

## SSH Configuration

### 1. SSH Key Setup (Secure Authentication)

```bash
# On Raspberry Pi, generate SSH key pair
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""

# Alternative: Ed25519 (recommended)
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""

# Display public key
cat ~/.ssh/id_rsa.pub

# On remote PostgreSQL server, add to authorized_keys
ssh-copy-id -i ~/.ssh/id_rsa.pub db_user@postgres_server_ip

# Or manually:
# 1. SSH to PostgreSQL server
ssh db_user@postgres_server_ip
# 2. Add Raspberry Pi's public key:
echo "SSH_PUBLIC_KEY_FROM_PI" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### 2. SSH Config File

```bash
# Create SSH config for easy access
nano ~/.ssh/config
```

```
# PostgreSQL Server
Host postgres-prod
    HostName 192.168.1.50
    User opac_user
    IdentityFile ~/.ssh/id_rsa
    Port 22
    StrictHostKeyChecking accept-new
    UserKnownHostsFile ~/.ssh/known_hosts

# Cloud Database Server
Host cloud-db
    HostName db.opac-elib.cloud
    User postgres
    IdentityFile ~/.ssh/cloud_key
    Port 22
    ProxyCommand ssh -W %h:%p bastion_host (if behind firewall)

# Backup Server
Host backup-server
    HostName backup.opac-elib.local
    User backup_user
    IdentityFile ~/.ssh/id_rsa
    Port 22
```

```bash
# Test SSH connection
ssh postgres-prod
ssh cloud-db

# Set proper permissions
chmod 600 ~/.ssh/config
chmod 700 ~/.ssh
```

### 3. SSH Tunneling for Database Access

```bash
# Method 1: Local port forwarding
# Access remote database through local port 5433
ssh -L 5433:localhost:5432 postgres-prod -N

# Connect to forwarded database
psql -h localhost -p 5433 -U opac_user -d opac_db

# Method 2: Create persistent SSH tunnel
# Create script: ~/bin/create_tunnel.sh
#!/bin/bash
ssh -N -L 5433:localhost:5432 postgres-prod &
sleep 2
echo "SSH Tunnel established on port 5433"

# Make executable
chmod +x ~/bin/create_tunnel.sh
```

### 4. SSH Security Hardening

```bash
# On Raspberry Pi
nano ~/.ssh/config

# Add to all hosts:
AddKeysToAgent yes
IdentitiesOnly yes
```

```bash
# Disable password authentication (use keys only)
# On PostgreSQL server:
sudo nano /etc/ssh/sshd_config

# Modify:
PasswordAuthentication no
PubkeyAuthentication yes
X11Forwarding no
PermitRootLogin no
Port 22

# Restart SSH
sudo systemctl restart ssh
```

---

## Remote Database Connection

### 1. PostgreSQL Remote Access Setup

```bash
# On PostgreSQL server, edit postgresql.conf
sudo nano /etc/postgresql/15/main/postgresql.conf

# Find and modify:
listen_addresses = '*'  # or specific IP: '192.168.1.50'
```

```bash
# Configure PostgreSQL authentication (pg_hba.conf)
sudo nano /etc/postgresql/15/main/pg_hba.conf

# Add before existing entries:
# TYPE  DATABASE        USER            ADDRESS                 METHOD
host    opac_db         opac_user       192.168.1.100/32        md5
host    opac_db         opac_user       192.168.1.0/24          md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### 2. Database User & Roles

```bash
# Create database user on PostgreSQL server
sudo -u postgres psql

postgres=# CREATE USER opac_user WITH PASSWORD 'secure_password';
postgres=# CREATE DATABASE opac_db OWNER opac_user;
postgres=# GRANT ALL PRIVILEGES ON DATABASE opac_db TO opac_user;
postgres=# \q
```

### 3. Test Remote Connection from Raspberry Pi

```bash
# Install PostgreSQL client
sudo apt install -y postgresql-client

# Test connection
psql -h 192.168.1.50 -U opac_user -d opac_db -c "SELECT version();"

# If successful, create .pgpass for password-less access
nano ~/.pgpass

# Format: hostname:port:database:username:password
192.168.1.50:5432:opac_db:opac_user:secure_password

chmod 600 ~/.pgpass

# Test again (should not prompt for password)
psql -h 192.168.1.50 -U opac_user -d opac_db -c "SELECT 1;"
```

### 4. Django Database Configuration

```bash
# Update Django settings.py
nano /srv/opac-elibrary/elibrary/settings.py

# Or use environment variables
nano /srv/opac-elibrary/.env
```

```python
# settings.py approach
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'opac_db',
        'USER': 'opac_user',
        'PASSWORD': 'secure_password',
        'HOST': '192.168.1.50',
        'PORT': '5432',
        'CONN_MAX_AGE': 600,
    }
}
```

```bash
# Or .env approach (recommended)
DATABASE_URL=postgresql://opac_user:secure_password@192.168.1.50:5432/opac_db
```

### 5. Verify Connection in Django

```bash
cd /srv/opac-elibrary
source venv/bin/activate

# Test database connection
python manage.py dbshell

# Should show psql prompt, type: \q to exit

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

---

## VPN Setup (Optional)

### For Secure Remote Access

### 1. WireGuard VPN Configuration

```bash
# On Raspberry Pi
sudo apt install -y wireguard wireguard-tools

# Generate keys
wg genkey | tee privatekey | wg pubkey > publickey

# View keys
cat privatekey
cat publickey
```

```bash
# Create WireGuard configuration
sudo nano /etc/wireguard/wg0.conf
```

```
[Interface]
Address = 10.0.0.1/24
SaveMconfig = false
ListenPort = 51820
PrivateKey = RASPBERRY_PI_PRIVATE_KEY

# PostgreSQL Server Peer
[Peer]
PublicKey = POSTGRES_SERVER_PUBLIC_KEY
AllowedIPs = 192.168.1.50/32
Endpoint = postgres_server_ip:51820
PersistentKeepalive = 25
```

```bash
# Start WireGuard
sudo systemctl enable wg-quick@wg0.service
sudo systemctl start wg-quick@wg0.service

# Check status
sudo wg show
```

### 2. Firewall Configuration

```bash
# Allow VPN port
sudo ufw allow 51820/udp

# Forward VPN traffic
sudo sysctl -w net.ipv4.ip_forward=1
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
```

---

## Cloud Deployment

### AWS/Azure Deployment Example

### 1. Database Migration to Cloud

```bash
# Backup local database
pg_dump -h 192.168.1.50 -U opac_user opac_db > opac_db_backup.sql

# Create database on cloud provider
# AWS RDS: Use AWS Console or:
aws rds create-db-instance \
  --db-instance-identifier opac-prod-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-user-account-name opac_user \
  --allocated-storage 20

# Restore to cloud database
psql -h cloud-db-endpoint.rds.amazonaws.com \
  -U opac_user -d opac_db < opac_db_backup.sql
```

### 2. Update Django Configuration

```bash
# Update .env for cloud database
nano /srv/opac-elibrary/.env

# Change:
DATABASE_URL=postgresql://opac_user:password@cloud-db-endpoint.rds.amazonaws.com:5432/opac_db

# Restart application
sudo systemctl restart opac-gunicorn.service
```

### 3. Docker Deployment (Alternative)

```bash
# Create Dockerfile
nano Dockerfile
```

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "elibrary.wsgi:application"]
```

```bash
# Build image
docker build -t opac-elibrary:1.0 .

# Push to registry
docker tag opac-elibrary:1.0 your-registry/opac-elibrary:1.0
docker push your-registry/opac-elibrary:1.0

# Deploy to Kubernetes or container service
kubectl apply -f k8s-deployment.yaml
```

---

## Remote Monitoring

### 1. SSH-Based Monitoring

```bash
# Monitor Raspberry Pi resources remotely
ssh pi-prod "free -h && df -h && top -b -n 1 | head -15"

# Monitor database connections
ssh postgres-prod "psql -U opac_user -d opac_db -c 'SELECT * FROM pg_stat_activity;'"

# Check application logs
ssh pi-prod "tail -20 /var/log/opac/gunicorn-error.log"
```

### 2. Monitoring Script

```bash
# Create monitoring script: ~/bin/monitor.sh
#!/bin/bash

echo "=== System Status ==="
ssh pi-prod "uname -a && uptime"

echo -e "\n=== Disk Usage ==="
ssh pi-prod "df -h | grep -E '^/dev|^Filesystem'"

echo -e "\n=== Memory Usage ==="
ssh pi-prod "free -h"

echo -e "\n=== Database Connections ==="
ssh postgres-prod "psql -U opac_user -d opac_db -c 'SELECT count(*) FROM pg_stat_activity;'"

echo -e "\n=== Application Status ==="
ssh pi-prod "sudo systemctl status opac-gunicorn.service --no-pager | head -10"

echo -e "\n=== Recent Errors ==="
ssh pi-prod "tail -5 /var/log/opac/gunicorn-error.log"
```

```bash
# Make executable
chmod +x ~/bin/monitor.sh

# Schedule daily monitoring
crontab -e
# Add: 0 10 * * * ~/bin/monitor.sh > ~/logs/monitoring.log 2>&1
```

### 3. Health Check Endpoint

```python
# Add to Django urls.py
path('health/', views.health_check, name='health_check'),

# In views.py
def health_check(request):
    from django.db import connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=500)
```

```bash
# Monitor health endpoint
watch -n 60 "curl -s http://raspberrypi.local/health/ | jq ."
```

---

## Failover & Disaster Recovery

### 1. Automated Failover Script

```bash
# Create failover script: ~/bin/failover.sh
#!/bin/bash

PRIMARY_DB="192.168.1.50"
SECONDARY_DB="backup.opac-elib.local"
DB_NAME="opac_db"
DB_USER="opac_user"

# Test primary connection
if ! psql -h $PRIMARY_DB -U $DB_USER -d $DB_NAME -c "SELECT 1" 2>/dev/null; then
    echo "Primary database offline, switching to secondary..."
    
    # Update connection string
    sed -i "s/HOST=.*/HOST=$SECONDARY_DB/" /srv/opac-elibrary/.env
    
    # Restart application
    sudo systemctl restart opac-gunicorn.service
    
    # Notify administrator
    echo "Failover complete at $(date)" | mail -s "Database Failover Alert" admin@example.com
else
    echo "Primary database is operational"
fi
```

```bash
# Schedule to run every 5 minutes
crontab -e
# Add: */5 * * * * ~/bin/failover.sh >> ~/logs/failover.log 2>&1
```

### 2. Backup & Restore Procedures

```bash
# Full backup script: ~/bin/backup_full.sh
#!/bin/bash

BACKUP_DIR="/srv/opac-elibrary/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
pg_dump -h 192.168.1.50 -U opac_user opac_db | \
  gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Application backup
tar -czf $BACKUP_DIR/app_$DATE.tar.gz \
  --exclude='venv' --exclude='.git' --exclude='__pycache__' \
  /srv/opac-elibrary

# Encrypt backups
gpg --symmetric --cipher-algo AES256 $BACKUP_DIR/db_$DATE.sql.gz
gpg --symmetric --cipher-algo AES256 $BACKUP_DIR/app_$DATE.tar.gz

# Upload to remote server
scp $BACKUP_DIR/db_$DATE.sql.gz.gpg backup-server:/backups/
scp $BACKUP_DIR/app_$DATE.tar.gz.gpg backup-server:/backups/

# Cleanup old backups (keep 14 days)
find $BACKUP_DIR -name "*.gz.gpg" -mtime +14 -delete

echo "Backup completed: $DATE"
```

```bash
# Restore procedure
#!/bin/bash

BACKUP_FILE="db_20260117_100000.sql.gz"
BACKUP_DIR="/srv/opac-elibrary/backups"

# Decrypt
gpg --output $BACKUP_DIR/$BACKUP_FILE $BACKUP_DIR/$BACKUP_FILE.gpg

# Restore database
gunzip -c $BACKUP_DIR/$BACKUP_FILE | \
  psql -h 192.168.1.50 -U opac_user opac_db

echo "Restore completed from $BACKUP_FILE"
```

### 3. Disaster Recovery Plan

```
DISASTER RECOVERY CHECKLIST:

[ ] Identify Issue
    - Database offline
    - Application crashed
    - Disk full
    - Network unreachable

[ ] Immediate Actions
    - Switch to failover system if applicable
    - Notify team/users
    - Enable logging for diagnosis

[ ] Recovery Steps
    - Check recent backups
    - Restore from last good state
    - Verify data integrity
    - Test all critical functions

[ ] Post-Recovery
    - Document incident
    - Update monitoring
    - Review logs
    - Communicate status to users

[ ] Prevention
    - Implement monitoring
    - Increase backup frequency
    - Test restore procedures regularly
    - Update disaster recovery plan
```

---

## Security Considerations

### SSH Key Management
- Rotate keys every 6 months
- Never share private keys
- Use different keys for different environments
- Implement key escrow for critical keys

### Network Security
- Use VPN for remote connections
- Implement firewall rules
- Monitor for suspicious connections
- Use intrusion detection systems

### Data Protection
- Encrypt data in transit (TLS/SSL)
- Encrypt data at rest
- Use strong passwords for database users
- Implement role-based access control

---

## Troubleshooting

```bash
# SSH connection issues
ssh -v postgres-prod  # Verbose mode for debugging

# Database connection timeout
# Check firewall: sudo iptables -L -n
# Test port: telnet 192.168.1.50 5432

# Django connection errors
python manage.py dbshell  # Test directly

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql.log
```

---

**Last Updated:** January 17, 2026  
**For Issues:** Refer to TROUBLESHOOTING.md or contact system administrator.
