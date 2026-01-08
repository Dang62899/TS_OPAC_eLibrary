# Days 3-4 Docker Setup - Quick Start Checklist

## ✅ Pre-Deployment Checklist

### Windows Prerequisites
- [ ] Windows 10 Pro/Enterprise or Windows 11 (Home can use WSL2)
- [ ] At least 8GB RAM available
- [ ] 20GB free disk space
- [ ] Internet connection (for downloads)

### Step 1: Install Docker Desktop (10 minutes)

```powershell
# Open PowerShell as Administrator
# Run these commands:

wsl --install
wsl --set-default-version 2
```

Then:
- Download Docker Desktop: https://www.docker.com/products/docker-desktop
- Install with default settings
- Enable WSL2 integration: Docker Desktop → Settings → Resources → WSL Integration
- Verify: `docker --version` and `docker-compose --version`

### Step 2: WSL2 Configuration (5 minutes)

Create file: `C:\Users\[YourUsername]\.wslconfig`

```ini
[wsl2]
memory=4GB
processors=4
swap=2GB
localhostForwarding=true
```

Then restart WSL:
```powershell
wsl --shutdown
```

### Step 3: Prepare Application (5 minutes)

**Verify files exist in your project:**
- [ ] `Dockerfile` - Present and correct
- [ ] `docker-compose.yml` - Present and correct
- [ ] `nginx.conf` - Present and correct
- [ ] `.env` file - Created with correct values

**Update `.env` file:**
```env
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
SECRET_KEY=your-random-secret-key-here

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

### Step 4: Build Docker Image (10 minutes)

```powershell
cd C:\Users\Dang\Desktop\TS_OPAC_eLibrary
docker-compose build
```

Expected output:
```
Building web
...
Successfully tagged elibrary:latest
```

### Step 5: Start Containers (5 minutes)

```powershell
docker-compose up -d
```

Wait 10 seconds for database to start:
```powershell
Start-Sleep -Seconds 10
docker-compose ps
```

Expected output:
```
NAME          STATUS
elibrary_db   Up ...
elibrary_web  Up ...
elibrary_nginx Up ...
```

### Step 6: Initialize Database (5 minutes)

```powershell
# Wait for database to be ready
docker-compose exec db pg_isready -U elibrary_user

# Apply migrations
docker-compose exec web python manage.py migrate

# Create superuser (follow prompts)
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

### Step 7: Verify Deployment (5 minutes)

**Test URLs:**
```powershell
# Application
curl http://localhost

# Admin Panel
curl http://localhost/admin

# API
curl http://localhost/api/

# Database check
docker-compose exec db psql -U elibrary_user -d elibrary -c "SELECT version();"
```

**Open in browser:**
- Application: http://localhost
- Admin: http://localhost/admin (use superuser credentials)
- API: http://localhost/api/

---

## 🔍 Verification Tests

### ✅ All Containers Running?
```powershell
docker-compose ps
```
Should show 3 containers: `db`, `web`, `nginx` all `Up`

### ✅ Database Connected?
```powershell
docker-compose exec web python manage.py shell
```
Then in Python:
```python
from django.db import connection
connection.ensure_connection()
print("✅ Database connected!")
exit()
```

### ✅ Static Files Loaded?
```powershell
# Check if admin interface loads correctly
curl http://localhost/admin/
```
Should return HTML (not 404 error)

### ✅ API Responding?
```powershell
curl http://localhost/api/
```
Should return JSON response

---

## 📊 Data Migration (Optional Now)

### If you want to keep existing data:

```powershell
# 1. Backup SQLite (if exists)
copy db.sqlite3 db.sqlite3.backup

# 2. Export data from SQLite
python manage.py dumpdata > data.json

# 3. Load into PostgreSQL (in Docker)
docker-compose exec web python manage.py loaddata data.json

# 4. Verify
docker-compose exec web python manage.py shell
```

In Python:
```python
from django.apps import apps
models = apps.get_models()
for model in models:
    count = model.objects.count()
    if count > 0:
        print(f"{model._meta.label}: {count} records")
```

---

## 🛠️ Useful Commands

### Monitor Logs
```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web      # Django app
docker-compose logs -f db       # PostgreSQL
docker-compose logs -f nginx    # Web server
```

### Execute Commands in Container
```powershell
# Django shell
docker-compose exec web python manage.py shell

# Database shell
docker-compose exec db psql -U elibrary_user -d elibrary

# Bash shell
docker-compose exec web bash
```

### Resource Usage
```powershell
# Real-time resource monitoring
docker stats

# Container details
docker-compose ps -a
```

### Restart Services
```powershell
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart web

# Stop and start
docker-compose down
docker-compose up -d
```

---

## ⚠️ Troubleshooting

### Containers Won't Start
```powershell
# Check logs
docker-compose logs

# Rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Database Connection Failed
```powershell
# Check if database is ready
docker-compose exec db pg_isready -U elibrary_user

# Wait and retry
Start-Sleep -Seconds 5
docker-compose restart db
```

### Out of Memory
Edit `.wslconfig` and increase memory, then:
```powershell
wsl --shutdown
docker-compose up -d
```

### Port Already in Use
```powershell
# Find what's using port
netstat -ano | findstr :80

# Kill process
taskkill /PID <PID> /F
```

---

## 📋 Post-Deployment

### Access Points
| Service | URL | Login |
|---------|-----|-------|
| Web App | http://localhost | N/A |
| Admin | http://localhost/admin | superuser account |
| API | http://localhost/api/ | Token auth (if enabled) |
| Database | localhost:5432 | pguser/password |

### Backup Data
```powershell
# Database backup
docker-compose exec db pg_dump -U elibrary_user elibrary > backup_$(Get-Date -Format "yyyyMMdd").sql

# Media backup
tar -czf media_backup.tar.gz ./media/
```

### Stop Services
```powershell
# Stop without removing
docker-compose stop

# Stop and remove
docker-compose down

# Stop and remove everything (including data!)
docker-compose down -v
```

---

## 🚀 Next: Deploy to Ubuntu/Raspberry Pi

When you have Ubuntu/Raspberry Pi ready:

1. Copy project files to Ubuntu
2. Install Docker and Docker Compose on Ubuntu
3. Run same `docker-compose up -d` command
4. Restore database backup if needed

**No changes needed!** Same files work on Ubuntu/RPi.

---

## 📞 Need Help?

**Check logs first:**
```powershell
docker-compose logs
```

**Common issues are usually in logs!** Search for `ERROR` or `CRITICAL`

**Reset everything:**
```powershell
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
docker-compose exec web python manage.py migrate
```

---

**Ready to start?** Run: `docker-compose up -d`

**Your app will be available at:** http://localhost
