# 🚀 Production Deployment Files

This directory contains everything needed to deploy TS_OPAC_eLibrary to production.

## 📋 Quick Navigation

| File | Purpose | Action |
|------|---------|--------|
| **`.env.production.template`** | Environment variables | Copy → `.env.production` → Edit |
| **`Dockerfile`** | Docker image definition | Use with `docker build` |
| **`docker-compose.yml`** | Full stack configuration | Run with `docker-compose up` |
| **`nginx.conf`** | Web server config | Copy to `/etc/nginx/nginx.conf` |
| **`.dockerignore`** | Docker build optimization | Automatic (already in place) |
| **`DEPLOYMENT_GUIDE.md`** | 📖 **START HERE** | Read for step-by-step instructions |
| **`PRE_DEPLOYMENT_CHECKLIST.md`** | ✅ Verification tasks | Complete before deploying |
| **`SECURITY_HARDENING.md`** | 🔒 Security guide | Configure production security |
| **`PRODUCTION_DEPLOYMENT_SUMMARY.md`** | Overview | Quick reference |

---

## 🎯 Getting Started (Choose One)

### Option A: Docker Compose (⭐ Recommended, 5 minutes)

```bash
# 1. Configure
cp .env.production.template .env.production
nano .env.production  # Edit with your values

# 2. Deploy
docker-compose up -d

# 3. Initialize
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

# 4. Access
# http://localhost (or your domain)
```

**Best for:** Cloud servers, rapid deployment, all-in-one stack

### Option B: Traditional Server (30 minutes)

```bash
# Follow DEPLOYMENT_GUIDE.md "Manual Deployment" section
# For Ubuntu 20.04+
```

**Best for:** On-premise servers, custom configurations

---

## 📝 Step-by-Step Deployment

### Step 1: Review Documentation (5 min)
1. Read `PRODUCTION_DEPLOYMENT_SUMMARY.md` for overview
2. Skim `DEPLOYMENT_GUIDE.md` to choose your method
3. Note domain name and IP address

### Step 2: Prepare Environment (10 min)
1. Copy `.env.production.template` to `.env.production`
2. Generate secure keys:
   ```bash
   # SECRET_KEY
   python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   
   # Database password
   openssl rand -base64 32
   
   # Redis password
   openssl rand -base64 32
   ```
3. Update `.env.production` with your values:
   - `ELIBRARY_SECRET_KEY` - Paste generated key
   - `ELIBRARY_ALLOWED_HOSTS` - Your domain(s)
   - `DB_PASSWORD` - Database password
   - `REDIS_PASSWORD` - Redis password
   - `EMAIL_*` - Email configuration

### Step 3: Deploy (5-30 min depending on method)

**Docker (5 min):**
```bash
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

**Traditional (30 min):**
- Follow detailed steps in `DEPLOYMENT_GUIDE.md`
- Create systemd services
- Configure Nginx
- Set up database

### Step 4: Configure SSL (10 min)
```bash
# Docker with Let's Encrypt
certbot certonly --standalone -d yourdomain.com

# Update nginx.conf with certificate paths
# Restart Nginx: docker-compose restart nginx
```

### Step 5: Verify (5 min)
1. Check application: `curl https://yourdomain.com`
2. Run Django checks: `python manage.py check --deploy`
3. View logs: `docker-compose logs -f` (Docker) or `journalctl -u elibrary -f` (Traditional)
4. Monitor: Open monitoring dashboard

---

## 🔒 Security Settings

### Pre-Deployment
- [ ] Edit `.env.production` with secure values
- [ ] Set `ELIBRARY_PRODUCTION=True`
- [ ] Set `ELIBRARY_DEBUG=False`
- [ ] Generate secure `ELIBRARY_SECRET_KEY` (50+ chars)
- [ ] Use strong database password (32+ chars)
- [ ] Use strong Redis password (32+ chars)

