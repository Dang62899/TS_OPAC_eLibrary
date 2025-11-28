# e-Library Installation & Usage Guide

## Table of Contents
1. [Installation](#installation)
2. [Initial Setup](#initial-setup)
3. [Usage Guide](#usage-guide)
4. [Feature Walkthrough](#feature-walkthrough)
5. [Common Tasks](#common-tasks)
6. [Troubleshooting](#troubleshooting)

---

## Installation

### Option 1: Quick Install (Recommended)

**Windows:**
```batch
cd e-library
setup.bat
```

**Linux/Mac:**
```bash
cd e-library
chmod +x setup.sh
./setup.sh
```

This automated script will:
- Create virtual environment
- Install dependencies
- Run migrations
- Create superuser (you'll be prompted)
- Load sample data

### Option 2: Manual Installation

1. **Navigate to project directory:**
   ```batch
   cd e-library
   ```

2. **Create virtual environment:**
   ```batch
   python -m venv venv
   ```

3. **Activate virtual environment:**
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. **Install dependencies:**
   ```batch
   pip install -r requirements.txt
   ```

5. **Run database migrations:**
   ```batch
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser account:**
   ```batch
   python manage.py createsuperuser
   ```
   Enter username, email, and password when prompted.

7. **Load initial data (optional but recommended):**
   ```batch
   python manage.py create_initial_data
   ```

8. **Run development server:**
   ```batch
   python manage.py runserver
   ```

9. **Access the application:**
   Open browser: http://localhost:8000

---

## Initial Setup

### 1. Login to Admin Panel

Visit: http://localhost:8000/admin

Login with your superuser credentials.

### 2. Review Pre-loaded Data

The `create_initial_data` command creates:

**Publication Types:**
- Manuals (MAN)
- SOPs (SOP)
- Capstone Projects (CAP)
- TTPs (TTP)

**Locations:**
- Main Library (MAIN)
- Digital Collection (DIGI)
- Reference Section (REF)
- Archives (ARCH)

**Test Users:**
- Staff (username: staff, password: staff123)
- Borrower (username: borrower, password: borrower123)

**Sample Publications:**
- System Administration Manual (with 3 copies)
- Emergency Response Procedures (with 2 copies)

### 3. Add Your Own Content

#### Add Publications:
1. Admin > Catalog > Publications > Add Publication
2. Fill in:
   - Title (required)
   - Publication Type (required)
   - Authors (select or add new)
   - Subjects
   - Call number
   - Abstract/Summary
   - Cover image (optional)

#### Add Items (Copies):
1. After creating publication, scroll to "Items" section
2. Click "Add another Item"
3. Enter:
   - Barcode (unique identifier)
   - Location
   - Status (usually "Available")

---

## Usage Guide

### For Borrowers

#### 1. Register Account
- Go to homepage
- Click "Register"
- Fill in registration form
- Login with credentials

#### 2. Search Catalog
- Use search box on homepage
- Or visit Search page
- Use advanced search for filters:
  - Publication type
  - Language
  - Date range
  - Available only

#### 3. View Publication Details
- Click any publication title
- View complete information
- Check availability status
- See all copies and locations

#### 4. Place Hold
- On publication detail page
- Click "Place Hold"
- Select pickup location
- Receive email when ready

#### 5. Manage Account
- Go to "My Account"
- View active loans
- See due dates
- Renew items (if eligible)
- View/cancel holds
- Check borrowing history

#### 6. Renew Items
- From "My Account"
- Click "Renew" next to loan
- Can renew up to 2 times (configurable)
- Cannot renew if overdue or has holds

### For Staff

#### 1. Access Circulation Dashboard
- Login as staff user
- Go to "Circulation" menu
- View statistics:
  - Active loans
  - Overdue items
  - Holds waiting/ready
  - Items in transit

#### 2. Check Out Items

**Process:**
1. Circulation > Check Out
2. Scan/enter item barcode (e.g., MAN001-001)
3. Enter borrower card number or username
4. Add notes (optional)
5. Click "Check Out"

**System automatically:**
- Calculates due date
- Updates item status
- Checks borrowing limits
- Records transaction

#### 3. Check In Items

**Process:**
1. Circulation > Check In
2. Scan/enter item barcode
3. Click "Check In"

**System automatically:**
- Marks loan as returned
- Checks for holds
- Places on hold shelf if needed
- Detects overdue items

#### 4. Manage Holds

**View Holds:**
- Circulation > Manage Holds
- See "Waiting" and "Ready" tabs

**Process Hold:**
1. When item returned, check holds
2. If hold exists, set as "Ready"
3. System sends email notification
4. Place item on hold shelf

#### 5. Borrower Management

**Search Borrowers:**
- Circulation > Borrowers
- Search by name, username, or card number
- Filter by blocked status

**View Borrower Details:**
- Click "View Details"
- See active loans
- View holds
- Check borrowing history
- View account status

**Block/Unblock:**
- From borrower detail page
- Click "Block" button
- Enter reason
- Borrower cannot borrow until unblocked

#### 6. Reports

**Overdue Report:**
- Circulation > Reports > Overdue Items
- See all overdue loans
- View days overdue
- Access borrower contact info

**Circulation Statistics:**
- Circulation > Reports > Circulation Statistics
- View last 30 days:
  - Total checkouts/returns
  - Most borrowed items
  - Most active borrowers
  - Statistics by publication type

---

## Feature Walkthrough

### Complete Checkout Example

1. **Borrower "John Reader" visits library**
2. **Staff opens Circulation > Check Out**
3. **Staff scans item barcode: MAN001-001**
4. **Staff scans borrower card: LIB001**
5. **System validates:**
   - Item is available
   - Borrower not blocked
   - Under borrowing limit (5 items)
6. **System creates loan:**
   - Due date: +14 days
   - Status: Active
   - Item status: On Loan
7. **Confirmation displayed**

### Complete Hold Example

1. **All copies of a publication are checked out**
2. **Borrower searches catalog, finds publication**
3. **Borrower clicks "Place Hold"**
4. **Selects pickup location**
5. **Hold created:**
   - Status: Waiting
   - Queue position: 1
6. **When item returned:**
   - Staff checks in item
   - System detects hold
   - Hold status: Ready
   - Email sent to borrower
   - Item placed on hold shelf
7. **Borrower picks up item within 7 days**

### Renewal Example

1. **Borrower has item due in 5 days**
2. **Logs into "My Account"**
3. **Clicks "Renew" next to loan**
4. **System checks:**
   - Not overdue ✓
   - Under renewal limit (2) ✓
   - No holds on item ✓
5. **New due date: +14 days**
6. **Renewal count: 1**

---

## Common Tasks

### Add New Staff User
1. Admin > Accounts > Users > Add User
2. Set user_type = "staff"
3. Assign library card number
4. Set permissions if needed

### Add Publication with Multiple Copies
1. Create publication record
2. In same form, use "Items" inline section
3. Add multiple items with unique barcodes
4. Set location and status for each

### Handle Damaged Item
1. Admin > Catalog > Items
2. Find item by barcode
3. Change status to "Damaged"
4. Add notes about damage
5. Item won't appear as available

### Change Loan Period
1. Edit `elibrary/settings.py`
2. Find: `LOAN_PERIOD_DAYS = 14`
3. Change to desired days
4. Restart server

### Send Manual Notification
1. Admin > Circulation > Notifications
2. Create notification
3. Set type, borrower, message
4. System will send on next Celery task run

---

## Troubleshooting

### Cannot Login
- Verify username/password
- Check if account is active
- Check if borrower is blocked (staff can unblock)

### Item Won't Check Out
**Possible reasons:**
- Item not in "Available" status
- Borrower blocked
- Borrower at loan limit
- Check error message for details

**Solutions:**
- Check item status in Admin
- Check borrower status
- Increase max_items_allowed for borrower

### Renewal Failed
**Reasons:**
- Already renewed 2 times (limit reached)
- Item is overdue
- Item has holds

**Solution:**
- Return and re-check out (staff)
- Clear holds if appropriate

### Email Not Sending
**Check:**
1. EMAIL_BACKEND in settings.py
2. Celery worker is running
3. Celery beat is running
4. Redis is running
5. Email configuration correct

**Test:**
```python
python manage.py shell
from django.core.mail import send_mail
send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
```

### Celery Tasks Not Running
**Start services:**
```batch
# Terminal 1 - Worker
celery -A elibrary worker -l info

# Terminal 2 - Beat
celery -A elibrary beat -l info
```

**Check Redis:**
- Ensure Redis server is running
- Default: localhost:6379

### Database Errors
**Reset database:**
```batch
del db.sqlite3
python manage.py migrate
python manage.py createsuperuser
python manage.py create_initial_data
```

### Import Errors
**Ensure:**
1. Virtual environment is activated
2. In correct directory (e-library/)
3. All dependencies installed: `pip install -r requirements.txt`

### Static Files Not Loading
**Run:**
```batch
python manage.py collectstatic
```

### Permission Denied
**For staff functions:**
- User must have user_type = 'staff' or 'admin'
- Check in Admin > Accounts > Users

---

## Additional Resources

- **Django Documentation**: https://docs.djangoproject.com/
- **Celery Documentation**: https://docs.celeryproject.org/
- **Bootstrap Documentation**: https://getbootstrap.com/docs/

---

## Getting Help

1. Check error messages carefully
2. Review this guide and README.md
3. Check Django error pages (when DEBUG=True)
4. Verify configuration in settings.py
5. Check server console for errors

---

**Happy Library Managing! 📚**
