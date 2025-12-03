# Cloudflare Pages Configuration for TS_OPAC eLIbrary Django Application

## Build Configuration

- **Build Command:** `python manage.py collectstatic --noinput && python manage.py migrate --noinput`
- **Build Output Directory:** `staticfiles`
- **Python Version:** 3.11+
- **Node Version:** Latest (20+)

## Environment Variables

Add these to your Cloudflare Pages project settings:

### Production Environment Variables:
```
DJANGO_SETTINGS_MODULE=elibrary.settings
ELIBRARY_PRODUCTION=True
DEBUG=False
SECRET_KEY=your-very-secure-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=your-database-connection-string
```

### Development Environment Variables:
```
DJANGO_SETTINGS_MODULE=elibrary.settings
ELIBRARY_PRODUCTION=False
DEBUG=True
```

## Deployment Steps

### Option 1: Using Cloudflare Pages (Recommended)

Cloudflare Pages is designed for static sites and frontend applications. For a Django backend, you have a few options:

#### 1A: Deploy Backend Separately (Recommended)
- Deploy Django backend to **Heroku**, **Railway**, **Render**, or **PythonAnywhere**
- Use Cloudflare Pages only for static assets
- Use CORS to connect frontend to backend API

#### 1B: Use Cloudflare Workers + Python API
- This approach requires adapting your Django app as API endpoints
- More complex - not recommended for full Django apps

### Option 2: Deploy to Heroku (Better for Django)

```bash
# 1. Install Heroku CLI
# 2. Login to Heroku
heroku login

# 3. Create Heroku app
heroku create ts-opac-elibrary

# 4. Add PostgreSQL database
heroku addons:create heroku-postgresql:hobby-dev

# 5. Set environment variables
heroku config:set DJANGO_SETTINGS_MODULE=elibrary.settings
heroku config:set ELIBRARY_PRODUCTION=True
heroku config:set SECRET_KEY=your-secret-key

# 6. Deploy
git push heroku main

# 7. Migrate database
heroku run python manage.py migrate

# 8. Create superuser
heroku run python manage.py createsuperuser
```

### Option 3: Deploy to Railway.app (Easiest)

```bash
# 1. Sign up at railway.app
# 2. Connect your GitHub repository
# 3. Railway auto-detects Django and sets up:
#    - Python environment
#    - PostgreSQL database
#    - Environment variables
# 4. Push to main branch and Railway deploys automatically
```

### Option 4: Deploy to PythonAnywhere

1. Sign up at pythonanywhere.com
2. Link your GitHub repository
3. Configure Django settings
4. PythonAnywhere handles static files and database

## Current Issue with Cloudflare Pages

Cloudflare Pages detected a deployment command looking for a **Wrangler Worker** configuration, but TS_OPAC eLIbrary is a **Django full-stack application**, not a static site.

### Why Cloudflare Pages Fails:
- ❌ Pages is designed for static sites (HTML, CSS, JS)
- ❌ Pages cannot execute Python backend code
- ❌ Pages tries to use Wrangler (for Workers), which isn't configured
- ❌ Django requires a Python runtime server

### Recommended Solutions:

1. **Use Railway.app** (Easiest - auto-configures Django)
2. **Use Heroku** (Good free tier - just add credit card)
3. **Use PythonAnywhere** (Python-specific hosting)
4. **Use AWS Elastic Beanstalk** (More complex but scalable)

## Proper Cloudflare Setup for Django

If you want to use Cloudflare (not Pages):

1. **Backend:** Deploy Django to Heroku/Railway/PythonAnywhere
2. **CDN:** Use Cloudflare as reverse proxy/CDN
3. **Static Files:** Serve static files from Cloudflare Pages or S3
4. **DNS:** Point your domain to Cloudflare

This gives you:
- ✅ Django backend running on dedicated Python server
- ✅ Cloudflare CDN for faster static file delivery
- ✅ DDoS protection
- ✅ Better performance

## Files to Remove from Git

These were created for failed Cloudflare Pages deployment:
```bash
git rm wrangler.jsonc wrangler.json
git commit -m "Remove Cloudflare Pages config - using Railway.app instead"
```

## Next Steps

**Recommended: Use Railway.app**

1. Go to https://railway.app
2. Click "Start a New Project"
3. Select "Deploy from GitHub"
4. Select your TS_OPAC_eLibrary repository
5. Railway auto-detects Django and sets up PostgreSQL
6. Add environment variables:
   - DJANGO_SETTINGS_MODULE=elibrary.settings
   - ELIBRARY_PRODUCTION=True
   - SECRET_KEY=your-secret-key
7. Push to main branch
8. Railway deploys automatically

**Total setup time: 10 minutes**
**Cost: Free with paid options available**

Would you like me to set up Railway.app configuration files instead?
