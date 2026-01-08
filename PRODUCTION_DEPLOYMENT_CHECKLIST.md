# Production Deployment Checklist - Days 7-8

## Pre-Deployment (Before Starting)

### Environment Setup
- [ ] Copy `.env.production.example` to `.env.production`
- [ ] Generate strong DJANGO_SECRET_KEY
- [ ] Update all configuration values in `.env.production`
- [ ] Configure email credentials (Gmail App Password, etc.)
- [ ] Set ALLOWED_HOSTS to production domain
- [ ] Create SSL directory: `mkdir -p ssl`
- [ ] Create logs directory: `mkdir -p logs`
- [ ] Create backups directory: `mkdir -p backups`

### SSL/TLS Certificates
- [ ] Obtain SSL certificates (Let's Encrypt recommended)
- [ ] Place certificate in `ssl/cert.pem`
- [ ] Place private key in `ssl/key.pem`
- [ ] Verify certificate permissions: `chmod 644 ssl/cert.pem && chmod 600 ssl/key.pem`
- [ ] Test certificate with: `openssl x509 -in ssl/cert.pem -text -noout`

### Database Preparation
- [ ] Backup current development database
- [ ] Test database restore procedure
- [ ] Verify PostgreSQL performance settings
- [ ] Plan backup strategy (daily at 2 AM recommended)

---

## Day 7: Production Deployment

### Phase 1: Django Settings (✓ Files Created)
- [ ] Review `elibrary/settings_production.py`
- [ ] Verify all security settings
- [ ] Check email configuration
- [ ] Verify database connection pool settings
- [ ] Test Sentry integration (if using)

### Phase 2: Environment Variables (✓ File Created)
- [ ] Fill in all required variables in `.env.production`
- [ ] Use strong passwords (>16 characters)
- [ ] Test email credentials manually
- [ ] Verify domain/hostname correct
- [ ] **IMPORTANT**: Never commit `.env.production` to git

### Phase 3: Docker Compose Update (✓ Documented in DAYS_7-8_PRODUCTION_GUIDE.md)
- [ ] Update `docker-compose.yml` with production services
- [ ] Add Redis container for caching
- [ ] Configure volume mounts correctly
- [ ] Set restart policies to `unless-stopped`
- [ ] Add healthcheck endpoints

### Phase 4: Nginx Configuration (✓ Documented in DAYS_7-8_PRODUCTION_GUIDE.md)
- [ ] Create `nginx_production.conf` with SSL
- [ ] Update domain name in nginx config
- [ ] Configure SSL certificates paths
- [ ] Enable security headers (CSP, HSTS, etc.)
- [ ] Set up rate limiting
- [ ] Configure gzip compression
- [ ] Test nginx configuration: `docker run --rm -v $(pwd)/nginx_production.conf:/tmp/nginx.conf nginx nginx -t -c /tmp/nginx.conf`

### Phase 5: SSL Certificate Setup
```bash
# Option 1: Let's Encrypt (Recommended)
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./ssl/key.pem
sudo chmod 644 ./ssl/cert.pem ./ssl/key.pem

# Verify
openssl x509 -in ssl/cert.pem -text -noout | grep "Issuer\|Subject\|Not Before\|Not After"
```

- [ ] Certificate installed in `ssl/cert.pem`
- [ ] Private key installed in `ssl/key.pem`
- [ ] Certificate validity checked
- [ ] Certificate renewal plan created

### Phase 6: Production Deployment Commands
```bash
# 1. Generate Django secret key
python3 -c "import secrets; print(secrets.token_urlsafe(50))"

# 2. Create environment file
cp .env.production.example .env.production
# Edit with actual values

# 3. Start containers
docker-compose up -d

# 4. Run migrations
docker-compose exec web python manage.py migrate --settings=elibrary.settings_production

# 5. Create superuser
docker-compose exec web python manage.py createsuperuser --settings=elibrary.settings_production

# 6. Collect static files
docker-compose exec web python manage.py collectstatic --noinput --settings=elibrary.settings_production

# 7. Run production checks
docker-compose exec web python manage.py check --deploy --settings=elibrary.settings_production
```

- [ ] Migrations applied successfully
- [ ] Superuser created
- [ ] Static files collected
- [ ] Deployment checks passed

### Phase 7: Database Backup Strategy
- [ ] Create `backup_database.sh` script (✓ Created)
- [ ] Make script executable: `chmod +x backup_database.sh`
- [ ] Test backup: `./backup_database.sh`
- [ ] Verify backup: `ls -lah backups/`
- [ ] Test restore procedure
- [ ] Add to crontab: `0 2 * * * /path/to/backup_database.sh`

### Phase 8: Health Check Endpoint
- [ ] Add health check view to `catalog/views.py` (✓ Documented)
- [ ] Add URL path to `catalog/urls.py`
- [ ] Test: `curl http://localhost/health/`
- [ ] Verify returns JSON with status

---

## Day 8: Monitoring & Error Tracking

### Sentry Setup (Optional but Recommended)
```bash
# 1. Create Sentry account
# Visit: https://sentry.io/signup/

# 2. Create Django project
# Copy DSN from Sentry dashboard

# 3. Install SDK
pip install sentry-sdk

# 4. Update requirements.txt
echo "sentry-sdk==1.40.0" >> requirements.txt

# 5. Add to .env.production
SENTRY_DSN=https://your-key@sentry.io/project-id

# 6. Test Sentry integration
docker-compose exec web python manage.py shell
# In shell:
# from accounts.security import AuditLogger
# AuditLogger.log_security_event('Test event')

# 7. Verify in Sentry dashboard
```

- [ ] Sentry account created
- [ ] DSN obtained and added to `.env.production`
- [ ] SDK installed
- [ ] Test event sent and received
- [ ] Notification rules configured
- [ ] Team added to Sentry project

### Logging & Monitoring
- [ ] Django logs configured and writing to `/var/log/elibrary/django.log`
- [ ] Security logs writing to `/var/log/elibrary/security.log`
- [ ] Log rotation configured (max 10MB, 10 backups)
- [ ] Log files readable by application
- [ ] Monitoring alerts set up (optional)

### Health Checks
- [ ] Database health check passing
- [ ] Application health check responding
- [ ] Redis cache health check passing
- [ ] All container health checks green

---

## Security Verification

### SSL/TLS
- [ ] HTTPS redirect working
- [ ] SSL certificate valid and not self-signed
- [ ] Certificate chain correct
- [ ] Test: `curl -I https://yourdomain.com` returns 200
- [ ] SSL Labs score: A or better (https://www.ssllabs.com)

### Security Headers
Verify using: `curl -I https://yourdomain.com`

- [ ] `Strict-Transport-Security` present
- [ ] `X-Content-Type-Options: nosniff` present
- [ ] `X-Frame-Options: DENY` present
- [ ] `X-XSS-Protection` present
- [ ] `Content-Security-Policy` present
- [ ] `Referrer-Policy` present

### Application Security
- [ ] DEBUG = False
- [ ] ALLOWED_HOSTS set correctly
- [ ] SECRET_KEY is strong (>50 chars)
- [ ] CSRF protection enabled
- [ ] Rate limiting active
- [ ] Account lockout working (5 attempts)
- [ ] Email verification working
- [ ] 2FA working (if enabled)

---

## Performance Testing

### Response Times
- [ ] Homepage: < 500ms
- [ ] Search API: < 1 second
- [ ] Admin panel: < 800ms
- [ ] API endpoints: < 200ms

### Load Testing (Optional)
```bash
# Install ab (Apache Bench)
# Mac: brew install httpd
# Ubuntu: sudo apt-get install apache2-utils

# Test homepage (100 requests, 10 concurrent)
ab -n 100 -c 10 https://yourdomain.com/

# Test API (1000 requests, 50 concurrent)
ab -n 1000 -c 50 https://yourdomain.com/api/search/advanced/?q=test
```

- [ ] No significant performance degradation under load
- [ ] Database connection pool not exhausted
- [ ] Memory usage reasonable
- [ ] CPU usage reasonable

### Caching
- [ ] Redis cache working
- [ ] Cache hitting on subsequent requests
- [ ] Cache invalidation working
- [ ] Cache size reasonable

---

## Final Verification

### Container Status
```bash
docker-compose ps
```

- [ ] All containers running and healthy
- [ ] No containers restarting
- [ ] All ports bound correctly

### Application Testing
```bash
# Test HTTP redirect to HTTPS
curl -I http://yourdomain.com

# Test HTTPS
curl -I https://yourdomain.com

# Test API
curl https://yourdomain.com/api/search/advanced/

# Test admin panel
# Open https://yourdomain.com/admin/ in browser

# Test health endpoint
curl https://yourdomain.com/health/
```

- [ ] HTTP redirects to HTTPS
- [ ] HTTPS working correctly
- [ ] API responding with data
- [ ] Admin panel loads
- [ ] Health endpoint returning 200
- [ ] Database queries working
- [ ] Static files loading
- [ ] Media files accessible

### Database
```bash
# Check database status
docker-compose exec db pg_isready -U elibrary

# Check database size
docker-compose exec db psql -U elibrary -d elibrary -c "SELECT pg_size_pretty(pg_database_size('elibrary'));"

# List tables
docker-compose exec db psql -U elibrary -d elibrary -c "\dt"
```

- [ ] Database connection stable
- [ ] All tables present
- [ ] Data integrity verified
- [ ] Backups working

---

## Post-Deployment

### Monitoring
- [ ] Set up monitoring dashboard
- [ ] Configure alerts (Sentry, monitoring service)
- [ ] Set up uptime monitoring
- [ ] Configure log aggregation
- [ ] Set up performance monitoring

### Maintenance Schedule
- [ ] Daily: Monitor logs and alerts
- [ ] Weekly: Review security logs
- [ ] Monthly: Update dependencies
- [ ] Quarterly: Security audit
- [ ] As needed: Backup testing and restoration

### Documentation
- [ ] Update runbooks with production URLs
- [ ] Document incident response procedure
- [ ] Create escalation contacts list
- [ ] Document emergency shutdown procedure
- [ ] Create disaster recovery plan

### Team Notification
- [ ] Notify team of production deployment
- [ ] Share access credentials securely
- [ ] Schedule training if needed
- [ ] Document access procedures
- [ ] Create monitoring dashboard access

---

## Rollback Plan

If deployment fails or issues occur:

```bash
# 1. Stop production containers
docker-compose down

# 2. Restore from backup
docker-compose exec -T db psql -U elibrary elibrary < backups/elibrary_backup_latest.sql.gz

# 3. Restart with previous version
# Update Dockerfile or image tag to previous version
docker-compose up -d

# 4. Verify restoration
docker-compose logs web
```

- [ ] Backup restore procedure tested
- [ ] Rollback steps documented
- [ ] Escalation contacts identified
- [ ] Incident communication plan ready

---

## Sign-Off

- [ ] All checklist items completed
- [ ] Team lead approval obtained
- [ ] Security review passed
- [ ] Performance testing passed
- [ ] Stakeholders notified

---

**Production Deployment Status**: Ready to go live ✅

**Next Steps**:
1. Execute Day 7 deployment
2. Monitor for 24 hours
3. Collect feedback
4. Plan Day 9-10 improvements

**Support Contact**: [Add your contact info]
**Escalation Contact**: [Add escalation contact]
**Status Page**: [Add status page URL if available]
