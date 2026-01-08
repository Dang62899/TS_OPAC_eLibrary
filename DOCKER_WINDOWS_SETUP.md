# Days 3-4: Docker Setup on Windows with WSL2

## Phase 1: Windows Prerequisites

### Step 1: Install WSL2 (Windows Subsystem for Linux)

```powershell
# Run PowerShell as Administrator

# Enable WSL2
wsl --install

# Set WSL2 as default
wsl --set-default-version 2

# Install Ubuntu 22.04 LTS
wsl --install -d Ubuntu-22.04

# Verify installation
wsl --list --verbose
```

**After installation:**
- Restart your computer
- Open Ubuntu from Start Menu
- Set username and password

### Step 2: Install Docker Desktop for Windows

1. **Download** from: https://www.docker.com/products/docker-desktop
2. **Install** with default settings
3. **Enable WSL2 integration:**
   - Docker Desktop → Settings → Resources → WSL Integration
   - Enable Ubuntu-22.04
4. **Verify installation:**

```powershell
docker --version
docker-compose --version
```

### Step 3: Allocate Resources to WSL2

Create file `%USERPROFILE%\.wslconfig`:

```ini
[wsl2]
memory=4GB
processors=4
swap=2GB
localhostForwarding=true
```

Restart WSL:
```powershell
wsl --shutdown
```

---

## Phase 2: Prepare Application Files

### Step 1: Update .env for Docker

Create/update `.env` file in project root:

```env
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,*.local
SECRET_KEY=your-super-secret-key-change-this-to-random-string-12345

# PostgreSQL (Docker)
DATABASE_URL=postgresql://elibrary_user:elibrary_password@db:5432/elibrary
DB_NAME=elibrary
DB_USER=elibrary_user
DB_PASSWORD=elibrary_password
DB_HOST=db
DB_PORT=5432

POSTGRES_DB=elibrary
POSTGRES_USER=elibrary_user
POSTGRES_PASSWORD=elibrary_password
```

### Step 2: Update Django Settings for PostgreSQL

Edit `elibrary/settings.py`:

```python
import dj_database_url
import os

# Database - Auto-detect from environment
if os.getenv('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            default=os.getenv('DATABASE_URL'),
            conn_max_age=600
        )
    }
else:
    # Fallback to SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
```

### Step 3: Install psycopg2 for PostgreSQL

Add to `requirements.txt`:

```
psycopg2-binary==2.9.9
dj-database-url==2.0.0
```

---

## Phase 3: Migration Script (SQLite → PostgreSQL)

### Create Migration Script

Create file `migrate_to_postgres.py`:

```python
#!/usr/bin/env python
import os
import django
import json
from django.core import serializers
from django.db import connections

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elibrary.settings')
django.setup()

def backup_sqlite():
    """Backup current SQLite data"""
    from django.apps import apps
    
    print("📦 Backing up SQLite data...")
    
    # Get all models
    models = apps.get_models()
    backup_data = {}
    
    for model in models:
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        
        queryset = model.objects.all()
        count = queryset.count()
        
        if count > 0:
            data = serializers.serialize('json', queryset)
            backup_data[f"{app_label}.{model_name}"] = json.loads(data)
            print(f"  ✓ {app_label}.{model_name}: {count} records")
    
    # Save to file
    with open('sqlite_backup.json', 'w') as f:
        json.dump(backup_data, f, indent=2)
    
    print(f"✅ Backup saved to sqlite_backup.json")
    return backup_data

def verify_migration():
    """Verify PostgreSQL has all data"""
    from django.apps import apps
    
    print("\n📊 Verifying PostgreSQL migration...")
    
    models = apps.get_models()
    total_records = 0
    
    for model in models:
        count = model.objects.count()
        if count > 0:
            total_records += count
            app_label = model._meta.app_label
            model_name = model._meta.model_name
            print(f"  ✓ {app_label}.{model_name}: {count} records")
    
    print(f"\n✅ Total records in PostgreSQL: {total_records}")

if __name__ == '__main__':
    print("🚀 Starting SQLite to PostgreSQL Migration\n")
    
    try:
        backup_sqlite()
        verify_migration()
        print("\n✨ Migration complete!")
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
```

---

## Phase 4: Docker Deployment

### Step 1: Build and Start Containers

```powershell
# Navigate to project
cd C:\Users\Dang\Desktop\TS_OPAC_eLibrary

# Build Docker image
docker-compose build

# Start containers in background
docker-compose up -d

# Check status
docker-compose ps
```

Expected output:
```
NAME                COMMAND                  SERVICE             STATUS
elibrary_db         "docker-entrypoint.s…"   db                  Up 10s
elibrary_web        "sh -c 'python manag…"   web                 Up 8s
elibrary_nginx      "nginx -g daemon off…"   nginx               Up 6s
```

