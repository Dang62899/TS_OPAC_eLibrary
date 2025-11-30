# Pre-Deployment Checklist

Use this checklist before deploying TS_OPAC_eLibrary to production.

## Code Quality & Testing

- [ ] All flake8 violations resolved (`flake8 --count` = 0)
- [ ] All pytest tests passing
- [ ] No syntax errors in Python files
- [ ] Code reviewed by team member
- [ ] All imports are working (`python manage.py shell` can import models)
- [ ] Black formatting applied (`black --check .` passes)
- [ ] No debug print statements in code

## Django Configuration

- [ ] `ELIBRARY_PRODUCTION=True` configured in environment
- [ ] `ELIBRARY_DEBUG=False` configured
- [ ] Secure `ELIBRARY_SECRET_KEY` generated (>50 characters)
- [ ] `ELIBRARY_ALLOWED_HOSTS` set with actual domain(s)
- [ ] `DATABASES` configured with PostgreSQL (not SQLite)
- [ ] `ALLOWED_HOSTS` matches `ELIBRARY_ALLOWED_HOSTS`
- [ ] `CSRF_TRUSTED_ORIGINS` includes all domains
- [ ] Email backend configured for password resets
- [ ] Django system check passes: `python manage.py check --deploy`
- [ ] No security warnings from `python manage.py check --deploy` (after hardening)

## Security

