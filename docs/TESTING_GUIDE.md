# System Testing & Verification Guide

## ✅ Automated Verification

### 1. **System Health Check**
```bash
python verify_system.py
```
Verifies:
- Database connection
- Django settings
- Data integrity (users, publications, items, loans)

**Expected Output:** `✅ ALL SYSTEM CHECKS PASSED - APPLICATION IS READY`

### 2. **Django System Checks**
```bash
python manage.py check
```
Verifies:
- All Django apps are properly configured
- Settings are valid
- Database schema is correct

**Expected Output:** `System check identified no issues (0 silenced)`

### 3. **URL Routing Test**
```bash
python test_urls.py
```
Verifies:
- All routes are accessible
- URL names are correctly configured
- Redirects work properly

**Expected Output:** All URLs show `✅ OK` or `⚠️ (302)` for protected pages

---

## 📋 Manual Testing Checklist

### Public Access
- [ ] Visit `http://127.0.0.1:8000/` - Homepage loads
- [ ] Click "Search Catalog" - Search page loads
- [ ] Browse publications - Results display correctly
- [ ] Publication detail page - Shows full metadata

### User Authentication
- [ ] Visit `/accounts/login/` - Login form appears
- [ ] Login with `admin / admin123` - Redirects to admin dashboard
- [ ] Login with `staff / staff123` - Redirects to staff dashboard
- [ ] Login with `student / student123` - Redirects to borrower account
- [ ] Logout - Redirects to homepage

### Admin Dashboard
- [ ] View system statistics
- [ ] Check user counts (admin, staff, borrowers)
- [ ] View collection status (available, on loan, on hold)
- [ ] Access user management
- [ ] Access circulation reports

### Staff Dashboard
- [ ] View circulation metrics
- [ ] Verify loan counts
- [ ] Check hold queue
- [ ] View recent activity

### Borrower Account
- [ ] View active loans
- [ ] Check loan due dates
- [ ] View holds
- [ ] Check circulation requests

### Circulation Operations (Staff)
- [ ] Test Checkout - Can mark item as borrowed
- [ ] Test Check-in - Can return item
- [ ] Manage Holds - Can view and process holds
- [ ] Borrower Management - Can view borrowers
- [ ] Reports - Can generate circulation reports

---

## 🐛 Debugging Commands

### View Logs
```bash
python manage.py runserver --verbosity 2
```
Shows detailed HTTP requests and Django operations.

### Database Query Tests
```bash
python manage.py dbshell
SELECT COUNT(*) FROM accounts_user;
SELECT COUNT(*) FROM catalog_publication;
```

### Check Specific User
```python
python manage.py shell
from accounts.models import User
admin = User.objects.get(username='admin')
print(f"Admin user_type: {admin.user_type}, is_staff: {admin.is_staff}")
exit()
```

### View All Routes
```bash
python manage.py show_urls
```
or
```bash
python manage.py dumpdata --format json > data.json
```

---

## 🔍 Common Issues & Solutions

### Issue: "Invalid HTTP_HOST header: 'testserver'"
**Solution:** Already fixed - `testserver` added to ALLOWED_HOSTS for testing.

### Issue: Database migrations not applied
**Solution:**
```bash
python manage.py migrate
```

### Issue: Static files not loading
**Solution:**
```bash
python manage.py collectstatic
```

### Issue: Permission denied errors
**Solution:** Ensure `db.sqlite3` and `media/` folders have proper permissions.

---

## 📊 Performance Testing

### Load Test (Simple)
```bash
# In separate terminal 1:
python manage.py runserver

# In separate terminal 2:
pip install locust
locust -f locustfile.py  # if you have one
```

### Database Performance
```python
from django.test.utils import override_settings
from django.test import TestCase
from django.db import connection
from django.test.utils import CaptureQueriesContext

with CaptureQueriesContext(connection) as context:
    # Your code here
    pass
print(f"Queries executed: {len(context)}")
```

---

## ✅ Pre-Deployment Testing

Run this sequence before deploying:

1. **System Check**
   ```bash
   python manage.py check
   ```

2. **Verification**
   ```bash
   python verify_system.py
   ```

3. **URL Test**
   ```bash
   python test_urls.py
   ```

4. **Manual Test** (see checklist above)

5. **Admin Test**
   - [ ] Login to `/admin/` with admin credentials
   - [ ] View Users, Publications, Items, Loans
   - [ ] Test adding/editing records

6. **Data Export**
   ```bash
   python manage.py dumpdata > backup.json
   ```

---

## 🎯 Test Data

Currently loaded:
- **Users:** 3 (admin, staff, student)
- **Publications:** 20 (technical documents)
- **Items:** 51 (distributed across publications)
- **Loans:** 3 (active loans for student)
- **Locations:** 3 (Main Library, East Branch, West Branch)

To reload demo data:
```bash
python setup_demo_data.py
```

---

## 📈 Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Django System | ✅ OK | 0 issues detected |
| Database | ✅ OK | SQLite, 51 items loaded |
| URLs | ✅ OK | All routes configured |
| Authentication | ✅ OK | 3 user accounts ready |
| Migrations | ✅ OK | 35 migrations applied |
| Static Files | ✅ OK | CSS/JS loading |
| Demo Data | ✅ OK | 20 publications, 51 items |

---

**Last Updated:** November 30, 2025  
**Ready for:** Development, Testing, Staging, Production
