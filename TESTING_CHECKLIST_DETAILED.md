# Testing Checklist for e-Library
## Pre-Deployment Verification

---

## Environment Setup ✅

- [ ] Migrations run successfully
- [ ] Sample books loaded (40 publications)
- [ ] Test users created (admin, staff, borrower)
- [ ] Static files collected
- [ ] No errors in console

---

## 1. Administrator Role Testing

### Login & Access
- [ ] Login as `admin` / `admin123` works
- [ ] Navigation shows: Home, Search, Circulation, Manage Users, Manage Catalog
- [ ] User dropdown shows profile and logout options

### User Management
- [ ] Can access "Manage Users" page
- [ ] Can view all users in system
- [ ] Can search users by name, email, username
- [ ] Can filter users by type (admin, staff, borrower)
- [ ] Can edit any user account
- [ ] Can change user type
- [ ] Can block/unblock users
- [ ] Can delete users (except self)
- [ ] Deleted users are removed from system

### Catalog Management
- [ ] Can access "Manage Catalog" page
- [ ] Can view all publications
- [ ] Can search publications
- [ ] Can filter by publication type
- [ ] Can edit publications via admin link
- [ ] Can delete publications
- [ ] Deletion confirmation works

### Circulation Access
- [ ] Can access circulation dashboard
- [ ] Can perform checkouts
- [ ] Can perform checkins
- [ ] Can manage holds
- [ ] Can view all reports

---

## 2. Staff/Librarian Role Testing

### Login & Access
- [ ] Login as `librarian` / `staff123` works
- [ ] Navigation shows: Home, Search, Circulation
- [ ] Does NOT show: Manage Users, Manage Catalog in main nav
- [ ] User dropdown shows profile and logout options

### Catalog Operations
- [ ] Can search catalog
- [ ] Can view publication details
- [ ] Can access "Manage Catalog" if implemented for staff
- [ ] Can add new publications
- [ ] Can edit publications
- [ ] CANNOT delete publications

### Circulation Operations
- [ ] Can access circulation dashboard
- [ ] Can checkout items to borrowers
- [ ] Can checkin returned items
- [ ] Can view holds
- [ ] Can update hold status
- [ ] Can view borrower information
- [ ] Can generate reports

### Limitations
- [ ] Cannot access "Manage Users"
- [ ] Cannot delete publications
- [ ] Cannot delete users
- [ ] Cannot modify admin accounts

---

## 3. Borrower/User Role Testing

### Registration & Login
- [ ] Can register new account
- [ ] Registration form validation works
- [ ] Login as `student` / `student123` works
- [ ] Library card number assigned automatically

### Navigation & Access
- [ ] Navigation shows: Home, Search
- [ ] Does NOT show: Circulation, Manage Users, Manage Catalog
- [ ] User dropdown shows: My Account, Profile, Logout

### Catalog Functions
- [ ] Can search catalog
- [ ] Quick search works
- [ ] Advanced search works
- [ ] Can filter by type, language, year
- [ ] Can browse by type, subject, author
- [ ] Can view publication details
- [ ] Can see item availability

### Account Management
- [ ] Can access "My Account" page
- [ ] Can view active loans
- [ ] Can view loan history
- [ ] Can view active holds
- [ ] Can edit profile information
- [ ] Can change password
- [ ] Can update contact info

### Self-Service Features
- [ ] Can place holds on checked-out items
- [ ] Can renew items (if no holds exist)
- [ ] Hold status updates correctly
- [ ] Renewal updates due date

### Limitations
- [ ] Cannot access circulation dashboard
- [ ] Cannot access user management
- [ ] Cannot access catalog management
- [ ] Cannot checkout items (must go through staff)

---

## 4. UI/UX Testing

### Layout & Design
- [ ] Footer sticks to bottom of page
- [ ] Footer displays "© 2025 e-Library Management System | RDS | TS"
- [ ] Footer has dark background with white text
- [ ] Cards have shadow and hover effects
- [ ] Buttons have modern gradient styling
- [ ] Buttons lift slightly on hover

### Forms
- [ ] Login form button properly spaced (mt-3)
- [ ] Login button is full width
- [ ] Register form button properly spaced (mt-3)
- [ ] Register button is full width
- [ ] Form inputs have focus effects
- [ ] All forms have proper validation

### Navigation
- [ ] Navbar is fixed at top
- [ ] Navbar has shadow effect
- [ ] Logo displays correctly
- [ ] Menu items appropriate for user role
- [ ] Dropdown menus work smoothly

### Responsive Design
- [ ] Works on desktop (1920x1080)
- [ ] Works on laptop (1366x768)
- [ ] Works on tablet (768x1024)
- [ ] Works on mobile (375x667)
- [ ] Navigation collapses on mobile
- [ ] Tables are scrollable on mobile

---

## 5. Sample Data Verification