### Post-Deployment
- [ ] Install SSL certificate (Let's Encrypt)
- [ ] Test SSL security: https://www.ssllabs.com/
- [ ] Test security headers: https://securityheaders.com/
- [ ] Set up database backups
- [ ] Configure monitoring/alerts
- [ ] Document admin procedures

**All settings are documented in `SECURITY_HARDENING.md`**

---

## 📊 Architecture

```
User Traffic
    ↓
Nginx (Port 80/443)
  ├─ SSL/TLS
  ├─ Rate Limiting
  └─ Static Files
    ↓
Django (Gunicorn × 4 workers)
    ↓
    ├─→ PostgreSQL (Database)
    ├─→ Redis (Cache & Celery Broker)
    └─→ Celery (Background Tasks)
```

---

## 🛠️ Important Files

### Configuration
- **`.env.production`** - Your production environment (DO NOT COMMIT)
- **`docker-compose.yml`** - Docker stack definition
- **`Dockerfile`** - Application image definition
- **`nginx.conf`** - Web server configuration

### Documentation
- **`DEPLOYMENT_GUIDE.md`** - Complete setup instructions (750+ lines)
- **`PRE_DEPLOYMENT_CHECKLIST.md`** - Verification checklist (100+ items)
- **`SECURITY_HARDENING.md`** - Security configuration guide (360+ lines)
- **`PRODUCTION_DEPLOYMENT_SUMMARY.md`** - Quick reference

---

## ⚠️ Critical Environment Variables

These MUST be set in `.env.production`:

```bash
# Security
ELIBRARY_SECRET_KEY=<generated-50+-char-key>
ELIBRARY_PRODUCTION=True
ELIBRARY_DEBUG=False
ELIBRARY_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgresql://elibrary_user:PASSWORD@localhost/elibrary_db

# Cache/Tasks
CELERY_BROKER_URL=redis://:PASSWORD@localhost:6379/0

# Email (optional but recommended)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-password
```

**Generate secure keys:**
```bash
# Python
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Bash/OpenSSL
openssl rand -base64 32
```

---

## 🧪 Verification Commands

After deployment, verify everything is working:

```bash
# Health check
curl https://yourdomain.com/health

# Django system check
python manage.py check --deploy

# Lint verification
python -m flake8 --count  # Should be: 0

# Database connectivity
docker-compose exec web python manage.py dbshell

# Static files
curl https://yourdomain.com/static/css/custom.css

# Admin panel
curl https://yourdomain.com/admin/

# Logs (Docker)
docker-compose logs -f web
docker-compose logs -f nginx
docker-compose logs -f db
```

---

## 🐛 Troubleshooting

### Application Won't Start
→ Check logs: `docker-compose logs web` or `journalctl -u elibrary -f`

### Database Error
→ Verify `DATABASE_URL` in `.env.production`
→ Test: `psql -U elibrary_user -d elibrary_db`

### Static Files Not Loading
→ Run: `docker-compose exec web python manage.py collectstatic --noinput`

### SSL Certificate Issues
→ Check expiration: `openssl x509 -in /path/to/cert -text -noout | grep Validity`
→ Renew: `certbot renew --force-renewal`

**More help:** See `DEPLOYMENT_GUIDE.md` "Troubleshooting" section

---

## 📦 Stack Components

- **Django 4.2+** - Web framework
- **PostgreSQL 13+** - Database
- **Redis 6+** - Cache & Celery broker
- **Nginx** - Reverse proxy & web server
- **Gunicorn** - WSGI application server
- **Celery** - Background job processing
- **Let's Encrypt** - Free SSL/TLS certificates

---

## 📋 Pre-Deployment Checklist

Before going live, complete **`PRE_DEPLOYMENT_CHECKLIST.md`** which includes:

- ✅ Code quality (lint, tests, imports)
- ✅ Django configuration (SECRET_KEY, ALLOWED_HOSTS, etc.)
- ✅ Security hardening (SSL, headers, passwords)
- ✅ Database setup (PostgreSQL, backups)
- ✅ Infrastructure (firewall, services, resources)
- ✅ Performance optimization (caching, compression)
- ✅ Monitoring & logging setup
- ✅ Post-deployment verification

---

## 🔄 Maintenance

### Daily
```bash
# Check logs
docker-compose logs web  # or: journalctl -u elibrary
tail -f /var/log/nginx/error.log
```

### Weekly
```bash
# Update & restart
docker-compose pull
docker-compose up -d
```

### Monthly
```bash
# Security updates
apt update && apt upgrade -y  # Linux

# Database backup
pg_dump -U elibrary_user elibrary_db > backup.sql
```

---

## 🚀 Next Steps

1. **Now:** Read `DEPLOYMENT_GUIDE.md`
2. **Then:** Complete `PRE_DEPLOYMENT_CHECKLIST.md`
3. **Setup:** Configure `.env.production`
4. **Deploy:** Run Docker Compose or follow traditional setup
5. **Verify:** Test all components
6. **Monitor:** Set up logging and alerts
7. **Backup:** Configure automated backups
8. **Secure:** Set up SSL and security headers

---

## 📞 Support

- **Setup Issues:** See `DEPLOYMENT_GUIDE.md` "Troubleshooting"
- **Security Questions:** See `SECURITY_HARDENING.md`
- **Code Quality:** See `LINT_CLEANUP_SUMMARY.md`
- **Django Docs:** https://docs.djangoproject.com/en/4.2/howto/deployment/

---

## 📄 File Summary

| File | Lines | Purpose |
|------|-------|---------|
| `.env.production.template` | 170 | Environment variable template |
| `Dockerfile` | 45 | Docker image definition |
| `docker-compose.yml` | 170 | Full stack orchestration |
| `nginx.conf` | 300+ | Web server configuration |
| `.dockerignore` | 60 | Docker build optimization |
| `DEPLOYMENT_GUIDE.md` | 750+ | Step-by-step deployment |
| `PRE_DEPLOYMENT_CHECKLIST.md` | 350+ | Verification checklist |
| `SECURITY_HARDENING.md` | 360+ | Security configuration |
| `PRODUCTION_DEPLOYMENT_SUMMARY.md` | 365 | Deployment overview |

**Total: 2,500+ lines of production deployment documentation and configuration**

---

## ✅ Status

- ✅ Code quality: 0 flake8 violations
- ✅ Django checks: Passing (6 expected dev warnings)
- ✅ Docker configured: Ready to deploy
- ✅ Documentation: Complete (750+ lines)
- ✅ Security: Hardened and documented
- ✅ **Status: PRODUCTION READY** 🎉

---

**Version:** 1.0  
**Updated:** 2024  
**Status:** ✅ Ready for Production Deployment