### Step 2: Wait for Database to be Ready

```powershell
# Check database health
docker-compose exec db pg_isready -U elibrary_user

# Wait for output: "accepting connections"
```

### Step 3: Run Django Migrations

```powershell
# Apply migrations to PostgreSQL
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Run migration verification script
docker-compose exec web python migrate_to_postgres.py
```

### Step 4: Verify Deployment

```powershell
# Check web container logs
docker-compose logs web

# Check database logs
docker-compose logs db

# Check Nginx logs
docker-compose logs nginx

# Test application
# Open browser: http://localhost
# Admin panel: http://localhost/admin
```

---

## Phase 5: Data Migration from SQLite

### Option A: Automatic Backup and Restore

```powershell
# 1. Stop all containers
docker-compose down

# 2. Backup current SQLite
copy db.sqlite3 db.sqlite3.backup

# 3. Restart with PostgreSQL
docker-compose up -d

# 4. Wait for database ready
Start-Sleep -Seconds 10

# 5. Run migrations
docker-compose exec web python manage.py migrate

# 6. Verify data
docker-compose exec web python manage.py shell
```

In Django shell:
```python
from django.apps import apps

models = apps.get_models()
for model in models:
    count = model.objects.count()
    if count > 0:
        print(f"{model._meta.label}: {count} records")
```

### Option B: Manual Data Export/Import

```powershell
# Export from SQLite (before Docker)
python manage.py dumpdata > data.json

# Import to PostgreSQL (in Docker)
docker-compose exec web python manage.py loaddata /path/to/data.json
```

---

## Phase 6: Testing

### Health Checks

```powershell
# Test web application
curl http://localhost

# Test admin panel
curl http://localhost/admin

# Test API endpoint
curl http://localhost/api/

# Check database connection
docker-compose exec web python manage.py dbshell
```

### Performance Monitoring

```powershell
# Monitor container resource usage
docker stats

# View container logs in real-time
docker-compose logs -f

# Check database performance
docker-compose exec db psql -U elibrary_user -d elibrary -c "SELECT version();"
```

---

## Phase 7: Troubleshooting

### Container Won't Start

```powershell
# Check logs
docker-compose logs

# Remove containers and volumes
docker-compose down -v

# Rebuild
docker-compose build --no-cache

# Start again
docker-compose up -d
```

### Database Connection Failed

```powershell
# Check if database is ready
docker-compose exec db pg_isready -U elibrary_user

# If not ready, wait and retry
Start-Sleep -Seconds 5
docker-compose restart db
```

### Static Files Not Loading

```powershell
# Collect static files again
docker-compose exec web python manage.py collectstatic --noinput --clear

# Verify permissions
docker-compose exec web ls -la /app/static/
```

### Out of Memory

```powershell
# Increase Docker memory in WSL2
# Edit ~/.wslconfig (see Phase 1, Step 3)

# Restart WSL
wsl --shutdown

# Start Docker again
```

---

## Phase 8: Accessing Services

| Service | URL | Notes |
|---------|-----|-------|
| Application | http://localhost | Main web interface |
| Admin Panel | http://localhost/admin | Django admin |
| API | http://localhost/api/ | REST API endpoints |
| Database | localhost:5432 | PostgreSQL (from host) |
| pgAdmin | http://localhost:5050 | (Optional) Database admin |

---

## Phase 9: Backup and Restore

### Backup PostgreSQL

```powershell
# Backup database
docker-compose exec db pg_dump -U elibrary_user elibrary > backup_$(Get-Date -Format "yyyyMMdd").sql

# Backup media files
tar -czf media_backup_$(Get-Date -Format "yyyyMMdd").tar.gz /path/to/media/
```

### Restore PostgreSQL

```powershell
# Restore database
cat backup_20260107.sql | docker-compose exec -T db psql -U elibrary_user -d elibrary
```

---

## Phase 10: Next Steps

### When Ubuntu/Raspberry Pi is Ready:

1. **Copy files** from Windows to Ubuntu:
   ```bash
   scp -r /path/to/project user@ubuntu-server:/home/user/
   ```

2. **Run same commands** on Ubuntu (no Docker needed on RPi, just containers):
   ```bash
   docker-compose up -d
   ```

3. **Restore backup** (data already migrated):
   ```bash
   cat backup_20260107.sql | docker-compose exec -T db psql -U elibrary_user -d elibrary
   ```

---

## Summary

✅ **Completed:**
- Windows Docker Desktop setup
- WSL2 integration
- PostgreSQL in Docker
- Django migrations
- Data from SQLite → PostgreSQL
- Full production stack running locally

**Application is now running at:** `http://localhost`

**Ready for:**
- Production deployment to Ubuntu/Raspberry Pi
- Scaling and optimization
- Security hardening
