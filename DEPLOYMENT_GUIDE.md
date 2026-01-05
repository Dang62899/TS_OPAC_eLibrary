# Deployment Guide - TS OPAC eLibrary

## Overview

This guide covers deployment to Railway.app (recommended) or Heroku.

## Phase 1: Pre-Deployment Checklist

### 1. Requirements
- [ ] Python 3.11+
- [ ] Git repository initialized
- [ ] All code committed to git
- [ ] Environment variables defined
- [ ] Database backups created
- [ ] Static files collected locally
- [ ] Tests passing (at least 70% coverage)
- [ ] Production SECRET_KEY generated

### 2. Generate Production SECRET_KEY

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. Environment Setup

Create `.env.production` with required variables:

```bash
cp .env.production.template .env.production
# Edit with production values
```

## Phase 2: Deploy to Railway.app (Recommended)

### Step 1: Install Railway CLI

```bash
npm install -g @railway/cli
```

### Step 2: Create Railway Project

```bash
railway init
# Select "Create a new project"
# Name: ts-opac-elibrary
```

### Step 3: Add PostgreSQL Database

```bash
railway add postgresql
```

### Step 4: Add Redis Cache

```bash
railway add redis
```

### Step 5: Deploy Application

```bash
railway up --detach
```

### Step 6: Set Environment Variables

```bash
railway variables set SECRET_KEY "your-secret-key"
railway variables set DEBUG False
railway variables set ALLOWED_HOSTS "*.railway.app"
```

### Step 7: Run Migrations

```bash
railway run python manage.py migrate
```

### Step 8: Create Superuser

```bash
railway run python manage.py createsuperuser
```

### Step 9: Collect Static Files

```bash
railway run python manage.py collectstatic --noinput
```

## Phase 3: Deploy to Heroku

### Step 1: Install Heroku CLI

```bash
# macOS
brew tap heroku/brew && brew install heroku

# Windows (using npm)
npm install -g heroku
```

### Step 2: Create Heroku App

```bash
heroku create ts-opac-elibrary
heroku login
```

### Step 3: Add PostgreSQL Add-on

```bash
heroku addons:create heroku-postgresql:hobby-dev
```

### Step 4: Add Redis Add-on

```bash
heroku addons:create heroku-redis:premium-0
```

### Step 5: Configure Environment Variables

```bash
heroku config:set SECRET_KEY="your-secret-key"
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS="ts-opac-elibrary.herokuapp.com"
```

### Step 6: Deploy Application

```bash
git push heroku main  # or your branch name
```

### Step 7: Run Migrations

```bash
heroku run python manage.py migrate
```

### Step 8: Create Superuser

```bash
heroku run python manage.py createsuperuser
```

### Step 9: View Logs

```bash
heroku logs --tail
```

## Phase 4: Post-Deployment Verification

### 1. Health Checks

```bash
# Check application is running
curl https://your-domain.com/
```

### 2. API Verification

```bash
# Test API endpoint
curl https://your-domain.com/api/v1/publications/

# Get auth token
curl -X POST https://your-domain.com/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'
```

### 3. Database Verification

```bash
# Check database connection
python manage.py dbshell

# Run system checks
python manage.py check --deploy
```

### 4. Static Files Verification

```bash
# Verify static files are served correctly
curl https://your-domain.com/static/css/custom.css
```

### 5. Monitoring

- Check application logs on Railway/Heroku dashboard
- Monitor error tracking via Sentry
- Review database performance metrics
- Check API response times

## Phase 5: Custom Domain Setup

### For Railway:

```bash
railway domain add your-domain.com
```

### For Heroku:

```bash
heroku domains:add your-domain.com
```

Then update your domain registrar's DNS records to point to the deployment platform.

## Scaling & Performance

### Increase Dyno Type (Heroku)

```bash
heroku dyos:type Standard-1X
```

### Database Connection Pooling

Already configured in `settings.py` with `dj-database-url`

### Caching Configuration

Redis is configured for:
- Session caching
- Celery task queue
- API response caching

## Troubleshooting

### Database Connection Issues

```bash
# Check DATABASE_URL is set correctly
heroku config:get DATABASE_URL

# Verify migrations
heroku run python manage.py showmigrations
```

### Static Files Not Loading

```bash
# Recollect static files
heroku run python manage.py collectstatic --noinput

# Verify WhiteNoise configuration in settings.py
```

### Memory Issues

```bash
# Monitor memory usage
heroku ps

# Scale down background workers if needed
heroku ps:scale worker=0
```

### SSL Certificate Issues

- Railway: Auto-managed
- Heroku: Auto-managed via letsencrypt

To force HTTPS:
```python
# Already configured in settings.py:
SECURE_SSL_REDIRECT = True
```

## Backup & Disaster Recovery

### Database Backups (Heroku)

```bash
# Create backup
heroku pg:backups create

# Download backup
heroku pg:backups download b001

# Restore backup
heroku pg:backups restore b001
```

### Database Backups (Railway)

Automated daily backups are enabled. Access via Railway dashboard.

### Media Files Backup

Consider using AWS S3 or Cloudinary for media storage:

```bash
# Install storages
pip install django-storages boto3

# Configure in settings.py for S3 storage
```

## Security Considerations

### Environment Variables
- Never commit `.env` files to git
- Use `.env.production` template only as reference
- Rotate secrets regularly
- Use strong SECRET_KEY

### HTTPS/SSL
- Enforced in production settings
- Auto-managed by deployment platform
- Verify SECURE_SSL_REDIRECT=True

### Database Security
- Use strong passwords
- Enable database encryption
- Restrict database access to application only
- Regular backups

### API Security
- Token authentication required for sensitive endpoints
- Rate limiting: 1000 requests/day per IP
- CORS configured for approved origins only
- CSRF protection enabled

## Monitoring & Alerting

### Error Tracking (Sentry)
```bash
# Set Sentry DSN
heroku config:set SENTRY_DSN="your-sentry-dsn"
```

### Application Monitoring
- Heroku: Built-in metrics via dashboard
- Railway: Built-in metrics via dashboard
- Custom: Configure with New Relic or DataDog

### Log Aggregation
```bash
# View application logs
heroku logs -t  # tail logs
heroku logs -n 100  # last 100 lines
```

## Next Steps

1. Monitor application in production
2. Set up automated backups
3. Configure alerts for errors
4. Plan scaling strategy
5. Review security audit logs regularly
6. Update dependencies quarterly
7. Perform load testing before peak usage

## Support & Documentation

- Django Documentation: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- Railway Documentation: https://docs.railway.app/
- Heroku Documentation: https://devcenter.heroku.com/
