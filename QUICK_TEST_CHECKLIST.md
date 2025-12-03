# TS_OPAC eLIBrary - Quick Testing Checklist

**Date:** December 3, 2025  
**Tester:** _______________  
**Status:** In Progress

---

## PHASE 1: AUTHENTICATION (5-10 min)

### Login/Logout
- [ ] Navigate to http://127.0.0.1:8000/
- [ ] Click "Login"
- [ ] Enter valid credentials
  - [ ] **Terminal Shows:** `POST /accounts/login/ HTTP/1.1" 302`
  - [ ] **Result:** Redirected to home page ✅
- [ ] Verify user name appears in navbar
- [ ] Click "Logout"
  - [ ] **Terminal Shows:** `POST /accounts/logout/ HTTP/1.1" 302`
  - [ ] **Result:** Logged out, redirected to home ✅

### Session Timeout (2 minutes)
- [ ] Login again
- [ ] Note the time
- [ ] **Wait 2 minutes without clicking anything**
- [ ] Try to navigate somewhere
  - [ ] **Result:** Logged out automatically ✅
  - [ ] Redirected to login page ✅

---

## PHASE 2: CATALOG BROWSING (5-10 min)

### Home Page
- [ ] **Terminal Shows:** `GET / HTTP/1.1" 200`
- [ ] Publications display ✅
- [ ] Images load ✅
- [ ] Titles readable ✅

### Browse Publications
- [ ] Click "Search Catalog"
  - [ ] **Terminal Shows:** `GET /catalog/ HTTP/1.1" 200`
- [ ] See list of publications ✅
- [ ] Click on a publication
  - [ ] **Terminal Shows:** `GET /catalog/publication/X/ HTTP/1.1" 200`
- [ ] Detail page loads ✅
- [ ] All information shows:
  - [ ] Title ✅
  - [ ] Author ✅
  - [ ] ISBN ✅
  - [ ] Description ✅
  - [ ] Cover image ✅

### Search Functionality
- [ ] Click "Search Catalog" again
- [ ] Search by title (e.g., "Django")
  - [ ] **Terminal Shows:** `GET /catalog/search/?q=Django HTTP/1.1" 200`
- [ ] Results display ✅
- [ ] Search by author
  - [ ] Results accurate ✅

### Browse by Category
- [ ] Click "Browse by Author"
  - [ ] **Terminal Shows:** `GET /catalog/browse-by-author/ HTTP/1.1" 200`
- [ ] Author list loads ✅
- [ ] Click an author
  - [ ] Publications by that author show ✅

---

## PHASE 3: DARK MODE & UI (5 min)

### Toggle Dark Mode
- [ ] Locate moon icon (🌙) in top-right navbar
- [ ] Click it
  - [ ] Colors change to dark ✅
  - [ ] Text remains readable ✅
  - [ ] **Terminal:** No HTTP request (client-side only) ✅
- [ ] Tables appear dark (not bright white) ✅
- [ ] Form inputs appear dark ✅
- [ ] Buttons visible ✅
- [ ] Toggle back to light mode
  - [ ] Colors change to light ✅
  - [ ] Back to original appearance ✅

### Refresh Page (Test Persistence)
- [ ] Toggle to dark mode
- [ ] Refresh page (F5)
  - [ ] **Terminal Shows:** `GET / HTTP/1.1" 200`
  - [ ] Dark mode persists ✅ (saved in browser)
- [ ] Toggle to light mode
- [ ] Refresh page
  - [ ] Light mode persists ✅

### Text Alignment
- [ ] Check table headers centered ✅
- [ ] Check card titles left-aligned ✅
- [ ] Check form labels properly spaced ✅
- [ ] Check buttons aligned ✅

---

## PHASE 4: CIRCULATION (If Admin/Staff Account) (10 min)

### Checkout
- [ ] Login as admin or staff user
- [ ] Navigate to Checkout
  - [ ] **Terminal Shows:** `GET /circulation/checkout/ HTTP/1.1" 200`
- [ ] Enter ISBN or scan barcode
- [ ] Select borrower
- [ ] Click "Checkout"
  - [ ] **Terminal Shows:** `POST /circulation/checkout/ HTTP/1.1" 302`
  - [ ] **Result:** Success message ✅
  - [ ] Book marked as checked out ✅

### Checkin
- [ ] Go to Checkin page
  - [ ] **Terminal Shows:** `GET /circulation/checkin/ HTTP/1.1" 200`
