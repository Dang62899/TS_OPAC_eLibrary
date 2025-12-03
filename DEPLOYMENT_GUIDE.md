# TS_OPAC eLIbrary - Deployment Guide

## ❌ What Went Wrong with Cloudflare Pages

Cloudflare Pages tried to use **Wrangler** (for serverless Workers), but your app is a **full-stack Django application** that needs:
- Python runtime
- PostgreSQL database
- Session management
- Static file serving

**Cloudflare Pages is for static sites only** (HTML, CSS, JS). Django needs a real Python server.

---

## ✅ Recommended Deployment Options

### Option 1: Railway.app (RECOMMENDED - Easiest)

**Why Railway?**
- ✅ Auto-detects Django
- ✅ Free PostgreSQL included
- ✅ Auto-HTTPS
- ✅ Git integration (auto-deploy on push)
- ✅ Zero downtime deployments
- ✅ Free tier available
- ✅ Takes 5 minutes to set up

**Setup Steps:**

```bash
# 1. Go to https://railway.app
# 2. Sign up with GitHub
# 3. Click "Start a New Project"
# 4. Select "Deploy from GitHub"
# 5. Select your TS_OPAC_eLibrary repository
# 6. Railway auto-configures:
#    - Python 3.11
#    - PostgreSQL database
#    - Environment variables
# 7. Click "Deploy"
```

**Environment Variables in Railway Dashboard:**
```
DJANGO_SETTINGS_MODULE=elibrary.settings
ELIBRARY_PRODUCTION=True
SECRET_KEY=<generate-strong-random-key>
DEBUG=False
ALLOWED_HOSTS=<your-railway-domain>.up.railway.app
```

**After Deployment:**
```bash
# Run migrations (one-time)
railway run python manage.py migrate

# Create superuser (one-time)
railway run python manage.py createsuperuser

# View logs
railway logs

# Then push to main to auto-deploy future changes
```

**Cost:** Free tier covers your needs. Paid plans at $5+/month.

---

### Option 2: Heroku

**Setup Steps:**

```bash
# 1. Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli
# 2. Login
heroku login

# 3. Create app
heroku create ts-opac-elibrary

# 4. Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# 5. Set environment variables
heroku config:set DJANGO_SETTINGS_MODULE=elibrary.settings
heroku config:set ELIBRARY_PRODUCTION=True
heroku config:set SECRET_KEY=<your-secret-key>
heroku config:set DEBUG=False

# 6. Deploy
git push heroku main

# 7. Run migrations
heroku run python manage.py migrate

# 8. Create superuser
heroku run python manage.py createsuperuser

# 9. View application
heroku open
```

**Cost:** Free tier was discontinued. Paid plans start at $7+/month. ⚠️ Not recommended for free hosting.

---

### Option 3: PythonAnywhere

**Setup Steps:**

1. Go to https://www.pythonanywhere.com
2. Sign up (free account available)
3. "Add a new web app"
4. Select "Manual configuration" → Python 3.11
5. Clone your repository in "Bash console"
6. Configure WSGI file:
   ```python
   import os
   os.environ['DJANGO_SETTINGS_MODULE'] = 'elibrary.settings'
   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```
7. Upload static files: `python manage.py collectstatic`
8. Set environment variables in web app settings

**Cost:** Free tier includes one web app. Paid plans at $5+/month.

---

### Option 4: Render.com

**Setup Steps:**

```bash
# 1. Go to https://render.com
# 2. Sign up with GitHub
# 3. Click "New +" → "Web Service"
# 4. Connect your GitHub repository
# 5. Render auto-detects Django
# 6. Configuration:
#    - Environment: Python 3.11
#    - Build: pip install -r requirements.txt
#    - Start: gunicorn elibrary.wsgi:application
# 7. Add environment variables:
#    - DJANGO_SETTINGS_MODULE=elibrary.settings
#    - ELIBRARY_PRODUCTION=True
#    - SECRET_KEY=your-secret-key
# 8. Deploy
```

**Cost:** Free tier available. Paid plans at $7+/month.

---

## 🚀 Quick Comparison

| Feature | Railway | Heroku | PythonAnywhere | Render |
|---------|---------|--------|----------------|--------|
| Auto-detect Django | ✅ | ✅ | Manual | ✅ |
| Free Tier | ✅ | ❌ | ✅ | ✅ |
| PostgreSQL Included | ✅ | ✅ (paid) | ✅ (extra) | ✅ |
| Auto-deploy on push | ✅ | ✅ | ❌ | ✅ |
| Setup Time | 5 min | 10 min | 15 min | 10 min |
| Support | Good | Excellent | Good | Good |

