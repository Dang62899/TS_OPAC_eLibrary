# Quick Start Guide - Testing the e-Library
## Get Started in 5 Minutes!

---

## Step 1: Setup Test Environment (2 minutes)

### Option A: Automatic Setup (Recommended)
```cmd
setup_test_data.bat
```
This will:
- Run migrations
- Create 40 sample books
- Create 3 test users
- Set up the database

### Option B: Manual Setup
```cmd
# Run migrations
python manage.py migrate

# Create sample books
python manage.py create_sample_books

# Create test users (use Django shell)
python manage.py shell
```
Then run the user creation commands from ADJUSTMENTS_SUMMARY.md

---

## Step 2: Start the Server
```cmd
python manage.py runserver
```

Open your browser to: **http://127.0.0.1:8000/**

---

## Step 3: Test Each User Role (3 minutes)

### 🔴 Test as ADMINISTRATOR
**Login:** `admin` / `admin123`

**Try these:**
1. Click **Manage Users** → See all users
2. Click **Manage Catalog** → See all publications
3. Try editing a user
4. Try adding a publication
5. Access **Circulation** dashboard

**Expected:** Full access to everything

---

### 🟡 Test as STAFF/LIBRARIAN
**Login:** `librarian` / `staff123`

**Try these:**
1. Click **Circulation** → See dashboard
2. Try a checkout (you'll need a borrower card: LC001)
3. Try a checkin
4. Click **Search Catalog** → Browse books
5. Try accessing **Manage Users** (should fail)

**Expected:** Circulation access, NO user management

---

### 🟢 Test as BORROWER/USER
**Login:** `student` / `student123`

**Try these:**
1. Click **My Account** → See your loans
2. Click **Search Catalog** → Find books
3. Try placing a hold on a book
4. Click **Profile** → Edit your info
5. Try accessing **Circulation** (should fail)

**Expected:** Can search and manage account, NO admin features

---

## Step 4: Verify UI Improvements

### Check These Visual Elements:
- ✅ Footer at bottom shows: "| RDS | TS"
- ✅ Login button has space above it (not cramped)
- ✅ Cards have nice shadows and hover effects
- ✅ Buttons are modern with gradients
- ✅ Navigation menu changes based on user role

---

## Step 5: Browse Sample Data

### Explore the 40 Sample Books:

**Manuals (10)** - Technical guides
- Search for: "Network", "Database", "Security"

**SOPs (10)** - Standard procedures
- Browse Type: SOP

**Capstone Projects (10)** - Student projects
- Browse Type: Capstone Project
- Look for: AI, Blockchain, IoT projects

**TTPs (10)** - Security tactics
- Search for: "Cybersecurity", "Threat", "Forensics"

---

## Quick Test Scenarios

### Scenario 1: Checkout Workflow
1. Login as **librarian**
2. Go to **Circulation** → **Checkout**
3. Enter barcode or Item ID: `MAN00101` (barcode optional; prefer ISBN or Item ID)
4. Enter library card: `LC001`
5. Click **Check Out**
6. Verify loan appears in circulation dashboard

### Scenario 2: User Management
1. Login as **admin**
2. Go to **Manage Users**
3. Search for "student"
4. Click **Edit** on student account
5. Change max items allowed
6. Save changes

### Scenario 3: Catalog Search
1. Login as **student**
2. Click **Search Catalog**
3. Search for "security"
4. Filter by Type: Manual
5. Click on a result to see details

### Scenario 4: Place a Hold
1. Login as **student**
2. Search for a book
3. If available, have staff check it out to another user first
4. Click **Place Hold**
5. Verify hold appears in **My Account**

---

## Common Test Credentials

```
ADMIN
- Username: admin
- Password: admin123
- Card: ADMIN001

STAFF
- Username: librarian
- Password: staff123
- Card: STAFF001

BORROWER
- Username: student
- Password: student123
- Card: LC001
```

---

## What to Look For

### ✅ Working Correctly
- Role-based menus
- Sticky footer with RDS | TS
- Modern button styling
- Smooth card animations
- All 40 sample books visible
- User management (admin only)
- Catalog management (admin/staff)
- Circulation functions (admin/staff)
- Account management (all users)

### ❌ Should NOT Work
- Staff accessing "Manage Users"
- Borrowers accessing "Circulation"
- Users accessing features above their permission level
- Deleting publications as staff
- Editing other users as borrower

---

## Troubleshooting

### Issue: "Table doesn't exist"
**Fix:** Run migrations
```cmd
python manage.py migrate
```

### Issue: "No sample books"
**Fix:** Run the command
```cmd
python manage.py create_sample_books
```

### Issue: "Cannot login"
**Fix:** Recreate test users
```cmd
python manage.py shell
# Then run user creation commands
```

### Issue: "Page not found (404)"
**Fix:** Check URL patterns are loaded
```cmd
python manage.py runserver --noreload
```

---

## Next Steps After Testing

1. ✅ Verify all features work as expected
2. ✅ Check detailed testing checklist
3. ✅ Review user manuals for accuracy
4. ✅ Fix any issues found
5. ✅ Prepare for deployment

---

## File References

- **Testing Checklist**: `TESTING_CHECKLIST_DETAILED.md`
- **Adjustments Summary**: `ADJUSTMENTS_SUMMARY.md`
- **Admin Manual**: `ADMIN_MANUAL.md`
- **Staff Manual**: `STAFF_MANUAL.md`
- **Borrower Manual**: `BORROWER_MANUAL.md`

---

## Support

Need help? Check:
1. Error messages in terminal
2. Browser console (F12)
3. Django debug page
4. Documentation files above

---

**Happy Testing! 🚀**

**Prepared by**: e-Library Development Team | RDS | TS  
**Date**: November 26, 2025
