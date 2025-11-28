# Administrator User Manual
## e-Library Management System

---

## Table of Contents
1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Dashboard Overview](#dashboard-overview)
4. [User Management](#user-management)
5. [Catalog Management](#catalog-management)
6. [Circulation Management](#circulation-management)
7. [Reports and Analytics](#reports-and-analytics)
8. [System Configuration](#system-configuration)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Introduction

Welcome to the e-Library Management System Administrator Manual. As an administrator, you have full control over the entire system, including user management, catalog management, circulation operations, and system configuration.

### Administrator Privileges
- **Full system access**: Complete control over all features and functions
- **User management**: Create, edit, and delete user accounts (Admins, Staff, Borrowers)
- **Catalog management**: Add, edit, and delete publications and items
- **Circulation control**: Override circulation policies and manage all transactions
- **System configuration**: Configure system settings and parameters
- **Reports access**: Generate and view all system reports
- **Audit capabilities**: Monitor system activity and user actions

---

## Getting Started

### Logging In
1. Navigate to the e-Library website
2. Click **Login** in the top navigation bar
3. Enter your administrator credentials
   - Username: Your admin username
   - Password: Your secure password
4. Click **Login**

### First-Time Setup
After logging in for the first time:
1. Update your profile information
2. Change your default password
3. Configure your notification preferences
4. Familiarize yourself with the admin dashboard

---

## Dashboard Overview

The administrator dashboard provides a comprehensive overview of library operations:

### Key Metrics Displayed
- **Active Loans**: Current number of items checked out
- **Overdue Items**: Items past their due date
- **Pending Holds**: Items on hold waiting to be picked up
- **Recent Activity**: Latest checkouts and returns
- **User Statistics**: Active users and blocked accounts
- **Catalog Statistics**: Total publications and items

### Navigation Menu
- **Home**: Return to the main catalog
- **Search Catalog**: Advanced search functionality
- **Circulation**: Access circulation dashboard
- **Manage Users**: User management interface
- **Manage Catalog**: Publication and item management
- **My Account**: View and edit your profile

---

## User Management

### Viewing All Users
1. Click **Manage Users** in the navigation menu
2. View the complete list of all users
3. Use filters to search by:
   - Username, name, or email
   - User type (Admin, Staff, Borrower)
   - Account status (Active, Blocked)

### Creating New Users

#### Creating an Admin User
1. Go to **Manage Users**
2. Click **Add New User**
3. Fill in required information:
   - Username (unique)
   - Email address
   - First and last name
   - Password (will be sent to user)
4. Select **User Type**: Administrator
5. Click **Register**
6. Notify the user of their account credentials

#### Creating a Staff User
1. Follow the same steps as creating an admin
2. Select **User Type**: Staff
3. Set appropriate permissions and access levels
4. Assign maximum items they can manage

#### Creating a Borrower Account
1. Users can self-register, or you can create accounts
2. For manual creation, select **User Type**: Borrower
3. Generate or assign a library card number
4. Set maximum items allowed (default: 5)

### Editing User Accounts
1. Find the user in **Manage Users**
2. Click the **Edit** button next to their name
3. Modify any of the following:
   - Personal information
   - User type
   - Library card number
   - Maximum items allowed
   - Account status (Active/Blocked)
4. Click **Save Changes**

### Blocking/Unblocking Users
1. Navigate to the user's account
2. Check the **Is Blocked** checkbox to block
3. Enter a **Block Reason** (e.g., "Excessive overdue items")
4. Click **Save Changes**
5. To unblock, uncheck **Is Blocked** and clear the reason

### Deleting User Accounts
**⚠️ Warning**: Deletion is permanent and cannot be undone!

1. Go to **Manage Users**
2. Find the user to delete
3. Click **Delete** button
4. Confirm the deletion
5. All user data and history will be permanently removed

### Best Practices for User Management
- ✅ Regularly review user accounts for inactive users
- ✅ Use descriptive block reasons
- ✅ Verify user information before creating accounts
- ✅ Limit the number of admin accounts
- ✅ Audit staff permissions periodically
- ❌ Do not share admin credentials
- ❌ Do not delete users with active loans

---

## Catalog Management

### Viewing Publications
1. Click **Manage Catalog** in the navigation menu
2. Browse all publications in the system
3. Use search and filters:
   - Search by title, ISBN, or call number
   - Filter by publication type
   - Sort by date, title, or popularity

### Adding New Publications

#### Via Admin Interface
1. Click **Add New Publication** in Manage Catalog
2. Fill in all required fields:
   - **Title**: Full publication title
   - **Subtitle**: Optional subtitle
   - **Publication Type**: Manual, SOP, Capstone Project, TTP
   - **Authors**: Select or create authors
   - **Subjects**: Assign subject categories
   - **Publisher**: Select or create publisher
   - **Publication Date**: Year published
   - **ISBN**: If applicable
   - **Call Number**: Classification number
   - **Language**: Default is English
   - **Pages**: Number of pages
   - **Abstract**: Brief description
3. Click **Save**

#### Adding Physical Items
After creating a publication:
1. Scroll to the **Items** section
2. Click **Add Item**
3. Enter:
   - **Barcode**: (Optional) Unique barcode number — barcode scanning is disabled by default. Use ISBN or Item ID for transactions.
   - **Location**: Physical location in library
   - **Status**: Available, Checked Out, In Transit, etc.
   - **Condition**: Excellent, Good, Fair, Poor
4. Save the item
5. Repeat for additional copies

### Editing Publications
1. Find the publication in **Manage Catalog**
2. Click **Edit**
3. Modify any fields as needed
4. Update authors, subjects, or other metadata
5. Click **Save Changes**

### Deleting Publications
**⚠️ Warning**: This deletes the publication and ALL associated items!

1. Navigate to the publication
2. Click **Delete**
3. Confirm deletion
4. The publication and all items will be removed

### Managing Items
- **Update Status**: Change item availability
- **Update Condition**: Reflect physical condition
- **Move Locations**: Transfer items between locations
- **Withdraw Items**: Remove damaged or lost items

### Best Practices for Catalog Management
- ✅ Use consistent call number formatting
- ✅ Add detailed abstracts for searchability
- ✅ Assign multiple relevant subjects
- ✅ Include all authors and contributors
- ✅ Verify ISBN accuracy
- ✅ Add cover images when available
- ❌ Do not delete publications with active loans
- ❌ Do not use special characters in barcodes

---

## Circulation Management

### Circulation Dashboard
Access via **Circulation** in the main menu

#### Dashboard Features
- **Active Loans**: View all current checkouts
- **Overdue Report**: Identify overdue items
- **Holds Management**: Process holds and reservations
- **In-Transit Items**: Track items moving between locations

### Checking Out Items
1. Click **Checkout** in Circulation menu
2. Enter the publication's **ISBN** (barcode scanning is optional). Barcode entry is still stored per item but is not required for transactions.
3. Scan or enter the **borrower's library card number**
4. Verify borrower information and eligibility
5. Set the due date (or use default)
6. Click **Check Out**
7. Print or email receipt

### Checking In Items
1. Click **Checkin** in Circulation menu
2. Enter the publication's **ISBN** or select from the returned item list. Barcode scanning is optional and disabled by default.
3. System will automatically process return
4. Note any overdue fines
5. Check item condition
6. Update status if damaged

### Managing Holds
1. Go to **Manage Holds** in Circulation
2. View holds by status:
   - **Waiting**: Hold placed, waiting for availability
   - **Ready**: Item available for pickup
   - **Picked Up**: Hold fulfilled
3. Mark items as ready when available
4. Send notifications to borrowers
5. Cancel holds if needed

### Managing Overdue Items
1. Click **Overdue Report**
2. Review list of overdue items
3. Send reminder notifications
4. Contact borrowers with excessive overdues
5. Block accounts if necessary

### Override Functions (Admin Only)
- **Extend Due Dates**: Override circulation policies
- **Waive Fines**: Remove penalties
- **Force Checkout**: Allow blocked users to borrow
- **Recall Items**: Request early return of items

---

## Reports and Analytics

### Available Reports
1. **Circulation Statistics**
   - Total checkouts and returns
   - Most borrowed items
   - Peak usage times

2. **User Reports**
   - Active vs. inactive users
   - Borrowing patterns
   - Blocked accounts

3. **Collection Reports**
   - Holdings by type
   - Items never borrowed
   - Items needing replacement

4. **Overdue Reports**
   - Current overdue items
   - Overdue trends
   - User compliance rates

### Generating Reports
1. Navigate to **Reports** section
2. Select report type
3. Set date range and filters
4. Click **Generate Report**
5. Export as PDF or Excel

---

## System Configuration

### General Settings
- Library name and information
- Operating hours
- Contact information
- Logo and branding

### Circulation Policies
- Default loan period
- Maximum items per user
- Renewal limits
- Fine calculations
- Hold policies

### User Settings
- Registration requirements
- Library card format
- Password policies
- User types and permissions

### Email Notifications
- Overdue notices
- Hold notifications
- Welcome emails
- Password resets

---

## Best Practices

### Security
- ✅ Use strong, unique passwords
- ✅ Log out when finished
- ✅ Regularly review user permissions
- ✅ Enable two-factor authentication (if available)
- ✅ Monitor system logs for unusual activity

### Data Management
- ✅ Perform regular backups
- ✅ Validate data before deletion
- ✅ Keep catalog information current
- ✅ Archive old records appropriately

### User Support
- ✅ Respond promptly to user issues
- ✅ Provide clear instructions
- ✅ Document policy changes
- ✅ Train staff regularly

---

## Troubleshooting

### Common Issues and Solutions

#### Cannot Create New User
- **Problem**: Error when creating user account
- **Solutions**:
  - Verify username is unique
  - Check that email is valid
  - Ensure all required fields are filled
  - Verify library card number format

#### Publication Won't Delete
- **Problem**: Cannot remove publication
- **Solutions**:
  - Check for active loans on items
  - Verify no pending holds
  - Check for linked records
  - Contact system administrator

#### Reports Not Generating
- **Problem**: Reports fail to generate
- **Solutions**:
  - Verify date range is valid
  - Check filter settings
  - Ensure sufficient permissions
  - Try a smaller date range

#### User Cannot Login
- **Problem**: User reports login failure
- **Solutions**:
  - Verify account is not blocked
  - Reset password
  - Check username spelling
  - Verify account exists

---

## Support and Contact

For technical support or questions:
- **System Administrator**: [Contact Information]
- **Email**: support@elibrary.example.com
- **Phone**: (555) 123-4567

---

**Document Version**: 1.0  
**Last Updated**: November 2025  
**Prepared by**: e-Library Development Team | RDS | TS
