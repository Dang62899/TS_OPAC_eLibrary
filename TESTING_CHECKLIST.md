# e-Library Testing Checklist

## Pre-Testing Setup

- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Database migrations run (`python manage.py migrate`)
- [ ] Superuser created
- [ ] Initial data loaded (`python manage.py create_initial_data`)
- [ ] Development server running (`python manage.py runserver`)

## User Authentication Tests

### Registration
- [ ] Can register new borrower account
- [ ] Email validation works
- [ ] Password validation enforced
- [ ] Duplicate username prevented
- [ ] New user can login after registration

### Login/Logout
- [ ] Can login with correct credentials
- [ ] Login fails with incorrect password
- [ ] Logout works correctly
- [ ] Redirected appropriately after login
- [ ] Session persists correctly

### Profile Management
- [ ] Can view profile
- [ ] Can edit profile information
- [ ] Changes save correctly
- [ ] Email updates properly

## Catalog (OPAC) Tests

### Search Functionality
- [ ] Keyword search returns results
- [ ] Search by title works
- [ ] Search by author works
- [ ] Search by subject works
- [ ] Search by call number works
- [ ] Search by ISBN works
- [ ] Advanced search filters work
- [ ] Publication type filter works
- [ ] Language filter works
- [ ] Date range filter works
- [ ] Available-only filter works
- [ ] Pagination works correctly
- [ ] No results message displays properly

### Browse Features
- [ ] Browse by publication type works
- [ ] Browse by subject works
- [ ] Browse by author works
- [ ] Pagination in browse views works

### Publication Detail
- [ ] Publication details display correctly
- [ ] All bibliographic information shown
- [ ] Authors display properly
- [ ] Subjects display properly
- [ ] Item copies list shows correctly
- [ ] Item status displays accurately
- [ ] Due dates show for checked-out items
- [ ] Hold button appears when appropriate
- [ ] Cover image displays (if present)

## Circulation System Tests (Staff)

### Check Out
- [ ] Can access checkout page (staff only)
- [ ] ISBN entry works (barcode scanning is disabled by default)
- [ ] Borrower lookup by card number works
- [ ] Borrower lookup by username works
- [ ] Due date calculated correctly
- [ ] Checkout prevents if item unavailable
- [ ] Checkout prevents if borrower blocked
- [ ] Checkout prevents if borrower at limit
- [ ] Item status updates to "On Loan"
- [ ] Loan record created correctly
- [ ] Success message displays
- [ ] Item statistics update (times borrowed)

### Check In
- [ ] Can access checkin page (staff only)
- [ ] ISBN entry works (barcode scanning/entry temporarily on hold)
- [ ] Returns item correctly
- [ ] Calculates overdue correctly
- [ ] Item status updates to "Available"
- [ ] Hold detection works
- [ ] Item placed on hold shelf if hold exists
- [ ] Success message displays
- [ ] Overdue warning displays

### Renewals
- [ ] Staff can renew from borrower detail
- [ ] Borrower can renew online
- [ ] Renewal extends due date correctly
- [ ] Renewal count increments
- [ ] Renewal prevented if at limit (2)
- [ ] Renewal prevented if overdue
- [ ] Renewal prevented if item has holds
- [ ] Error messages display properly

### Hold Management
- [ ] Borrowers can place holds
- [ ] Pickup location selection works
- [ ] Hold queue position calculated
- [ ] Cannot place duplicate hold
- [ ] Staff can view waiting holds
- [ ] Staff can view ready holds
- [ ] Staff can set hold as ready
- [ ] Hold shelf status works
- [ ] Borrowers can cancel holds
- [ ] Hold expiration tracking works

### Borrower Management
- [ ] Can search borrowers by name
- [ ] Can search by username
- [ ] Can search by card number
- [ ] Can filter by blocked status
- [ ] Borrower detail shows all info
- [ ] Active loans display correctly
- [ ] Loan history displays
- [ ] Active holds display
- [ ] Can block borrower with reason
- [ ] Can unblock borrower
- [ ] Blocked status enforced

