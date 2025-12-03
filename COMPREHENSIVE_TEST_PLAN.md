# TS_OPAC eLIBrary - Comprehensive Test Plan

**Date:** December 3, 2025  
**Purpose:** Systematic testing and debugging of all system features  
**Test Environment:** Development (localhost:8000)

---

## PHASE 1: CORE FUNCTIONALITY TESTING

### 1.1 Authentication & Session Management

#### 1.1.1 User Registration
- [ ] Navigate to registration page
- [ ] Fill registration form with valid data
- [ ] Submit form
- [ ] Verify user created in database
- [ ] Check email confirmation (if enabled)
- [ ] Try duplicate email (should fail)
- [ ] Try weak password (should fail)
- [ ] Try registration with special characters

**Terminal Output Expected:**
```
POST /accounts/register/ HTTP/1.1" 200
```

#### 1.1.2 User Login
- [ ] Navigate to login page
- [ ] Login with correct credentials
- [ ] Verify redirect to home page
- [ ] Check session is created
- [ ] Try login with wrong password (should fail)
- [ ] Try login with non-existent user (should fail)
- [ ] Check "Remember Me" functionality (if available)
- [ ] Try SQL injection in username field

**Terminal Output Expected:**
```
POST /accounts/login/ HTTP/1.1" 302
GET / HTTP/1.1" 200
```

#### 1.1.3 Session Timeout Testing
- [ ] Login to system
- [ ] Note login time
- [ ] Wait 2 minutes without activity
- [ ] Try to click a link or refresh
- [ ] Verify automatic logout
- [ ] Check redirected to login page
- [ ] Verify session cleared from database

**Observation:**
- Session should expire after 2 minutes of inactivity
- User should be logged out without manual action

#### 1.1.4 Logout
- [ ] Click logout button
- [ ] Verify redirect to home page
- [ ] Try accessing protected page
- [ ] Verify redirected to login
- [ ] Check session removed from database

**Terminal Output Expected:**
```
POST /accounts/logout/ HTTP/1.1" 302
GET /accounts/login/ HTTP/1.1" 200
```

#### 1.1.5 Profile Management
- [ ] Login as user
- [ ] Navigate to profile
- [ ] Edit profile information
- [ ] Upload profile picture (if available)
- [ ] Save changes
- [ ] Refresh page and verify changes persist
- [ ] Try uploading invalid file type

**Terminal Output Expected:**
```
GET /accounts/profile/ HTTP/1.1" 200
POST /accounts/profile/edit/ HTTP/1.1" 302
```

---

### 1.2 Catalog Management

#### 1.2.1 Browse Publications
- [ ] Navigate to catalog
- [ ] Verify all publications load
- [ ] Check pagination (if available)
- [ ] Count publications displayed vs database
- [ ] Verify cover images show
- [ ] Check publication titles are readable
- [ ] Check author names display

**Terminal Output Expected:**
```
GET /catalog/ HTTP/1.1" 200
GET /static/media/covers/... HTTP/1.1" 200
```

#### 1.2.2 Publication Details
- [ ] Click on a publication
- [ ] Verify detail page loads
- [ ] Check all information displays:
  - [ ] Title
  - [ ] Author
  - [ ] Publication date
  - [ ] ISBN
  - [ ] Subject
  - [ ] Description
  - [ ] Available copies
- [ ] Check cover image displays
- [ ] Check action buttons present

**Terminal Output Expected:**
```
GET /catalog/publication/1/ HTTP/1.1" 200
```

#### 1.2.3 Search Functionality
- [ ] Navigate to search
- [ ] Search by publication title
- [ ] Verify results display correctly
- [ ] Search by author name
- [ ] Search by ISBN
- [ ] Try empty search
- [ ] Try special characters in search
- [ ] Try SQL injection in search field
- [ ] Check pagination of results

**Terminal Output Expected:**
```
GET /catalog/search/?q=test HTTP/1.1" 200
GET /catalog/search-suggestions/?q=test HTTP/1.1" 200
```

