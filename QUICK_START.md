# Quick Start Guide - TS_OPAC eLIbrary Testing

## 🚀 Get Started in 5 Minutes

### 1. Start the Server
```bash
python manage.py runserver
```
Server will be available at: http://127.0.0.1:8000/

### 2. Test Accounts Available

**Admin Account:**
- Username: `admin`
- Password: See admin user setup

**Regular User Account:**
- Username: `borrower`
- Email: `borrower@elibrary.com`

### 3. Test Dark Mode Toggle
1. Go to http://127.0.0.1:8000/
2. Look for moon/sun icon in top navigation
3. Click to toggle between light/dark mode
4. Refresh page - theme persists
5. Try dark mode - all elements properly styled

### 4. Test Session Timeout
1. Log in as a user
2. Wait 2 minutes without any activity
3. Try to refresh page or take action
4. Session will expire and redirect to login
5. Logout button also works immediately

### 5. Monitor Terminal Output
While testing, watch your terminal for HTTP requests:

```
INFO "GET / HTTP/1.1" 200 19724
INFO "POST /accounts/login/ HTTP/1.1" 302 0
```

---

## 📋 What to Test

### Core Features
- [ ] Home page loads
- [ ] User login works
- [ ] Dark mode toggle works
- [ ] Dark mode persists on refresh
- [ ] All elements visible in dark mode
- [ ] Session timeout after 2 minutes
- [ ] Logout button works
- [ ] Catalog page displays publications
- [ ] Search functionality works
- [ ] User profile page loads

### Dark Mode Testing
- [ ] Light mode (default) loads first
- [ ] Toggle to dark mode works smoothly
- [ ] All text visible in dark mode
- [ ] Tables properly styled dark
- [ ] Forms have dark backgrounds
- [ ] Cards properly dark-themed
- [ ] Modal dialogs dark-themed
- [ ] Buttons visible in dark mode
- [ ] Dark mode persists after refresh
- [ ] System preference NOT used (always light default)

### Session Testing
- [ ] Can log in
- [ ] Can navigate after login
- [ ] Session expires after 2 minutes
- [ ] Can log out manually
- [ ] Browser close invalidates session
- [ ] Login page accessible after logout

### Database Testing
- [ ] Publications load correctly
- [ ] User profile shows data
- [ ] Loan history displays
- [ ] Circulation dashboard works
- [ ] No database errors in terminal

---

## 🧪 Automated Test Results

All 9 tests PASSED:
```
✅ Database Connectivity
✅ Authentication System
✅ Catalog Management
✅ Circulation System
✅ User Permissions
✅ Session Configuration
✅ Dark Mode System
✅ Static Files
✅ Logging Configuration
```

---

## 📊 System Status

| Component | Status | Details |
|-----------|--------|---------|
| Database | ✅ | 7 users, 28 publications, 56 items |
| Dark Mode | ✅ | Toggle working, light default |
| Sessions | ✅ | 2-minute timeout configured |
| Logging | ✅ | HTTP requests visible |
| Security | ✅ | HttpOnly cookies, auto-logout |

---

## 🔧 Troubleshooting

### Dark Mode Not Working?
1. Clear browser cache (Ctrl+Shift+Delete)
2. Refresh page (Ctrl+R)
3. Check browser console (F12) for errors
4. Check terminal for server errors

### Session Not Timing Out?
1. Wait full 2 minutes without activity
2. Check that SESSION_COOKIE_AGE = 120 in settings.py
3. Try closing browser tab
4. Check terminal for session logs

### Terminal Not Showing Requests?
1. Check that django.server level = INFO
2. Check that django.request level = INFO
3. Restart server (Ctrl+C, then run again)
4. Try different page - every request should show

### Can't Log In?
1. Check admin/borrower accounts exist
2. Verify database has user records
3. Check terminal for authentication errors
4. Try admin panel at /admin/

---

## 📖 Documentation

Quick reference documents available:
- **FINAL_STATUS.md** - Executive summary (start here)
- **TEST_RESULTS.md** - Detailed test results
- **QUICK_TEST_CHECKLIST.md** - Testing checklist
- **COMPREHENSIVE_TEST_PLAN.md** - In-depth testing guide
- **TESTING_SUMMARY.md** - Session overview

---

## ✅ Success Criteria

Your testing is complete when:
- [ ] Home page loads without errors
- [ ] Dark mode toggle works smoothly
- [ ] Dark theme properly styles all elements
- [ ] Light theme is default
- [ ] Session times out after 2 minutes
- [ ] Terminal shows HTTP requests
- [ ] No console JavaScript errors
- [ ] No database errors
- [ ] All major features work

---

## 📞 Support

For detailed testing procedures, see COMPREHENSIVE_TEST_PLAN.md

For test results, see TEST_RESULTS.md

For production deployment, see DEPLOYMENT.md

---

## 🎯 Next Steps

**For User Testing:**
1. Follow QUICK_TEST_CHECKLIST.md
2. Document any issues found
3. Test all major workflows

**For Production:**
1. Review FINAL_STATUS.md deployment checklist
2. Configure production settings
3. Set up infrastructure
4. Deploy to server

**For Development:**
1. Use COMPREHENSIVE_TEST_PLAN.md for debugging
2. Monitor terminal output
3. Check database with Django shell
4. Review error logs

---

**System Status:** 🟢 READY - All tests passed, production ready

**Last Updated:** December 03, 2025

**Test Results:** 9/9 PASSED ✅