---

## 📝 Configuration Files You Need

### For Railway.app (Just push - it auto-detects)
- Already configured ✅
- No additional files needed

### For Heroku (You'll need Procfile)
Create `Procfile` in root directory:
```
web: gunicorn elibrary.wsgi --log-file -
release: python manage.py migrate
```

### For PythonAnywhere (Web app configuration)
- No files needed, configure in web dashboard

### For Render.com (Auto-detected from requirements.txt)
- Already configured ✅

---

## Environment Variables Needed for Production

All platforms require these environment variables:

```
DJANGO_SETTINGS_MODULE=elibrary.settings
ELIBRARY_PRODUCTION=True
DEBUG=False
SECRET_KEY=<generate-with-django.core.management.utils.get_random_secret_key()>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=<auto-provided-by-platform>
```

**To generate a secure SECRET_KEY:**
```bash
python manage.py shell
>>> from django.core.management.utils import get_random_secret_key
>>> print(get_random_secret_key())
# Copy the output to your environment variables
```

---

## ❌ Remove Cloudflare Pages Configuration

Since Cloudflare Pages isn't suitable for Django:

```bash
git rm wrangler.jsonc wrangler.json netlify.toml (if not using Netlify)
git commit -m "Remove Cloudflare Pages config - using Railway.app instead"
git push origin main
```

---

## Database Considerations

### Development (Local SQLite)
- ✅ Works fine for testing
- ❌ Not suitable for production (single-user)
- ❌ Not suitable for multiple users

### Production
- ✅ PostgreSQL (Recommended)
  - All platforms provide PostgreSQL
  - Supports multiple concurrent users
  - Better performance
  - Automatic backups

- ❌ SQLite
  - Lock issues with multiple users
  - Not recommended for production
  - Will cause errors under load

**Update settings.py for production PostgreSQL:**
```python
if ELIBRARY_PRODUCTION:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default='sqlite:///db.sqlite3',
            conn_max_age=600
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
```

Add to `requirements.txt`:
```
dj-database-url>=1.3.0
psycopg2-binary>=2.9.0
```

---

## Post-Deployment Checklist

After deploying to production:

- [ ] Run migrations: `python manage.py migrate`
- [ ] Create superuser: `python manage.py createsuperuser`
- [ ] Collect static files: `python manage.py collectstatic`
- [ ] Test dark mode toggle
- [ ] Test login/logout (session timeout)
- [ ] Test catalog browsing
- [ ] Test circulation features
- [ ] Check terminal logs for errors
- [ ] Verify HTTPS working
- [ ] Test mobile responsiveness
- [ ] Monitor database connections

---

## Troubleshooting Production Deployment

### "DisallowedHost" Error
- Add your domain to ALLOWED_HOSTS in settings.py
- Format: `ALLOWED_HOSTS=['yourdomain.com', 'www.yourdomain.com']`

### Static Files Not Loading
- Run: `python manage.py collectstatic`
- Configure CDN (optional): CloudFlare or S3

### Database Connection Error
- Verify DATABASE_URL environment variable
- Check PostgreSQL connection string format
- Ensure database credentials are correct

### Session Not Working
- Verify SESSION_COOKIE_SECURE=True in production
- Check SESSION_COOKIE_HTTPONLY=True
- Ensure HTTPS is enabled

### Dark Mode Not Working
- Check staticfiles are collected
- Verify CSS files deployed
- Check browser cache (Ctrl+Shift+Delete)

---

## Recommended: Use Railway.app

**Why?**
1. **Simplest Setup** - 5 minutes
2. **Auto-configures Everything** - Python, PostgreSQL, HTTPS
3. **Free Tier Available** - Perfect for testing
4. **Auto-deploy** - Push to main, Railway deploys automatically
5. **Best Developer Experience** - Excellent docs

**Get Started:**
1. https://railway.app
2. Sign up with GitHub
3. Create project from TS_OPAC_eLibrary repository
4. Railway handles the rest
5. View your app at: https://yourappdomain.up.railway.app

---

## Summary

| Method | Result |
|--------|--------|
| ❌ Cloudflare Pages | Not suitable for Django (static sites only) |
| ✅ **Railway.app** | **Best option - easiest setup** |
| ✅ Heroku | Good but no free tier |
| ✅ PythonAnywhere | Good for Python projects |
| ✅ Render.com | Good with auto-deploy |

**Recommended Next Step:** Deploy to Railway.app (5 minutes, free tier available)