#### 1.2.4 Browse by Category
- [ ] Browse by Author
  - [ ] Verify list loads
  - [ ] Click author to see publications
  - [ ] Verify correct publications show
- [ ] Browse by Subject
  - [ ] Verify list loads
  - [ ] Click subject to see publications
- [ ] Browse by Type
  - [ ] Verify list loads
  - [ ] Click type to see publications

**Terminal Output Expected:**
```
GET /catalog/browse-by-author/ HTTP/1.1" 200
GET /catalog/browse-by-subject/ HTTP/1.1" 200
GET /catalog/browse-by-type/ HTTP/1.1" 200
```

---

### 1.3 Circulation Management

#### 1.3.1 Checkout (Borrowing)
- [ ] Login as staff/admin
- [ ] Navigate to checkout page
- [ ] Scan/enter barcode or ISBN
- [ ] Select borrower
- [ ] Click checkout
- [ ] Verify loan created
- [ ] Check database record
- [ ] Check "available copies" decremented
- [ ] Try checkout with invalid barcode
- [ ] Try checkout exceeding max items
- [ ] Verify checkout confirmation shows

**Terminal Output Expected:**
```
POST /circulation/checkout/ HTTP/1.1" 302
GET /circulation/checkout/ HTTP/1.1" 200
```

#### 1.3.2 Checkin (Return)
- [ ] Navigate to checkin page
- [ ] Scan/enter returned item barcode
- [ ] Click checkin
- [ ] Verify loan marked as returned
- [ ] Check "available copies" incremented
- [ ] Check overdue status (if applicable)
- [ ] Verify fine calculation (if applicable)

**Terminal Output Expected:**
```
POST /circulation/checkin/ HTTP/1.1" 302
```

#### 1.3.3 Hold Management
- [ ] Login as user
- [ ] Navigate to publication detail
- [ ] Place hold on available book
- [ ] Verify hold created
- [ ] View holds list
- [ ] Check hold status
- [ ] Try placing hold when max reached
- [ ] Cancel a hold
- [ ] Verify hold removed

**Terminal Output Expected:**
```
POST /circulation/hold/place/ HTTP/1.1" 302
```

#### 1.3.4 Loan History
- [ ] View personal loan history
- [ ] Check all borrowed items show
- [ ] Verify dates display correctly
- [ ] Check return status
- [ ] Check overdue items highlighted
- [ ] Try accessing other user's history (should fail)

**Terminal Output Expected:**
```
GET /circulation/my-loans/ HTTP/1.1" 200
```

#### 1.3.5 Overdue & Notifications
- [ ] Manually set a loan past due date (in database)
- [ ] Check overdue report
- [ ] Verify overdue items highlighted
- [ ] Check notification generation
- [ ] Verify email notification sent (check console)

**Terminal Output Expected:**
```
GET /circulation/reports/overdue/ HTTP/1.1" 200
```

---

### 1.4 Admin Dashboard & Reports

#### 1.4.1 Dashboard
- [ ] Login as admin
- [ ] Navigate to dashboard
- [ ] Verify statistics cards load:
  - [ ] Total publications
  - [ ] Total users
  - [ ] Active loans
  - [ ] Overdue items
- [ ] Check charts display
- [ ] Verify data is current

**Terminal Output Expected:**
```
GET /circulation/admin/dashboard/ HTTP/1.1" 200
GET /circulation/admin/dashboard-metrics/ HTTP/1.1" 200
```

#### 1.4.2 User Management
- [ ] View user list
- [ ] Search for user
- [ ] View user details
- [ ] Edit user information
- [ ] Deactivate user
- [ ] Reactivate user
- [ ] Delete user (if allowed)

**Terminal Output Expected:**
```
GET /circulation/borrower-list/ HTTP/1.1" 200
POST /circulation/borrower/1/edit/ HTTP/1.1" 302
```

#### 1.4.3 Reports
- [ ] Generate activity report
- [ ] Generate circulation report
- [ ] Generate overdue report
- [ ] Export to CSV (if available)
- [ ] Filter by date range
- [ ] Verify data accuracy