### In-Transit Management
- [ ] Can send item in transit
- [ ] Item status updates to "In Transit"
- [ ] From location captured
- [ ] To location set correctly
- [ ] Can receive in-transit item
- [ ] Item location updates on receive
- [ ] Item status updates on receive
- [ ] Transit list displays properly

## Reports Tests

### Overdue Report
- [ ] Shows all overdue items
- [ ] Displays days overdue correctly
- [ ] Shows borrower information
- [ ] Shows contact information
- [ ] Print function works
- [ ] Empty state displays when no overdues

### Circulation Statistics
- [ ] Shows correct date range (30 days)
- [ ] Total checkouts count correct
- [ ] Total returns count correct
- [ ] Most borrowed items list correct
- [ ] Most active borrowers list correct
- [ ] Statistics by type display
- [ ] Print function works

### Dashboard Statistics
- [ ] Active loans count correct
- [ ] Overdue count correct
- [ ] Holds waiting count correct
- [ ] Holds ready count correct
- [ ] Items in transit count correct
- [ ] Recent checkouts display
- [ ] Recent returns display

## My Account Tests (Borrower)

### Account Overview
- [ ] Active loans display
- [ ] Due dates show correctly
- [ ] Overdue items highlighted
- [ ] Renewal button appears when eligible
- [ ] Active holds display
- [ ] Hold status correct (waiting/ready)
- [ ] Queue position shows
- [ ] Loan history displays
- [ ] Account information correct

### Online Actions
- [ ] Can renew eligible items
- [ ] Cannot renew ineligible items
- [ ] Can cancel holds
- [ ] Cannot cancel fulfilled holds
- [ ] Links to publications work

## Notification Tests (Requires Celery)

### Email Notifications
- [ ] Celery worker running
- [ ] Celery beat running
- [ ] Redis running
- [ ] Overdue notices send
- [ ] Pre-due notices send
- [ ] Hold ready notices send
- [ ] Email content correct
- [ ] Email recipients correct
- [ ] Notification records created

## Admin Interface Tests

### Publication Management
- [ ] Can add publications
- [ ] Can edit publications
- [ ] Can add authors inline
- [ ] Can add items inline
- [ ] Can upload cover images
- [ ] Can set subjects
- [ ] All fields save correctly

### Item Management
- [ ] Can add items
- [ ] Can change item status
- [ ] Barcode uniqueness enforced (barcode is optional for now; ISBN is used for transactions)
- [ ] Location selection works
- [ ] Statistics display correctly

### User Management
- [ ] Can add users
- [ ] Can set user type
- [ ] Can assign card numbers
- [ ] Can set borrowing limits
- [ ] Can view user activity

### Circulation Records
- [ ] Can view loans
- [ ] Can view holds
- [ ] Can view notifications
- [ ] Can view transit records
- [ ] Filters work correctly

## Edge Cases & Error Handling

### Invalid Actions
- [ ] Cannot checkout unavailable item
- [ ] Cannot checkout to blocked user
- [ ] Cannot exceed borrowing limit
- [ ] Cannot renew beyond limit
- [ ] Cannot access staff pages as borrower
- [ ] Cannot access others' accounts

### Data Validation
- [ ] Duplicate barcodes prevented
- [ ] Email format validated
- [ ] Required fields enforced
- [ ] Date ranges validated
- [ ] Unique constraints work

### Error Messages
- [ ] Clear error messages display
- [ ] Form validation messages show
- [ ] Permission denied handled
- [ ] 404 pages work
- [ ] 500 errors caught (in production)

## Security Tests

### Authentication
- [ ] Login required for protected pages
- [ ] Staff-only pages require staff role
- [ ] Cannot access admin without permissions
- [ ] Sessions expire correctly
- [ ] CSRF protection works

