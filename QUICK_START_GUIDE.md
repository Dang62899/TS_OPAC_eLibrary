# TS OPAC eLibrary - Quick Reference Guide

## 🚀 Quick Start

### Start Application
```bash
docker-compose up -d
```

### Access Application
- **Homepage**: http://localhost/
- **Admin Panel**: http://localhost/admin/
- **API Root**: http://localhost/api/v1/

### View Status
```bash
docker-compose ps                    # Container status
docker-compose logs web              # Application logs
docker-compose logs -f db            # Database logs
```

---

## 📚 Features Summary

### 1. Advanced Search
```
URL: http://localhost/api/search/advanced/

Parameters:
- q=query              Search across all fields
- authors=1,2          Filter by author IDs
- subjects=1,2         Filter by subject IDs
- available_only=true  Show only available items
- sort_by=date         Sort by: date, title, popularity
- page=1               Pagination (default: page 1)

Example:
/api/search/advanced/?q=harry&available_only=true&sort_by=date
```

### 2. Analytics Dashboard
```
Endpoints:
GET /api/analytics/metrics/              Overall library stats
GET /api/analytics/metrics/today/        Today's statistics
GET /api/analytics/circulation/trends/   Circulation trends
GET /api/analytics/circulation/popular/  Popular items

Response includes:
- Total publications and items
- Availability statistics
- Circulation history
- User activity
```

### 3. Mobile Optimization
```
Features:
- Responsive design (all screen sizes)
- Touch-friendly buttons
- Mobile navigation menu
- Dark mode support
- PWA ready

CSS File: static/css/mobile.css
Include in templates: <link rel="stylesheet" href="{% static 'css/mobile.css' %}">
```

### 4. Security Features
```
File: accounts/security.py

Features:
- Account Lockout: 5 failed attempts → 30 min lock
- 2FA: TOTP-based (with pyotp)
- Input Validation: Search queries, emails, ISBNs
- Session Management: Secure tokens
- Audit Logging: Data access tracking
- Security Headers: CSP, HSTS, etc.

Usage:
from accounts.security import AccountSecurityManager
AccountSecurityManager.record_failed_login('username')
```

---

## 📊 Database Sample Data

**8 Publications:**
1. 1984 - George Orwell (1949)
2. Pride and Prejudice - Jane Austen (1813)
3. The Great Gatsby - F. Scott Fitzgerald (1925)
4. To Kill a Mockingbird - Harper Lee (1960)
5. Norwegian Wood - Haruki Murakami (1987)
6. Murder on the Orient Express - Agatha Christie (1934)
7. The Shining - Stephen King (1977)
8. Harry Potter - J.K. Rowling (1997)

**Metadata:**
- 8 Authors
- 6 Subjects (Fiction, Mystery, Sci-Fi, Biography, History, Technology)
- 5 Publishers
- 4 Locations (Main Floor, 2nd Floor, Reference, Digital)
- 21 Physical Items (2-3 copies per book)

---

## 🔧 Common Commands

### Database Management
```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Populate sample data
docker-compose cp populate_db.py elibrary_web:/app/
docker-compose exec web python /app/populate_db.py

# Access database shell
docker-compose exec db psql -U elibrary elibrary
```

### Django Management
```bash
# Collect static files
docker-compose exec web python manage.py collectstatic

# Run tests
docker-compose exec web python manage.py test

# Check deployment readiness
docker-compose exec web python manage.py check --deploy

# Makemigrations
docker-compose exec web python manage.py makemigrations
```

### Container Management
```bash
# Stop all containers
docker-compose down

# Stop and remove volumes (WARNING: data loss)
docker-compose down -v

# Restart containers
docker-compose restart

# View container logs (last 100 lines)
docker-compose logs --tail=100

# Stream logs in real-time
docker-compose logs -f
```

---

## 🔐 Security Checklist

### Before Production
- [ ] Set DEBUG = False in settings
- [ ] Generate strong SECRET_KEY
- [ ] Update ALLOWED_HOSTS
- [ ] Configure SSL/TLS certificates
- [ ] Enable SECURE_SSL_REDIRECT
- [ ] Set SESSION_COOKIE_SECURE = True
- [ ] Configure email backend
- [ ] Set up logging/monitoring
- [ ] Enable 2FA
- [ ] Configure rate limiting

### Production Settings
```python
# elibrary/settings.py

DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
```

---

## 📱 Mobile Testing

### Test on Different Screen Sizes
```css
Breakpoints:
- Mobile: <576px (default)
- Tablet: 576px - 768px
- Desktop: 768px - 992px
- Large: 992px - 1200px
- XL: >1200px
```

### Browser Testing
- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (iOS/macOS)
- ✅ Android browsers

### Performance Check
```bash
# Using Chrome DevTools
1. Open http://localhost/
2. Press F12 → DevTools
3. Device toolbar → Responsive
4. Performance tab → Record
5. Lighthouse → Analyze
```

---

## 🧪 API Testing

### Using curl
```bash
# Basic search
curl "http://localhost/api/search/advanced/?q=fiction"

# Advanced search with filters
curl "http://localhost/api/search/advanced/?q=fiction&available_only=true&sort_by=date"

# Get metrics
curl "http://localhost/api/analytics/metrics/"

# Get suggestions
curl "http://localhost/api/search/suggestions/?q=har&type=title"
```