**Terminal Output Expected:**
```
GET /circulation/reports/ HTTP/1.1" 200
POST /circulation/reports/generate/ HTTP/1.1" 200
```

---

## PHASE 2: THEME & UI TESTING

### 2.1 Dark Mode
- [ ] Toggle to dark mode (moon icon)
- [ ] Verify all elements properly styled:
  - [ ] Background dark
  - [ ] Text light and readable
  - [ ] Tables not bright white
  - [ ] Form inputs dark
  - [ ] Buttons visible
  - [ ] Links visible
- [ ] Toggle back to light mode
- [ ] Refresh page - dark mode persists
- [ ] Clear browser storage - defaults to light
- [ ] Test on different pages

**Expected:** All UI elements have proper contrast and are readable

### 2.2 Light Mode (Default)
- [ ] Open app first time
- [ ] Verify light theme loads
- [ ] Check text readable on light background
- [ ] Check all colors appropriate
- [ ] Verify images visible
- [ ] Check buttons have proper color

### 2.3 Text Alignment
- [ ] Check table text alignment
- [ ] Check card titles alignment
- [ ] Check headings properly formatted
- [ ] Check form labels positioning
- [ ] Check modal dialogs centered
- [ ] Check buttons properly spaced

### 2.4 Responsive Design

#### Desktop (1920x1080)
- [ ] All elements visible
- [ ] No horizontal scroll
- [ ] Navigation works
- [ ] Layouts properly spaced

#### Tablet (768x1024)
- [ ] Content readable
- [ ] Navigation responsive
- [ ] Tables scroll horizontally
- [ ] Forms properly sized

#### Mobile (375x667)
- [ ] Hamburger menu works
- [ ] Content readable
- [ ] Touch targets adequate
- [ ] No overflow

**Tools:** Use browser DevTools (F12) → Device Emulation

---

## PHASE 3: DATABASE TESTING

### 3.1 Data Integrity
- [ ] Count publications in UI
- [ ] Count publications in database
  ```sql
  SELECT COUNT(*) FROM catalog_publication;
  ```
- [ ] Verify counts match
- [ ] Check user records
  ```sql
  SELECT COUNT(*) FROM accounts_user;
  ```
- [ ] Check loan records
  ```sql
  SELECT COUNT(*) FROM circulation_loan;
  ```
- [ ] Verify relationships intact
  - User has many loans
  - Publication has many loans
  - Author has many publications

### 3.2 Data Validation
- [ ] Try creating publication with null title
- [ ] Try creating user with invalid email
- [ ] Try loan with invalid user ID
- [ ] Check required fields enforced
- [ ] Check duplicate ISBNs rejected
- [ ] Check date ranges valid

### 3.3 Database Performance
- [ ] Load app with 100+ publications
- [ ] Check load time (should be <2s)
- [ ] Browse multiple pages
- [ ] Search with large dataset
- [ ] Check no slow queries in terminal

---

## PHASE 4: SECURITY TESTING

### 4.1 Authentication Security
- [ ] Try SQL injection in login:
  ```
  Username: admin' --
  Password: anything
  ```
- [ ] Try XSS in login:
  ```
  Username: <script>alert('xss')</script>
  ```
- [ ] Check password requirements enforced
- [ ] Check password never logged
- [ ] Check CSRF tokens present in forms

### 4.2 Authorization Testing
- [ ] Login as regular user
- [ ] Try accessing /admin (should redirect)
- [ ] Try accessing /circulation/admin (should fail)
- [ ] Try accessing other user's profile
- [ ] Try accessing other user's loans
- [ ] Try modifying other user's data via URL

### 4.3 Session Security
- [ ] Check session cookies HttpOnly
- [ ] Check session doesn't expose user ID in URL
- [ ] Check session timeout working (2 min)
- [ ] Try using expired session
- [ ] Check session not reusable after logout

### 4.4 CSRF Protection
- [ ] Check forms have CSRF token
- [ ] Try POST request without token
- [ ] Verify request rejected

---