### Authorization
- [ ] Users cannot modify others' data
- [ ] Borrowers cannot access staff functions
- [ ] URL manipulation prevented
- [ ] Form tampering prevented

## Performance Tests

### Page Load
- [ ] Homepage loads quickly
- [ ] Search results load reasonably
- [ ] Large result sets paginate
- [ ] Images load efficiently
- [ ] No excessive queries

### Database
- [ ] Queries optimized (use select_related)
- [ ] Indexes working
- [ ] Large datasets handled
- [ ] No N+1 query problems

## User Experience Tests

### Navigation
- [ ] Main menu works on all pages
- [ ] Breadcrumbs display correctly
- [ ] Links go to correct pages
- [ ] Back buttons work
- [ ] Responsive design works

### Forms
- [ ] All forms submit correctly
- [ ] Cancel buttons work
- [ ] Field help text displays
- [ ] Placeholders helpful
- [ ] Auto-focus on barcode fields

### Messages
- [ ] Success messages display
- [ ] Error messages display
- [ ] Warning messages display
- [ ] Info messages display
- [ ] Messages dismissible

## Mobile Responsiveness

- [ ] Works on mobile phones
- [ ] Works on tablets
- [ ] Bootstrap responsive classes work
- [ ] Navigation menu collapses
- [ ] Forms usable on mobile
- [ ] Tables scroll horizontally if needed

## Browser Compatibility

- [ ] Works in Chrome
- [ ] Works in Firefox
- [ ] Works in Edge
- [ ] Works in Safari
- [ ] No console errors

## Data Integrity

### Loan Lifecycle
- [ ] Checkout → Active loan
- [ ] Return → Returned status
- [ ] Item status follows loan status
- [ ] Statistics update correctly
- [ ] History preserved

### Hold Lifecycle
- [ ] Place hold → Waiting
- [ ] Item returned → Ready
- [ ] Pickup → Fulfilled
- [ ] Expiration → Expired
- [ ] Queue positions correct

## Final Checks

- [ ] All templates render without errors
- [ ] All URLs resolve correctly
- [ ] All static files load
- [ ] No broken links
- [ ] No missing images
- [ ] Console free of errors
- [ ] Database integrity maintained
- [ ] Backup/restore works

## Production Readiness

- [ ] DEBUG set to False
- [ ] SECRET_KEY changed
- [ ] ALLOWED_HOSTS configured
- [ ] Database configured (PostgreSQL/MySQL)
- [ ] Email backend configured
- [ ] Static files collected
- [ ] Media files configured
- [ ] HTTPS/SSL configured
- [ ] Error logging configured
- [ ] Backup strategy in place

---

## Test Scenarios

### Scenario 1: Complete Borrowing Workflow
1. [ ] Borrower searches for publication
2. [ ] Views publication detail
3. [ ] All copies checked out, places hold
4. [ ] Another borrower returns item
5. [ ] Staff sets hold ready
6. [ ] Email notification sent
7. [ ] Borrower checks out held item
8. [ ] Renews item once
9. [ ] Returns item
10. [ ] Loan marked as returned

### Scenario 2: Overdue Workflow
1. [ ] Item checked out
2. [ ] Due date passes
3. [ ] System detects overdue
4. [ ] Overdue notice sent
5. [ ] Appears in overdue report
6. [ ] Item returned late
7. [ ] Marked as overdue_returned

### Scenario 3: Multiple Holds
1. [ ] Item checked out
2. [ ] User A places hold
3. [ ] User B places hold
4. [ ] Queue positions: A=1, B=2
5. [ ] Item returned
6. [ ] Hold A set ready
7. [ ] User A picks up
8. [ ] Hold B now position 1

---

**Testing Notes:**
- Document any bugs found
- Note performance issues
- Record user feedback
- List enhancement ideas
- Track test coverage
