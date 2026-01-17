# Comprehensive Troubleshooting Manual
## TS_OPAC eLibrary System

**Version:** 1.0  
**Date:** January 17, 2026  
**Purpose:** Solutions for common issues, errors, and system failures

---

## Table of Contents
1. [Connection Issues](#connection-issues)
2. [Application Errors](#application-errors)
3. [Database Problems](#database-problems)
4. [Performance Issues](#performance-issues)
5. [Security Problems](#security-problems)
6. [Deployment Errors](#deployment-errors)
7. [Backup & Recovery](#backup--recovery)
8. [API Issues](#api-issues)

---

## Connection Issues

### SSH Connection Refused

**Symptom:** `Connection refused` when SSHing to Raspberry Pi

**Diagnosis:**
```bash
# Check if SSH is running
sudo systemctl status ssh

# Check SSH listening on port 22
sudo netstat -tlnp | grep 22

# Check SSH configuration
sudo nano /etc/ssh/sshd_config | grep -E "^Port|^ListenAddress"
```

**Solutions:**

```bash
# 1. Enable SSH service
sudo systemctl enable ssh
sudo systemctl start ssh

# 2. Check firewall
sudo ufw status
sudo ufw allow 22/tcp

# 3. Verify IP address
hostname -I

# 4. Test from local network
ping raspberrypi.local
ping 192.168.1.100

# 5. Restart SSH
sudo systemctl restart ssh
```

### SSH: Network Unreachable

**Symptom:** `Network is unreachable` error

**Diagnosis:**
```bash
# Check network connectivity
ping 8.8.8.8
ping gateway_ip

# Check Ethernet cable
ethtool eth0

# Check IP configuration
ip addr show
ip route show
```

**Solutions:**

```bash
# 1. Configure static IP
sudo nano /etc/dhcpcd.conf

# Add:
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=8.8.8.8 8.8.4.4

# 2. Restart networking
sudo systemctl restart networking

# 3. Verify connectivity
ping 192.168.1.1
```

### PostgreSQL Connection Failed

**Symptom:** `psql: error: FATAL: Ident authentication failed for user "opac_user"`

**Diagnosis:**
```bash
# Check PostgreSQL service
sudo systemctl status postgresql

# Check listening ports
sudo netstat -tlnp | grep 5432

# Test local connection
sudo -u postgres psql

# Check pg_hba.conf
sudo grep "opac_user" /etc/postgresql/15/main/pg_hba.conf
```

**Solutions:**

```bash
# 1. Fix authentication method
sudo nano /etc/postgresql/15/main/pg_hba.conf

# Change line from:
# TYPE  DATABASE        USER            ADDRESS                 METHOD
# local   opac_db         opac_user                               ident

# To:
# local   opac_db         opac_user                               md5

# 2. Create .pgpass for password-less access
nano ~/.pgpass
# Format: hostname:port:database:username:password
chmod 600 ~/.pgpass

# 3. Restart PostgreSQL
sudo systemctl restart postgresql

# 4. Test connection
psql -h localhost -U opac_user -d opac_db -c "SELECT 1;"
```

### Cannot Reach Remote Database

**Symptom:** `Could not connect to server: Connection timed out`

**Diagnosis:**
```bash
# Check firewall on remote server
sudo ufw status
sudo iptables -L -n | grep 5432

# Test network connectivity
telnet remote_ip 5432
nc -zv remote_ip 5432

# Check PostgreSQL listen address
sudo grep "listen_addresses" /etc/postgresql/15/main/postgresql.conf
```

**Solutions:**

```bash
# 1. Allow port 5432 through firewall
sudo ufw allow 5432/tcp
sudo iptables -A INPUT -p tcp --dport 5432 -j ACCEPT

# 2. Configure PostgreSQL to listen on all interfaces
sudo nano /etc/postgresql/15/main/postgresql.conf
# Change: listen_addresses = '*'

# 3. Add Raspberry Pi to pg_hba.conf
sudo nano /etc/postgresql/15/main/pg_hba.conf
# Add: host    opac_db         opac_user       192.168.1.100/32        md5

# 4. Restart PostgreSQL
sudo systemctl restart postgresql

# 5. Test connection
psql -h remote_ip -U opac_user -d opac_db -c "SELECT 1;"
```

---

## Application Errors

### 502 Bad Gateway

**Symptom:** Browser shows "502 Bad Gateway" error

**Diagnosis:**
```bash
# Check if Gunicorn is running
sudo systemctl status opac-gunicorn.service

# Check Gunicorn socket
ls -la /srv/opac-elibrary/gunicorn.sock

# Check Gunicorn logs
sudo tail -50 /var/log/opac/gunicorn-error.log

# Check Nginx error logs
sudo tail -50 /var/log/nginx/error.log
```

**Solutions:**

```bash
# 1. Restart Gunicorn
sudo systemctl restart opac-gunicorn.service

# 2. Check for permission issues
sudo chown opac:opac /srv/opac-elibrary/gunicorn.sock
sudo chmod 660 /srv/opac-elibrary/gunicorn.sock

# 3. Verify Django app is working
cd /srv/opac-elibrary
source venv/bin/activate
python manage.py check
python manage.py runserver 0.0.0.0:8000  # Test directly

# 4. Check Nginx socket configuration
sudo grep "gunicorn.sock" /etc/nginx/sites-enabled/opac-elibrary

# 5. Verify Nginx configuration
sudo nginx -t

# 6. Restart Nginx
sudo systemctl restart nginx
```

### ImportError: No module named 'django'

**Symptom:** `ImportError: No module named 'django'`

**Diagnosis:**
```bash
# Check if virtual environment is activated
echo $VIRTUAL_ENV

# Check installed packages
pip list | grep -i django

# Check Python path
python -c "import sys; print(sys.path)"
```

**Solutions:**

```bash
# 1. Activate virtual environment
source /srv/opac-elibrary/venv/bin/activate

# 2. Install missing dependencies
pip install -r requirements.txt

# 3. Verify installation
python -c "import django; print(django.VERSION)"

# 4. Check Gunicorn service file
sudo grep "ExecStart" /etc/systemd/system/opac-gunicorn.service
# Should include full path to Python: /srv/opac-elibrary/venv/bin/gunicorn

# 5. Reload systemd
sudo systemctl daemon-reload
sudo systemctl restart opac-gunicorn.service
```

### Static Files Not Loading (404 errors)

**Symptom:** CSS, JavaScript, images return 404

**Diagnosis:**
```bash
# Check if static files collected
ls -la /srv/opac-elibrary/static/

# Check Nginx static file configuration
sudo grep -A5 "location /static/" /etc/nginx/sites-enabled/opac-elibrary

# Check permissions
sudo ls -la /srv/opac-elibrary/static/

# Test direct access
curl http://192.168.1.100/static/css/custom.css -v
```

**Solutions:**

```bash
# 1. Collect static files
cd /srv/opac-elibrary
source venv/bin/activate
python manage.py collectstatic --clear --noinput

# 2. Fix permissions
sudo chown -R opac:opac /srv/opac-elibrary/static/
sudo chmod -R 755 /srv/opac-elibrary/static/

# 3. Verify Nginx configuration
sudo nano /etc/nginx/sites-enabled/opac-elibrary
# Should have: location /static/ { alias /srv/opac-elibrary/static/; }

# 4. Reload Nginx
sudo systemctl reload nginx

# 5. Clear browser cache
# Ctrl+Shift+R to hard refresh
```

### Database Query Timeout

**Symptom:** `Timeout waiting for connection` or query takes too long

**Diagnosis:**
```bash
# Check active connections
psql -h localhost -U opac_user -d opac_db -c "SELECT * FROM pg_stat_activity;"

# Check for long-running queries
psql -h localhost -U opac_user -d opac_db -c "SELECT pid, query_start, query FROM pg_stat_activity WHERE query_start < NOW() - INTERVAL '5 minutes';"

# Check table sizes
psql -h localhost -U opac_user -d opac_db << EOF
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
EOF
```

**Solutions:**

```bash
# 1. Increase Django connection timeout
# In settings.py:
DATABASES = {
    'default': {
        # ... other settings ...
        'CONN_MAX_AGE': 600,  # Connection pooling
        'OPTIONS': {
            'connect_timeout': 30,  # Increase timeout
        }
    }
}

# 2. Optimize queries
python manage.py shell
>>> from django.db import connection
>>> from django.test.utils import CaptureQueriesContext
>>> with CaptureQueriesContext(connection) as context:
...     # Run query
... print([q['sql'] for q in context])

# 3. Create missing indexes
psql -h localhost -U opac_user -d opac_db << EOF
CREATE INDEX idx_item_status ON catalog_item(status);
CREATE INDEX idx_loan_user_date ON circulation_loan(user_id, checkout_date);
EOF

# 4. Analyze tables
psql -h localhost -U opac_user -d opac_db -c "ANALYZE;"

# 5. Restart PostgreSQL
sudo systemctl restart postgresql
```

---

## Database Problems

### "Disk space is too low"

**Symptom:** Database operations fail, disk full error

**Diagnosis:**
```bash
# Check disk space
df -h

# Check PostgreSQL data directory
sudo du -sh /var/lib/postgresql/

# Check individual table sizes
psql -h localhost -U opac_user -d opac_db << EOF
SELECT schemaname, tablename, pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size
FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_relation_size(schemaname||'.'||tablename) DESC LIMIT 10;
EOF
```

**Solutions:**

```bash
# 1. Identify large files
sudo find /var/lib/postgresql -type f -size +1G -exec ls -lh {} \;

# 2. Clean old WAL files
sudo su - postgres -c 'cd /var/lib/postgresql/15/main/pg_wal && ls -la | tail -20'
# Safely remove old WAL: psql -c "SELECT pg_wal_lsn_diff(pg_current_wal_lsn(), '0/0')"

# 3. Vacuum database
psql -h localhost -U opac_user -d opac_db -c "VACUUM FULL ANALYZE;"

# 4. Backup and archive old data
psql -h localhost -U opac_user -d opac_db << EOF
-- Archive old loans
INSERT INTO circulation_loan_archive
SELECT * FROM circulation_loan WHERE return_date < NOW() - INTERVAL '2 years';
DELETE FROM circulation_loan WHERE return_date < NOW() - INTERVAL '2 years';
EOF

# 5. Add more disk space (if possible)
# Expand SD card or add external storage
```

### Database Corruption

**Symptom:** `ERROR: index ... is unusable` or data integrity errors

**Diagnosis:**
```bash
# Check index integrity
psql -h localhost -U opac_user -d opac_db -c "REINDEX DATABASE opac_db;"

# Check for corruption
psql -h localhost -U opac_user -d opac_db -c "SELECT pg_catalog.pg_identify_object(classid, objid, objsubid) AS obj FROM pg_catalog.pg_class WHERE relname LIKE '%invalid%';"
```

**Solutions:**

```bash
# 1. Rebuild indexes
psql -h localhost -U opac_user -d opac_db << EOF
REINDEX INDEX idx_item_status;
REINDEX INDEX idx_publication_title;
-- Or full reindex:
REINDEX DATABASE opac_db;
EOF

# 2. Restore from backup
psql -h localhost -U opac_user -d opac_db < /backups/opac_db_backup.sql

# 3. Check file system
sudo fsck -n /dev/sda1  # Check without repairs
sudo fsck -y /dev/sda1  # Check and repair
```

---

## Performance Issues

### High CPU Usage

**Symptom:** CPU at 90%+ even with few users

**Diagnosis:**
```bash
# Real-time CPU monitoring
top -b -n 1 | head -15

# Check which process uses CPU
ps aux --sort=-%cpu | head -10

# Check Django for runaway processes
sudo systemctl status opac-gunicorn.service

# Check PostgreSQL
ps aux | grep postgres
```

**Solutions:**

```bash
# 1. Find expensive queries
psql -h localhost -U opac_user -d opac_db << EOF
SELECT query, calls, total_time, mean_time FROM pg_stat_statements
WHERE mean_time > 1000 ORDER BY total_time DESC LIMIT 10;
EOF

# 2. Add indexes for slow queries
CREATE INDEX idx_new_index ON table_name(column);

# 3. Limit worker processes
# In /etc/systemd/system/opac-gunicorn.service:
# Change: --workers 4  (reduce from default)

# 4. Increase swap
sudo nano /etc/dphys-swapfile
# CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# 5. Restart services
sudo systemctl daemon-reload
sudo systemctl restart opac-gunicorn.service
```

### High Memory Usage

**Symptom:** Memory at 90%+, system becomes sluggish

**Diagnosis:**
```bash
# Check memory usage
free -h

# Check per-process memory
ps aux --sort=-%mem | head -10

# Check cache vs used memory
cat /proc/meminfo | grep -E "MemTotal|MemAvailable|Cached|Buffers"
```

**Solutions:**

```bash
# 1. Reduce worker processes
# In Gunicorn config: --workers 2 (instead of 4)

# 2. Clear caches
sudo systemctl restart opac-gunicorn.service  # Clears Python cache

# 3. Increase swap
sudo nano /etc/dphys-swapfile
# CONF_SWAPSIZE=2048

# 4. Optimize Django settings
# In settings.py:
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
        'TIMEOUT': 3600,  # 1 hour
        'OPTIONS': {
            'MAX_POOL_SIZE': 10,  # Limit memory
        }
    }
}

# 5. Monitor memory growth
watch -n 5 'free -h'
```

### Slow Page Load Times

**Symptom:** Pages load in 5+ seconds

**Diagnosis:**
```bash
# Check Nginx response time
sudo tail -20 /var/log/nginx/access.log | grep -oP 'upstream_response_time \K[0-9.]+'

# Measure request latency
curl -w "Total: %{time_total}s\n" -o /dev/null -s http://raspberrypi.local/

# Check database query time
python manage.py shell
>>> from django.db import reset_queries, connection
>>> reset_queries()
>>> # Run your query
>>> print(len(connection.queries), 'queries took', sum(float(q['time']) for q in connection.queries), 'seconds')
```

**Solutions:**

```bash
# 1. Enable caching
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# 2. Optimize database queries
# Use select_related() for foreign keys
Publication.objects.select_related('publication_type', 'publisher').all()

# Use prefetch_related() for reverse relationships
Publication.objects.prefetch_related('authors', 'subjects').all()

# 3. Add database indexes
CREATE INDEX idx_pub_type_date ON catalog_publication(publication_type_id, date_added DESC);

# 4. Minify static assets
python manage.py collectstatic --compress --clear --noinput

# 5. Enable gzip compression
# In Nginx config:
gzip on;
gzip_types text/plain text/css text/javascript application/json application/javascript;
gzip_comp_level 6;
```

---

## Security Problems

### SSL Certificate Expired

**Symptom:** Browser warning "Certificate is not valid" or "HTTPS connection not secure"

**Diagnosis:**
```bash
# Check certificate expiry
openssl x509 -in /path/to/certificate.pem -noout -dates

# Check certificate details
sudo openssl x509 -in /etc/ssl/certs/opac-cert.pem -noout -text
```

**Solutions:**

```bash
# 1. Generate new self-signed certificate (development)
sudo openssl req -new -x509 -days 365 -nodes \
  -out /etc/ssl/certs/opac-cert.pem \
  -keyout /etc/ssl/private/opac-key.pem

# 2. For production, use Let's Encrypt (free)
sudo apt install -y certbot python3-certbot-nginx
sudo certbot certonly --nginx -d yourdomain.com
# Auto-renew: sudo certbot renew --dry-run

# 3. Update Nginx configuration
sudo nano /etc/nginx/sites-enabled/opac-elibrary
# ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
# ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

# 4. Restart Nginx
sudo systemctl restart nginx
```

### Authentication Not Working

**Symptom:** Login always fails, even with correct credentials

**Diagnosis:**
```bash
# Check auth logs
tail -20 /var/log/auth.log

# Test login manually
python manage.py shell
>>> from django.contrib.auth import authenticate
>>> user = authenticate(username='testuser', password='testpass')
>>> print(user)

# Check user status
>>> from django.contrib.auth.models import User
>>> User.objects.filter(username='testuser').values('is_active', 'is_staff')
```

**Solutions:**

```bash
# 1. Verify SECRET_KEY is set
# In settings.py or .env:
echo $SECRET_KEY  # Should not be empty

# 2. Check session backend
INSTALLED_APPS should include 'django.contrib.sessions'
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# 3. Reset user password
python manage.py shell
>>> from django.contrib.auth.models import User
>>> user = User.objects.get(username='testuser')
>>> user.set_password('newpassword')
>>> user.save()

# 4. Verify CORS settings
ALLOWED_HOSTS = ['*']  # Or specific domains
CSRF_TRUSTED_ORIGINS = ['http://localhost', 'http://raspberrypi.local']

# 5. Clear session cache
python manage.py clearsessions
```

### SQL Injection Vulnerability

**Symptom:** Unexpected database modifications, data leak

**Diagnosis:**
```bash
# Check for raw SQL queries
grep -r "raw(" /srv/opac-elibrary --include="*.py"
grep -r ".extra(" /srv/opac-elibrary --include="*.py"

# Audit recent database changes
psql -h localhost -U opac_user -d opac_db << EOF
SELECT * FROM pg_catalog.pg_stat_user_tables
ORDER BY n_tup_del DESC, n_tup_upd DESC LIMIT 10;
EOF

# Check database logs
sudo tail -100 /var/log/postgresql/postgresql.log | grep -i "delete\|update\|drop"
```

**Solutions:**

```bash
# 1. Use parameterized queries (Django ORM)
# WRONG: Publication.objects.raw(f"SELECT * FROM catalog_publication WHERE title = '{title}'")
# RIGHT: Publication.objects.filter(title=title)

# 2. Use prepared statements
from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT * FROM catalog_publication WHERE title = %s", [title])

# 3. Escape user input
from django.utils.html import escape
safe_input = escape(user_input)

# 4. Use Django validators
from django import forms
class SearchForm(forms.Form):
    query = forms.CharField(max_length=200)  # Limits input

# 5. Restrict database user privileges
# In PostgreSQL:
GRANT SELECT, INSERT, UPDATE ON catalog_publication TO opac_user;
REVOKE DELETE ON catalog_publication FROM opac_user;
```

---

## Deployment Errors

### Permission Denied During Deployment

**Symptom:** `Permission denied` when accessing files or directories

**Diagnosis:**
```bash
# Check file ownership
ls -la /srv/opac-elibrary/

# Check user permissions
id opac

# Check directory permissions
stat /srv/opac-elibrary/
```

**Solutions:**

```bash
# 1. Fix ownership
sudo chown -R opac:opac /srv/opac-elibrary/

# 2. Fix permissions
sudo chmod -R 755 /srv/opac-elibrary/
sudo chmod -R 644 /srv/opac-elibrary/*.py

# 3. Fix log directory
sudo mkdir -p /var/log/opac
sudo chown opac:opac /var/log/opac
sudo chmod 755 /var/log/opac

# 4. Fix socket directory
sudo chmod 755 /srv/opac-elibrary/
sudo chown opac:opac /srv/opac-elibrary/gunicorn.sock
```

### Port Already in Use

**Symptom:** `Address already in use` when starting service

**Diagnosis:**
```bash
# Check which process is using port 80
sudo lsof -i :80
sudo netstat -tlnp | grep :80

# Check which process is using port 5432
sudo lsof -i :5432
sudo netstat -tlnp | grep :5432
```

**Solutions:**

```bash
# 1. Kill the process
sudo kill -9 <PID>

# 2. Or change port in configuration
# For Nginx: listen 8080 instead of 80
# For Gunicorn: --bind 0.0.0.0:8001

# 3. Check if service is already running
sudo systemctl status opac-gunicorn.service
sudo systemctl status nginx.service

# 4. Restart services properly
sudo systemctl stop nginx opac-gunicorn.service
sleep 2
sudo systemctl start nginx opac-gunicorn.service
```

---

## Backup & Recovery

### Backup Failed

**Symptom:** Backup script returned error, no backup file created

**Diagnosis:**
```bash
# Check backup script
cat ~/bin/backup_full.sh

# Check backup logs
tail -50 /var/log/opac/backup.log

# Test backup manually
pg_dump -U opac_user -d opac_db -v 2>&1 | head -50
```

**Solutions:**

```bash
# 1. Verify database connectivity
psql -h localhost -U opac_user -d opac_db -c "SELECT 1;"

# 2. Check disk space
df -h

# 3. Verify backup directory
ls -la /srv/opac-elibrary/backups/
chmod 755 /srv/opac-elibrary/backups/

# 4. Run manual backup
pg_dump -U opac_user -d opac_db | gzip > /srv/opac-elibrary/backups/manual_backup.sql.gz

# 5. Schedule backup with cron
crontab -e
# 0 2 * * * /srv/opac-elibrary/scripts/backup_full.sh >> /var/log/opac/backup.log 2>&1
```

### Restore Failed

**Symptom:** Restore command hangs or returns error

**Diagnosis:**
```bash
# Check backup file integrity
file /backups/opac_db_backup.sql.gz
gunzip -t /backups/opac_db_backup.sql.gz  # Test compression

# Check database space
psql -U opac_user -d opac_db -c "SELECT pg_database_size('opac_db');"
```

**Solutions:**

```bash
# 1. Drop and recreate database
psql -U postgres << EOF
DROP DATABASE opac_db;
CREATE DATABASE opac_db OWNER opac_user;
EOF

# 2. Restore from backup
gunzip -c /backups/opac_db_backup.sql.gz | psql -U opac_user -d opac_db

# 3. If restore hangs, restore in smaller steps
# Extract to SQL first:
gunzip -c /backups/opac_db_backup.sql.gz > /tmp/backup.sql

# Restore specific tables
psql -U opac_user -d opac_db < /tmp/backup.sql

# 4. Verify restore
psql -U opac_user -d opac_db -c "SELECT COUNT(*) FROM catalog_publication;"
```

---

## API Issues

### API Returns 401 Unauthorized

**Symptom:** All API requests return 401 even with valid token

**Diagnosis:**
```bash
# Check token in database
psql -h localhost -U opac_user -d opac_db -c "SELECT * FROM authtoken_token LIMIT 5;"

# Test API request with token
curl -H "Authorization: Token YOUR_TOKEN" http://raspberrypi.local/api/v1/

# Check API authentication settings
grep -r "Authentication" /srv/opac-elibrary/elibrary/ --include="*.py"
```

**Solutions:**

```bash
# 1. Generate valid token
python manage.py shell
>>> from rest_framework.authtoken.models import Token
>>> from django.contrib.auth.models import User
>>> user = User.objects.get(username='testuser')
>>> token, created = Token.objects.get_or_create(user=user)
>>> print(token.key)

# 2. Verify token format
# Should be: Authorization: Token abc123def456...

# 3. Check API settings
# In settings.py:
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
}

# 4. Refresh token
>>> token.delete()
>>> token = Token.objects.create(user=user)
>>> print(token.key)
```

### API Returns 403 Forbidden

**Symptom:** Valid token but access denied to resource

**Diagnosis:**
```bash
# Check user permissions
python manage.py shell
>>> user = User.objects.get(username='testuser')
>>> user.user_permissions.all()
>>> user.groups.all()

# Check object-level permissions
# In Django admin: Users > testuser > Permissions
```

**Solutions:**

```bash
# 1. Grant permissions
python manage.py shell
>>> from django.contrib.auth.models import Permission, Group
>>> from django.contrib.contenttypes.models import ContentType
>>> user = User.objects.get(username='testuser')
>>> # Grant specific permission
>>> perm = Permission.objects.get(codename='add_publication')
>>> user.user_permissions.add(perm)
>>> user.save()

# 2. Or add to group with permissions
>>> group = Group.objects.get(name='Librarians')
>>> user.groups.add(group)
>>> user.save()

# 3. Check API permission classes
# In settings.py:
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
        'api.permissions.IsLibrarianOrReadOnly',  # Custom
    ],
}
```

---

## Emergency Commands

### Quick Service Restart

```bash
# Restart all services
sudo systemctl restart opac-gunicorn.service nginx postgresql

# Or individually
sudo systemctl restart opac-gunicorn.service
sudo systemctl restart nginx
sudo systemctl restart postgresql
```

### System Status Check

```bash
#!/bin/bash
echo "=== System Status ==="
echo "Disk:"
df -h | grep -E '^/dev|^Filesystem'
echo -e "\nMemory:"
free -h
echo -e "\nServices:"
systemctl status opac-gunicorn.service nginx postgresql --no-pager | grep "Active:"
echo -e "\nDatabase:"
psql -h localhost -U opac_user -d opac_db -c "SELECT COUNT(*) FROM catalog_publication;"
echo -e "\nWeb Server:"
curl -s -I http://localhost/ | head -1
```

### Clear All Caches

```bash
# Django cache
python manage.py flush_cache

# Redis cache
redis-cli FLUSHALL

# Browser cache
# In settings.py: SESSION_COOKIE_AGE = 1
python manage.py clearsessions
```

---

## Getting Help

1. **Check Logs First:**
   - Django: `/var/log/opac/gunicorn-error.log`
   - Nginx: `/var/log/nginx/error.log`
   - PostgreSQL: `/var/log/postgresql/postgresql.log`

2. **Gather System Information:**
   ```bash
   uname -a
   python --version
   psql --version
   systemctl --version
   ```

3. **Test Components:**
   ```bash
   python manage.py check
   psql -h localhost -U opac_user -d opac_db -c "SELECT 1;"
   curl -I http://localhost/
   ```

4. **Contact Support:**
   - Include error message and logs
   - Provide system information
   - List recent changes made
   - Include diagnostic output from commands above

---

**Last Updated:** January 17, 2026  
**Version:** 1.0  
**Status:** Production Ready

For additional support, refer to:
- Django Documentation: https://docs.djangoproject.com/
- PostgreSQL Documentation: https://www.postgresql.org/docs/
- Nginx Documentation: https://nginx.org/en/docs/
- Raspberry Pi Documentation: https://www.raspberrypi.com/documentation/