## PHASE 5: ERROR HANDLING

### 5.1 Page Errors
- [ ] Try accessing non-existent publication (/catalog/999/)
  - [ ] Should show 404
- [ ] Try accessing without login
  - [ ] Should redirect to login
- [ ] Try invalid search queries
  - [ ] Should show no results gracefully

### 5.2 Database Errors
- [ ] Check error messages clear (not exposing database details)
- [ ] Verify 500 errors show friendly message
- [ ] Check error logged in terminal

### 5.3 Form Validation
- [ ] Submit form with missing required field
- [ ] Submit form with invalid email
- [ ] Submit form with too-long input
- [ ] Verify error messages helpful

### 5.4 File Upload Errors
- [ ] Try uploading unsupported file type
- [ ] Try uploading too-large file
- [ ] Try uploading duplicate file
- [ ] Verify error handling graceful

---

## PHASE 6: INTEGRATION TESTING

### 6.1 Email Notifications
- [ ] Check console for email output
- [ ] Verify subject lines clear
- [ ] Verify email content appropriate
- [ ] Check email formatting readable

### 6.2 Data Flow
- [ ] Checkout → Loan created → History updated
- [ ] Checkin → Loan updated → Copy available
- [ ] User registration → Can login → Profile created
- [ ] Publication add → Appears in search → Can borrow

### 6.3 Cross-Module Functionality
- [ ] Create publication in catalog
- [ ] User can find it
- [ ] User can borrow it
- [ ] Check circulation history
- [ ] Check admin can see stats

---

## TERMINAL MONITORING CHECKLIST

As you test, watch the terminal for HTTP requests:

**Good Indicators (200, 302 status codes):**
```
GET /catalog/ HTTP/1.1" 200
POST /accounts/login/ HTTP/1.1" 302
GET /circulation/dashboard/ HTTP/1.1" 200
```

**Warning Signs (400, 403, 500 codes):**
```
GET /admin/ HTTP/1.1" 403              (Unauthorized)
GET /non-existent/ HTTP/1.1" 404       (Not found)
POST /checkout/ HTTP/1.1" 500          (Server error)
```

**Info Level Logs Should Show:**
- Request method (GET, POST, etc.)
- Path accessed
- HTTP status code
- Request size
- Timestamp

---

## TESTING EXECUTION GUIDE

### Quick Test (15 minutes)
1. Login/Logout cycle
2. Browse catalog and search
3. Checkout and checkin
4. Toggle dark mode
5. Check terminal output

### Standard Test (45 minutes)
1. Complete Phase 1 (Core Functionality)
2. Complete Phase 2 (Theme & UI)
3. Monitor terminal throughout

### Comprehensive Test (2-3 hours)
1. All 6 phases
2. Document all findings
3. Create issue list
4. Test fixes

---

## ISSUE TRACKING TEMPLATE

For each issue found:

```
**Issue #:** [number]
**Severity:** [Critical/High/Medium/Low]
**Category:** [Auth/Catalog/Circulation/UI/DB/Security]
**Description:** [What happened]
**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
**Expected:** [What should happen]
**Actual:** [What actually happened]
**Terminal Output:** [Paste relevant logs]
**Screenshot:** [If UI related]
**Status:** [Open/In Progress/Fixed/Won't Fix]
```

---

## SIGN-OFF

Once all tests pass:

- [ ] Phase 1: Core Functionality ✅
- [ ] Phase 2: Theme & UI ✅
- [ ] Phase 3: Database ✅
- [ ] Phase 4: Security ✅
- [ ] Phase 5: Error Handling ✅
- [ ] Phase 6: Integration ✅
- [ ] Terminal monitoring working ✅
- [ ] No outstanding issues ✅

**Date Completed:** _______________  
**Tested By:** _______________  
**Sign-Off:** Ready for Production _______________

---

## NOTES

- Terminal will show all HTTP requests (INFO level logging)
- Watch for patterns in requests
- Look for unexpected 404s or 500s
- Check response times
- Document any anomalies

**Happy Testing!** 🧪