- [ ] SSL/TLS certificate installed (Let's Encrypt recommended)
- [ ] HSTS enabled in nginx config
- [ ] Security headers configured:
  - [ ] X-Frame-Options: SAMEORIGIN
  - [ ] X-Content-Type-Options: nosniff
  - [ ] X-XSS-Protection: 1; mode=block
  - [ ] Referrer-Policy: strict-origin-when-cross-origin
- [ ] Content-Security-Policy header set appropriately
- [ ] SECURE_SSL_REDIRECT=True
- [ ] SESSION_COOKIE_SECURE=True
- [ ] CSRF_COOKIE_SECURE=True
- [ ] SECURE_HSTS_SECONDS set to 31536000 (1 year)
- [ ] Firewall configured (allow only 22, 80, 443)
- [ ] SSH key-based authentication enabled
- [ ] SSH password authentication disabled
- [ ] Database password is strong (min 32 characters)
- [ ] Redis password is strong (min 32 characters)

## Database

- [ ] PostgreSQL installed and configured
- [ ] Database user created with limited privileges
- [ ] All migrations applied: `python manage.py migrate`
- [ ] Database backups configured (automated daily)
- [ ] Backup retention policy defined (minimum 30 days)
- [ ] Backup restoration procedure tested
- [ ] Database connection timeout configured
- [ ] Connection pooling configured (for high traffic)

## Infrastructure

- [ ] Server specs meet requirements (2 CPU, 4GB RAM, 50GB disk)
- [ ] Operating system is up to date
- [ ] Docker and Docker Compose installed (if using Docker)
- [ ] System packages updated: `apt update && apt upgrade -y`
- [ ] Python 3.14+ installed
- [ ] Nginx installed and configured
- [ ] Redis installed and configured
- [ ] Gunicorn installed (or using Docker)
- [ ] Systemd services created and enabled (if manual deployment)

## Performance & Caching

- [ ] Static files collected: `python manage.py collectstatic --noinput`
- [ ] Redis configured as cache backend
- [ ] Cache timeout policies set appropriately
- [ ] Database query optimization verified (no N+1 queries)
- [ ] Nginx gzip compression enabled
- [ ] Nginx caching headers configured
- [ ] CDN configured (if using for static files)
- [ ] Database connection pooling enabled

## Monitoring & Logging

- [ ] Application logging configured
- [ ] Error logging to file system (with rotation)
- [ ] Sentry configured for error tracking (recommended)
- [ ] New Relic or similar APM installed (optional)
- [ ] Log rotation configured (logrotate)
- [ ] Uptime monitoring configured (StatusCake, UptimeRobot, etc.)
- [ ] Alert thresholds set:
  - [ ] CPU usage > 80%
  - [ ] Memory usage > 85%
  - [ ] Disk usage > 90%
  - [ ] Response time > 2 seconds
  - [ ] Error rate > 1%
- [ ] Health check endpoint working: `/health`
- [ ] Metrics dashboard accessible

## Load Testing & Performance

- [ ] Load test simulating 100+ concurrent users passed
- [ ] Response times acceptable (<500ms median)
- [ ] No memory leaks detected during load test
- [ ] Database query performance acceptable
- [ ] Static file delivery optimization verified
- [ ] Celery workers handling task queue efficiently

## Backup & Disaster Recovery

- [ ] Database backup procedure tested
- [ ] Application code version control verified
- [ ] Full system backup image created
- [ ] Disaster recovery plan documented
- [ ] Recovery time objective (RTO) defined
- [ ] Recovery point objective (RPO) defined
- [ ] Backup restoration tested from cold backup

## Deployment Process

- [ ] Deployment plan documented
- [ ] Rollback procedure documented
- [ ] Team trained on deployment process
- [ ] Maintenance window scheduled (if needed)
- [ ] Change management approval obtained
- [ ] User notification plan created
- [ ] DNS records verified and pointing to server
- [ ] Staging environment tested (mirrors production)

## Post-Deployment Verification

- [ ] Application loading at domain: `curl https://yourdomain.com`
- [ ] Admin panel accessible: `https://yourdomain.com/admin/`
- [ ] User registration working
- [ ] Login functionality working
- [ ] Database operations working (read/write)
- [ ] Celery tasks running and completing
- [ ] Email functionality working (test sending password reset)
- [ ] Static files loading correctly
- [ ] Media files accessible
- [ ] SSL certificate valid and auto-renewing
- [ ] Logs being written without errors
- [ ] Performance acceptable (response times)
- [ ] No database connection errors
- [ ] Rate limiting working correctly
- [ ] Security headers present: `curl -I https://yourdomain.com | grep -i security`

## SSL/TLS Verification

- [ ] SSL certificate installed and valid
- [ ] Certificate not expired
- [ ] Certificate auto-renewal configured
- [ ] Certificate chain complete (fullchain.pem)
- [ ] HTTPS enforced (HTTP redirects to HTTPS)
- [ ] SSL Labs A rating achieved
- [ ] TLS 1.2+ only (TLS 1.0/1.1 disabled)
- [ ] Strong cipher suites configured

## Documentation

- [ ] Deployment guide updated with production details
- [ ] Admin procedures documented
- [ ] Backup procedures documented
- [ ] Update procedures documented
- [ ] Emergency procedures documented
- [ ] Architecture diagram created
- [ ] API documentation updated (if applicable)
- [ ] Team trained on operation procedures

## Final Sign-Off

- [ ] Project owner approval: _________________ Date: _______
- [ ] Operations manager approval: _________________ Date: _______
- [ ] Security team approval: _________________ Date: _______
- [ ] Deployment scheduled by: _________________ Date: _______
- [ ] Deployed by: _________________ Date: _______
- [ ] Verified by: _________________ Date: _______

## Post-Go-Live (48 hours)

- [ ] No critical errors in logs
- [ ] Performance metrics stable
- [ ] User feedback positive
- [ ] Backup runs completed successfully
- [ ] Monitoring alerts functioning correctly
- [ ] Team on-call procedures verified
- [ ] Documentation updated with any issues encountered

---

## Quick Reference Commands

```bash
# Health check
curl https://yourdomain.com/health

# View logs
docker-compose logs -f web  # Docker
sudo journalctl -u elibrary -f  # Traditional

# Check Django system
python manage.py check --deploy

# Run backups
docker-compose exec db pg_dump -U elibrary_user elibrary_db > backup.sql
# or: pg_dump -U elibrary_user -h localhost elibrary_db > backup.sql

# Restart services
docker-compose restart web  # Docker
sudo systemctl restart elibrary  # Traditional

# Update application
git pull && python manage.py migrate && python manage.py collectstatic --noinput

# Monitor performance
docker stats  # Docker
top  # Traditional

# Check SSL certificate
openssl s_client -connect yourdomain.com:443
```

---

**Completed:** _____________ (date)  
**Deployed to:** _____________ (environment)  
**Notes:** _________________________________