### Manuals (10 items)
- [ ] All 10 manuals visible
- [ ] Each has proper title and metadata
- [ ] Each has multiple copies (items)
- [ ] Items are searchable
- [ ] Authors assigned correctly
- [ ] Subjects assigned correctly

### SOPs (10 items)
- [ ] All 10 SOPs visible
- [ ] Proper call numbers
- [ ] Multiple copies each
- [ ] Searchable and browseable

### Capstone Projects (10 items)
- [ ] All 10 projects visible
- [ ] 2024 publication dates
- [ ] Single copy each (typical for capstone)
- [ ] Detailed abstracts

### TTPs (10 items)
- [ ] All 10 TTPs visible
- [ ] Security-related subjects
- [ ] Multiple copies
- [ ] Proper categorization

---

## 6. Search Functionality

### Quick Search
- [ ] Search box always visible
- [ ] Search returns results
- [ ] Search highlights keywords
- [ ] No results message displays correctly

### Advanced Search
- [ ] All search fields work (title, author, subject, etc.)
- [ ] Filters work (type, language, year)
- [ ] "Available Only" filter works
- [ ] Results paginated properly (20 per page)
- [ ] Sort options work

### Browse Functions
- [ ] Browse by Type works
- [ ] Browse by Subject works
- [ ] Browse by Author works
- [ ] Pagination works in browse views

---

## 7. Circulation Testing

### Checkout Process
- [ ] Barcode scanning available (optional)
- [ ] Manual barcode entry works
- [ ] Library card verification works
- [ ] Eligibility checks work (not blocked, under limit)
- [ ] Due date calculated correctly
- [ ] Item status updates to "checked out"
- [ ] Loan recorded in system

### Checkin Process
- [ ] Barcode scanning available (optional)
- [ ] Item marked as returned
- [ ] Overdue detection works
- [ ] Item status updates to "available"
- [ ] Hold notifications trigger

### Hold Management
- [ ] Can place hold on checked-out item
- [ ] Hold status shows "waiting"
- [ ] Hold becomes "ready" when item returned
- [ ] Notifications sent
- [ ] Can cancel holds
- [ ] Expired holds handled

---

## 8. Security & Permissions

### Authentication
- [ ] Cannot access protected pages without login
- [ ] Logout works properly
- [ ] Session timeout works
- [ ] Password reset works

### Authorization
- [ ] Admin can access all features
- [ ] Staff limited to appropriate features
- [ ] Borrowers limited to user features
- [ ] URL manipulation blocked (cannot access admin URLs as staff)
- [ ] Decorators prevent unauthorized access

### Data Protection
- [ ] CSRF protection on all forms
- [ ] Passwords hashed in database
- [ ] User data private
- [ ] Delete confirmations required

---

## 9. Documentation Review

### ADMIN_MANUAL.md
- [ ] Comprehensive and accurate
- [ ] All features documented
- [ ] Clear instructions
- [ ] Troubleshooting section helpful

### STAFF_MANUAL.md
- [ ] Covers all staff functions
- [ ] Daily procedures clear
- [ ] Best practices included
- [ ] Common issues addressed

### BORROWER_MANUAL.md
- [ ] User-friendly language
- [ ] Step-by-step instructions
- [ ] FAQ section comprehensive
- [ ] Quick reference useful

---

## 10. Performance Testing

### Page Load Times
- [ ] Homepage loads < 2 seconds
- [ ] Search results load < 3 seconds
- [ ] Catalog browse loads < 2 seconds
- [ ] Dashboard loads < 2 seconds

### Database Queries
- [ ] No N+1 query issues
- [ ] Pagination prevents large data loads
- [ ] Indexes used appropriately

### Browser Compatibility
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Edge (latest)
- [ ] Safari (latest)

---

## 11. Error Handling

### User Errors
- [ ] Invalid login shows error message
- [ ] Form validation displays errors
- [ ] Missing required fields highlighted
- [ ] Clear error messages

### System Errors
- [ ] 404 page exists
- [ ] 403 page exists
- [ ] 500 page exists
- [ ] Errors logged appropriately

---

## 12. Final Checks

### Code Quality
- [ ] No Python errors
- [ ] No JavaScript console errors
- [ ] No broken links
- [ ] No missing images
- [ ] All templates render correctly

### Data Integrity
- [ ] Sample data loads without errors
- [ ] Relationships maintained
- [ ] Foreign keys valid
- [ ] No orphaned records

### Deployment Readiness
- [ ] All migrations applied
- [ ] Static files collected
- [ ] Settings configured for production
- [ ] Environment variables set
- [ ] Database backed up

---

## Sign-off

**Tested by**: _________________  
**Date**: _________________  
**Role**: _________________  

**Issues Found**: _________________  
_________________________________  
_________________________________  

**Status**: 
- [ ] Ready for Deployment
- [ ] Needs Fixes (see issues above)

---

**Document Version**: 1.0  
**Last Updated**: November 26, 2025  
**Prepared by**: e-Library Development Team | RDS | TS