- [ ] Enter ISBN of returned book
- [ ] Click "Checkin"
  - [ ] **Terminal Shows:** `POST /circulation/checkin/ HTTP/1.1" 302`
  - [ ] **Result:** Success message ✅
  - [ ] Book marked as returned ✅

### Dashboard
- [ ] Click "Dashboard"
  - [ ] **Terminal Shows:** `GET /circulation/dashboard/ HTTP/1.1" 200`
- [ ] Statistics load ✅
- [ ] Cards show:
  - [ ] Total publications ✅
  - [ ] Total users ✅
  - [ ] Active loans ✅
  - [ ] Overdue items ✅

---

## PHASE 5: TERMINAL MONITORING (2 min)

### Watch Terminal Output
During testing above, you should see patterns like:

```
✅ GOOD OUTPUT:
GET / HTTP/1.1" 200
GET /static/css/custom.css HTTP/1.1" 304
GET /catalog/ HTTP/1.1" 200
POST /accounts/login/ HTTP/1.1" 302
GET /circulation/dashboard/ HTTP/1.1" 200

⚠️ WARNING (but expected):
GET /.well-known/appspecific/com.chrome.devtools.json HTTP/1.1" 404
(This is normal - just Chrome looking for dev tools config)

❌ PROBLEMS (investigate if you see these):
HTTP/1.1" 500  (Server error)
HTTP/1.1" 403  (Forbidden - permission denied)
```

- [ ] Seeing appropriate status codes (200, 302) ✅
- [ ] No unexpected 500 errors ✅
- [ ] No permission errors (403) ✅

---

## PHASE 6: ERROR HANDLING (3 min)

### 404 Error
- [ ] Navigate to non-existent page: `localhost:8000/nonexistent/`
  - [ ] **Terminal Shows:** `HTTP/1.1" 404`
  - [ ] **Result:** Friendly error page ✅

### Missing Login
- [ ] Logout (if logged in)
- [ ] Try accessing protected page: `/circulation/dashboard/`
  - [ ] **Terminal Shows:** `HTTP/1.1" 302` (redirect to login)
  - [ ] **Result:** Redirected to login ✅

### Invalid Search
- [ ] Search for very specific term that doesn't exist
  - [ ] **Result:** "No results found" message ✅

---

## PHASE 7: BROWSER CONSOLE (2 min)

### Check for JavaScript Errors
- [ ] Press F12 (Developer Tools)
- [ ] Go to "Console" tab
- [ ] Check for red errors
  - [ ] **Expected:** No red errors ✅
  - [ ] Blue warnings okay (not errors) ✅
- [ ] See dark mode toggle message ✅
  - [ ] Look for: `Toggling theme from light to dark`

---

## SUMMARY

### Total Items: 50+
- [ ] **Passed:** _____ / 50+
- [ ] **Failed:** _____
- [ ] **Blocked:** _____

### Issues Found:
```
[List any problems discovered during testing]

Example:
- Issue #1: [Description]
- Issue #2: [Description]
```

### Terminal Output Assessment:
- [ ] Shows all HTTP requests ✅
- [ ] No unexpected errors ✅
- [ ] Response times acceptable ✅

### Overall Status:
- [ ] **✅ READY FOR PRODUCTION**
- [ ] **⚠️ NEEDS FIXES** (list issues above)
- [ ] **❌ CRITICAL ISSUES** (list below)

### Critical Issues (if any):
```
[List only critical issues that block functionality]
```

---

## QUICK REFERENCE - Expected Terminal Output

| Action | Expected Terminal Output |
|--------|--------------------------|
| Visit home page | `GET / HTTP/1.1" 200` |
| Login | `POST /accounts/login/ HTTP/1.1" 302` |
| Logout | `POST /accounts/logout/ HTTP/1.1" 302` |
| Browse catalog | `GET /catalog/ HTTP/1.1" 200` |
| Search | `GET /catalog/search/?q=... HTTP/1.1" 200` |
| View publication | `GET /catalog/publication/1/ HTTP/1.1" 200` |
| Access dashboard | `GET /circulation/dashboard/ HTTP/1.1" 200` |
| Checkout | `POST /circulation/checkout/ HTTP/1.1" 302` |
| Checkin | `POST /circulation/checkin/ HTTP/1.1" 302` |
| Dark mode toggle | *(No HTTP - client-side only)* |
| Refresh page | `GET / HTTP/1.1" 200` or `304` |

---

## SIGN-OFF

**Date Completed:** _______________

**Tested By:** _______________

**Approved By:** _______________

**Comments:**
```
[Any additional notes or observations]
```

---

**Good luck with testing!** 🧪✅