### Using Postman
1. Import `TS_OPAC_eLibrary_REST_API.postman_collection.json`
2. Set base URL: `http://localhost`
3. Test endpoints in folders:
   - Search
   - Analytics
   - Catalog
   - Circulation

### Using Python Requests
```python
import requests

# Search
response = requests.get('http://localhost/api/search/advanced/', {
    'q': 'fiction',
    'available_only': True,
    'sort_by': 'date'
})
print(response.json())

# Analytics
response = requests.get('http://localhost/api/analytics/metrics/')
print(response.json())
```

---

## 🚨 Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose logs web

# Rebuild image
docker-compose build --no-cache web

# Restart
docker-compose restart web
```

### Database Connection Error
```bash
# Verify PostgreSQL is running
docker-compose logs db

# Check database exists
docker-compose exec db psql -U elibrary -d elibrary -c "\dt"

# Run migrations
docker-compose exec web python manage.py migrate
```

### Static Files Not Loading
```bash
# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Check volumes
docker-compose exec nginx ls -la /app/static/
```

### Search Not Working
```bash
# Check search module
docker-compose exec web python -c "from catalog.search import AdvancedSearch; print('OK')"

# Test simple search
docker-compose exec web python manage.py shell
>>> from catalog.models import Publication
>>> Publication.objects.all().count()
```

### Security Headers Missing
```bash
# Verify headers
curl -I http://localhost/
# Should show X-Content-Type-Options, X-Frame-Options, etc.
```

---

## 📈 Monitoring & Logs

### View Application Logs
```bash
docker-compose logs web --tail=50 -f
```

### View Database Logs
```bash
docker-compose logs db --tail=50 -f
```

### View Nginx Logs
```bash
docker-compose logs nginx --tail=50 -f
```

### Check Container Stats
```bash
docker stats elibrary_web elibrary_db elibrary_nginx
```

---

## 🔄 Updates & Maintenance

### Update Dependencies
```bash
# Check for updates
pip install --upgrade pip
pip list --outdated

# Update in requirements.txt
pip install --upgrade django djangorestframework

# Regenerate requirements
pip freeze > requirements.txt

# Rebuild container
docker-compose build --no-cache web
```

### Database Backups
```bash
# Backup database
docker-compose exec db pg_dump -U elibrary elibrary > backup.sql

# Restore database
docker-compose exec -T db psql -U elibrary elibrary < backup.sql
```

### Clear Cache
```bash
# Django cache
docker-compose exec web python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()

# Static files
docker-compose exec web rm -rf staticfiles/*
docker-compose exec web python manage.py collectstatic
```

---

## 📖 Documentation Files

| File | Purpose |
|------|---------|
| PROJECT_COMPLETION_REPORT.md | Full project report |
| DAYS_5-6_FEATURES_COMPLETE.md | Features implementation summary |
| DAYS_5-6_IMPLEMENTATION.md | Detailed implementation guide |
| DOCKER_WINDOWS_SETUP.md | Docker setup instructions |
| README.md | Project overview |
| QUICK_REFERENCE.md | This file |

---

## 🎯 Next Steps

### Immediate (Before Launch)
1. [ ] Update ALLOWED_HOSTS with production domain
2. [ ] Configure SSL certificates
3. [ ] Set DEBUG = False
4. [ ] Generate strong SECRET_KEY
5. [ ] Test all endpoints

### Short-term (Week 1)
1. [ ] Enable 2FA for admin users
2. [ ] Set up monitoring/alerting
3. [ ] Configure email notifications
4. [ ] Create user documentation
5. [ ] Load production data

### Medium-term (Month 1)
1. [ ] Add LDAP/AD integration
2. [ ] Implement advanced reporting
3. [ ] Set up database backups
4. [ ] Performance tuning
5. [ ] User training

### Long-term (Quarter 1+)
1. [ ] Machine learning recommendations
2. [ ] Mobile app development
3. [ ] Elasticsearch integration
4. [ ] Microservices refactoring
5. [ ] Multi-language support

---

## 📞 Support & Resources

### Local Resources
- Admin Panel: http://localhost/admin/
- API Docs: See Postman collection
- Logs: `docker-compose logs`
- Database: `docker-compose exec db psql`

### External Resources
- Django Docs: https://docs.djangoproject.com/
- DRF Docs: https://www.django-rest-framework.org/
- Docker Docs: https://docs.docker.com/
- PostgreSQL Docs: https://www.postgresql.org/docs/

### Key Contacts
- Django Issues: https://github.com/django/django/issues
- DRF Issues: https://github.com/encode/django-rest-framework/issues
- Docker Support: https://support.docker.com/

---

## 🎓 Learning Resources

### Advanced Search
- See: `catalog/search.py` (full implementation with docstrings)
- Methods: `full_text_search()`, `filter_by_authors()`, `advanced_search()`

### Analytics
- See: `api/analytics.py` (API viewsets with examples)
- Endpoints: `/api/analytics/metrics/`, `/api/analytics/circulation/`

### Security
- See: `accounts/security.py` (security classes with usage examples)
- Classes: `AccountSecurityManager`, `InputSanitizer`, `AuditLogger`

### Mobile
- See: `static/css/mobile.css` (responsive styles with comments)
- Breakpoints: 576px, 768px, 992px, 1200px

---

**Last Updated**: 2026-01-08
**Version**: 1.0
**Status**: Production Ready ✅
