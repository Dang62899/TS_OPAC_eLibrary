# Staff/Librarian User Manual
## e-Library Management System

---

## Table of Contents
1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Circulation Dashboard](#circulation-dashboard)
4. [Checking Out Items](#checking-out-items)
5. [Checking In Items](#checking-in-items)
6. [Managing Holds](#managing-holds)
7. [Searching the Catalog](#searching-the-catalog)
8. [Managing Publications](#managing-publications)
9. [Assisting Borrowers](#assisting-borrowers)
10. [Daily Procedures](#daily-procedures)
11. [Best Practices](#best-practices)
12. [Common Issues](#common-issues)

---

## Introduction

Welcome to the Staff User Manual for the e-Library Management System. As a staff member (librarian), you have access to circulation functions, catalog management, and can assist borrowers with their needs.

### Staff Privileges
- ✅ **Circulation operations**: Check out and check in items
- ✅ **Hold management**: Process and manage holds
- ✅ **Catalog viewing**: Search and view all publications
- ✅ **Publication management**: Add and edit catalog entries
- ✅ **Borrower assistance**: Help users with their accounts
- ✅ **Reports**: View circulation reports
- ❌ **Limited access**: Cannot delete publications or users
- ❌ **Cannot**: Create or delete admin/staff accounts

---

## Getting Started

### Logging In
1. Open the e-Library website
2. Click **Login** in the navigation bar
3. Enter your credentials:
   - **Username**: Your assigned staff username
   - **Password**: Your password
4. Click **Login**

### Your Dashboard
After logging in, you'll see:
- Navigation menu with **Circulation** access
- Search catalog functionality
- Your account dropdown menu
- Recent activity notifications

---

## Circulation Dashboard

### Accessing the Dashboard
1. Click **Circulation** in the main navigation menu
2. The dashboard displays key information at a glance

### Dashboard Sections

#### Statistics Overview
- **Active Loans**: Current checked-out items
- **Overdue Loans**: Items past due date
- **Holds Waiting**: Items on hold
- **Holds Ready**: Items ready for pickup
- **Items In Transit**: Items being moved

#### Recent Activity
- **Recent Checkouts**: Last 10 items checked out
- **Recent Returns**: Last 10 items returned
- Shows borrower name, item, and timestamp

### Quick Actions
- **Checkout**: Start new checkout process
- **Checkin**: Process returned items
- **Manage Holds**: View and update holds
- **Search Borrowers**: Find borrower accounts
- **Overdue Report**: View overdue items

---

## Checking Out Items

### Standard Checkout Procedure
1. From the Circulation Dashboard, click **Checkout**
2. Enter the publication **ISBN** (barcode scanning is disabled by default)
   - Example ISBN: `978-1-234-56780-1`
3. Scan or manually enter the **borrower's library card number**
   - Example: `LC123456`
4. System will automatically:
   - Verify item availability
   - Check borrower eligibility
   - Calculate due date
5. Review the checkout details:
   - Item title (barcode stored as optional identifier)
   - Borrower name
   - Due date
6. Click **Check Out** to complete
7. Print receipt or email confirmation to borrower

### Pre-Checkout Verification
Before checking out, verify:
- ✅ Borrower account is active (not blocked)
- ✅ Borrower hasn't exceeded maximum items allowed
- ✅ Item status is "Available"
- ✅ Physical item condition is acceptable

### Common Checkout Scenarios

#### Borrower at Maximum Limit
**Problem**: Borrower already has maximum items checked out

**Solution**:
1. Ask borrower to return items first, OR
2. Have them renew existing items to free up slots
3. Contact administrator for limit increase if needed

#### Item Not Available
**Problem**: Item shows as checked out or on hold

**Solution**:
1. Check actual item status in the system
2. Offer to place a hold for the borrower
3. Suggest alternative publications

#### Blocked Borrower
**Problem**: Borrower account is blocked

**Solution**:
1. Check block reason (overdue items, fines, etc.)
2. Resolve the issue if possible
3. Contact administrator for unblocking if appropriate

---

## Checking In Items

### Standard Checkin Procedure
1. From the Circulation Dashboard, click **Checkin**
2. Enter the publication **ISBN** or select the item from the list
3. System automatically processes the return:
   - Marks item as returned
   - Calculates any overdue period
   - Updates item status to "Available"
4. Review return details:
   - Item information
   - Borrower who returned it
   - Return date
   - Overdue status (if applicable)
5. Click **Confirm Return**

### Physical Inspection
After checking in, always:
1. **Inspect the item** for damage
2. **Check completeness** (all pages, discs, etc.)
3. **Update condition** in system if needed
4. **Shelve** or set aside for processing

### Handling Overdue Returns
If item is overdue:
1. System will display "OVERDUE" warning
2. Note the number of days overdue
3. Inform borrower (if present)
4. Follow library policy for fines/warnings
5. Item still gets checked in

### Holds Processing
If the returned item has holds:
1. System will alert: "Hold exists for this item"
2. Click **Process Hold**
3. System marks hold as "Ready for Pickup"
4. Print hold slip with borrower name
5. Place item on hold shelf
6. System sends notification to borrower

---

## Managing Holds

### Viewing Holds
1. Click **Manage Holds** in Circulation menu
2. View holds organized by status:
   - **Waiting**: Placed, waiting for availability
   - **Ready**: Available for pickup
   - **Expired**: Not picked up in time

### Processing Holds

#### Making an Item Ready
1. When held item becomes available
2. Find the hold in "Waiting" status
3. Click **Mark as Ready**
4. Print hold slip
5. Place item on hold shelf
6. Borrower receives notification

#### Borrower Pickup
1. Verify borrower identity (library card)
2. Locate item on hold shelf
3. Click **Check Out** to borrower
4. Hold automatically completes

#### Canceling a Hold
1. Locate the hold
2. Click **Cancel Hold**
3. Enter reason (optional)
4. Confirm cancellation
5. Item becomes available to others

### Hold Shelf Management
- Check hold shelf daily
- Remove expired holds (items not picked up)
- Return expired hold items to shelves
- Keep hold shelf organized alphabetically

---

## Searching the Catalog

### Basic Search
1. Click **Search Catalog** in navigation
2. Enter search terms
3. Select search field:
   - **All Fields**: Searches everywhere
   - **Title**: Search by title only
   - **Author**: Search by author name
   - **Subject**: Search by subject category
   - **Call Number**: Exact call number
   - **ISBN**: ISBN number
4. Click **Search**

### Advanced Search
Use additional filters:
- **Publication Type**: Manual, SOP, Capstone, TTP
- **Language**: English, etc.
- **Year Range**: Publication date range
- **Available Only**: Show only available items

### Viewing Publication Details
1. Click on any publication title
2. View complete information:
   - Authors and subjects
   - Publication details
   - Abstract/description
   - **All items** (copies) with status
3. See item availability:
   - Available (green)
   - Checked Out (yellow)
   - On Hold (blue)
   - In Transit (orange)

---

## Managing Publications

### Adding New Publications
1. Click **Manage Catalog** in navigation
2. Click **Add New Publication**
3. Fill in required information:
   - **Title**: Full title of work
   - **Publication Type**: Select appropriate type
   - **Authors**: Add or select authors
   - **Subjects**: Assign subject headings
   - **Publisher**: Select publisher
   - **Publication Date**: Year published
   - **ISBN**: If applicable
   - **Call Number**: Classification number
   - **Abstract**: Brief description
4. Click **Save**
5. Add physical items (copies) after saving

### Adding Items to Publications
After creating a publication:
1. Click **Add Item**
2. Enter item details:
   - **Barcode**: Unique identifier (optional; barcode use is temporarily on hold)
   - **Location**: Physical location
   - **Status**: Usually "Available"
   - **Condition**: Excellent, Good, Fair, Poor
3. Click **Save Item**
4. Repeat for additional copies

### Editing Publications
1. Navigate to **Manage Catalog**
2. Find the publication
3. Click **Edit**
4. Modify information as needed
5. Click **Save Changes**

**Note**: Staff can edit but not delete publications

---

## Assisting Borrowers

### Helping Users Find Materials
1. Ask about their research topic/need
2. Use advanced search with subject terms
3. Show them how to browse by:
   - Publication type
   - Subject categories
   - Author
4. Explain call number system
5. Help locate physical items

### Helping with Account Issues

#### Password Reset
1. Verify user identity
2. Contact administrator for password reset
3. Provide temporary password to user

#### Checking Loan History
1. Search for borrower account
2. View their active loans
3. Check due dates
4. Inform about overdue items

#### Placing Holds for Users
1. Find desired publication
2. Click **Place Hold**
3. Enter borrower's library card number
4. Confirm hold placement
5. Inform user about pickup notification

### Teaching Users
Show borrowers how to:
- Search the catalog effectively
- View their own account
- Renew items online
- Place their own holds
- Update their profile information

---

## Daily Procedures

### Opening Procedures
1. **Log into system**
2. **Check circulation dashboard**
   - Review overnight activity
   - Check for holds to process
3. **Process hold shelf**
   - Mark available items as ready
   - Print hold slips
   - Send notifications
4. **Check for urgent notices**
   - System messages
   - Overdue alerts

### During the Day
1. **Monitor circulation desk**
2. **Process checkouts and checkins promptly**
3. **Assist borrowers with questions**
4. **Keep hold shelf organized**
5. **Report any system issues**

### Closing Procedures
1. **Process all pending returns**
2. **Update hold shelf**
3. **Check for items left at desk**
4. **Generate daily statistics report**
5. **Log out of system**

---

## Best Practices

### Circulation Excellence
- ✅ **Be prompt**: Process transactions quickly
- ✅ **Be accurate**: Double-check barcodes and cards
- ✅ **Be courteous**: Provide excellent customer service
- ✅ **Inspect items**: Check condition on return
- ✅ **Communicate**: Keep borrowers informed

### System Usage
- ✅ **Log out**: Always log out when leaving desk
- ✅ **Keep credentials secure**: Never share passwords
- ✅ **Report issues**: Immediately report system problems
- ✅ **Stay current**: Attend training sessions

### Data Integrity
- ✅ **Verify information**: Before adding publications
- ✅ **Use standard formats**: For call numbers and ISBNs
- ✅ **Be consistent**: Follow cataloging standards
- ✅ **Update status**: Keep item status current

### Customer Service
- ✅ **Be patient**: Especially with new users
- ✅ **Be helpful**: Go the extra mile
- ✅ **Be knowledgeable**: Know the collection
- ✅ **Be professional**: Maintain privacy and confidentiality

---

## Common Issues and Solutions

### Note: Barcode Scanning Temporarily On Hold
### Note: Barcode Scanning

Barcode scanning is optional and disabled by default. If barcode scanning is available and you prefer to use it, enable the `BARCODE_ENABLED` feature flag in settings. Otherwise use publication ISBN entry or select items from dropdown lists for transactions. If you need to capture barcode values for record-keeping, enter them manually when adding or editing items.

### Issue: Borrower Forgot Library Card
**Solutions**:
1. Ask for photo ID
2. Look up by name in system
3. Verify identity with ID
4. Use library card number from system
5. Remind them to bring card next time

### Issue: Item Shows Available but Can't Find It
**Solutions**:
1. Check nearby shelves (misshelved)
2. Check book carts and processing area
3. Check hold shelf
4. Mark as "Missing" in system
5. Offer to place hold when found

### Issue: System Running Slowly
**Solutions**:
1. Refresh the page
2. Clear browser cache
3. Log out and log back in
4. Report to IT if persists
5. Use backup computer if available

### Issue: Borrower Disputes Overdue
**Solutions**:
1. Check system loan history
2. Verify due date shown on receipt
3. Be polite but firm about policy
4. Escalate to supervisor if needed

### Issue: Multiple People Waiting
**Solutions**:
1. Stay calm and focused
2. Process transactions efficiently
3. Call for backup if available
4. Politely ask for patience
5. Prioritize quick transactions

---

## Tips for Success

### Efficiency Tips
- 💡 Learn keyboard shortcuts
- 💡 Use barcode scanner effectively
- 💡 Keep frequently used references handy
- 💡 Organize your workspace
- 💡 Prepare materials in advance

### Knowledge Building
- 📚 Familiarize yourself with the collection
- 📚 Learn common call number ranges
- 📚 Know where popular items are located
- 📚 Understand circulation policies
- 📚 Stay updated on new acquisitions

### Professional Development
- 🎓 Attend all training sessions
- 🎓 Ask questions when unsure
- 🎓 Share knowledge with colleagues
- 🎓 Learn from experienced staff
- 🎓 Suggest improvements

---

## Quick Reference Guide

### Essential Keyboard Shortcuts
- `Ctrl + F`: Find on page
- `F5`: Refresh page
- `Tab`: Move between fields
- `Enter`: Submit form

### Common Barcodes Prefixes
- `MAN`: Manuals
- `SOP`: Standard Operating Procedures
- `CAP`: Capstone Projects
- `TTP`: Tactics, Techniques, and Procedures
- `LC`: Library Card Numbers

### Important Links
- Circulation Dashboard: `/circulation/dashboard/`
- Search Catalog: `/catalog/search/`
- Manage Publications: `/catalog/manage/`
- Help Documentation: `/help/`

---

## Support and Assistance

### Getting Help
- **Supervisor**: Your direct supervisor
- **IT Support**: For technical issues
- **Administrator**: For account/permission issues
- **Colleagues**: Don't hesitate to ask experienced staff

### Contact Information
- **Help Desk**: support@elibrary.example.com
- **Phone**: (555) 123-4567
- **Office Hours**: Monday-Friday, 8 AM - 5 PM

---

**Document Version**: 1.0  
**Last Updated**: November 2025  
**Prepared by**: e-Library Development Team | RDS | TS

---

## Remember
> Your role as library staff is crucial to the success of the e-Library. Your attention to detail, customer service, and knowledge of the system directly impact user satisfaction and library operations. Thank you for your dedication!
