# e-Library Quick Start Guide

## Quick Installation (Windows)

Simply run the setup script:
```batch
setup.bat
```

This will:
1. Create a virtual environment
2. Install all dependencies
3. Run database migrations
4. Prompt you to create a superuser
5. Load initial sample data

## Manual Installation

### 1. Create Virtual Environment
```batch
python -m venv venv
venv\Scripts\activate
```

### 2. Install Dependencies
```batch
pip install -r requirements.txt
```

### 3. Database Setup
```batch
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser
```batch
python manage.py createsuperuser
```

### 5. Load Initial Data (Optional)
```batch
python manage.py create_initial_data
```

### 6. Run Development Server
```batch
python manage.py runserver
```

Visit: http://localhost:8000

## Default Test Accounts

After running `create_initial_data`:

**Staff Account:**
- Username: `staff`
- Password: `staff123`
- Access to circulation functions

**Borrower Account:**
- Username: `borrower`
- Password: `borrower123`
- Can search catalog, place holds, borrow items

## First Steps

### 1. Access Admin Panel
Go to http://localhost:8000/admin and login with your superuser account.

### 2. Add Content
- **Publication Types**: Already loaded (Manuals, SOPs, Capstone Projects, TTPs)
- **Locations**: Already loaded (Main Library, Digital Collection, etc.)
- **Publications**: Add your publications via Admin > Catalog > Publications
- **Items**: Add physical/digital copies via the Publication's detail page

### 3. Test the System

**As a Borrower:**
1. Login with `borrower` / `borrower123`
2. Search for publications
3. Place a hold on an item
4. View "My Account" to see holds

**As Staff:**
1. Login with `staff` / `staff123`
2. Go to Circulation Dashboard
3. Check out an item:
   - Barcode: `MAN001-001` (or any barcode from sample data)
   - Borrower: `borrower` or `LIB001`
4. Check in an item
5. Manage holds
6. View reports

## Key Features to Test

### Circulation System
1. **Check Out**: `/circulation/checkout/`
   - Scan item barcode
   - Enter borrower card number
   - System calculates due date automatically

2. **Check In**: `/circulation/checkin/`
   - Scan item barcode
   - System checks for holds and overdue status

3. **Manage Holds**: `/circulation/holds/manage/`
   - View waiting holds
   - Set holds as ready for pickup

4. **Borrower Management**: `/circulation/borrowers/`
   - Search borrowers
   - View borrower activity
   - Block/unblock borrowers

### Public Catalog (OPAC)
1. **Search**: `/search/`
   - Keyword search
   - Field-specific search
   - Advanced filters

2. **Browse**: Homepage
   - By publication type
   - By subject
   - By author

3. **Publication Details**: Click any publication
   - View all bibliographic info
   - See available copies
   - Check real-time status
   - Place holds

4. **My Account**: `/accounts/my-account/`
   - View active loans
   - Renew items online
   - Manage holds
   - View borrowing history

## Email Notifications (Optional)

To enable email notifications, you'll need Redis and Celery running:

### Install Redis
Download and install Redis for Windows or use WSL.

### Start Celery Worker
In a new terminal:
```batch
venv\Scripts\activate
celery -A elibrary worker -l info
```

### Start Celery Beat (Scheduled Tasks)
In another terminal:
```batch
venv\Scripts\activate
celery -A elibrary beat -l info
```

### Scheduled Tasks
- **9:00 AM Daily**: Send overdue notices
- **9:00 AM Daily**: Send pre-due notices

## Configuration

Edit `elibrary/settings.py` to customize:

```python
# Library Settings
LIBRARY_NAME = 'Your Library Name'
MAX_ITEMS_PER_BORROWER = 5
LOAN_PERIOD_DAYS = 14
RENEWAL_LIMIT = 2
PRE_DUE_NOTICE_DAYS = 2
```

## Troubleshooting

### Import Errors
If you see import errors, make sure:
1. Virtual environment is activated
2. All dependencies are installed: `pip install -r requirements.txt`
3. Migrations are run: `python manage.py migrate`

### No Module Named 'catalog'
Make sure you're in the correct directory (e-library/) and the virtual environment is activated.

### Database Errors
Delete `db.sqlite3` and run migrations again:
```batch
del db.sqlite3
python manage.py migrate
python manage.py createsuperuser
python manage.py create_initial_data
```

## Project Structure

```
e-library/
├── accounts/              # User authentication & profiles
│   ├── models.py         # Custom User model
│   ├── views.py          # Login, register, profile views
│   └── forms.py          # User forms
├── catalog/              # OPAC & publications
│   ├── models.py         # Publication, Item, Author, etc.
│   ├── views.py          # Search, browse, detail views
│   └── forms.py          # Search forms
├── circulation/          # Circulation system
│   ├── models.py         # Loan, Hold, InTransit, Notification
│   ├── views.py          # Checkout, checkin, holds, reports
│   ├── forms.py          # Circulation forms
│   └── tasks.py          # Celery tasks for notifications
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── catalog/          # Catalog templates
│   ├── circulation/      # Circulation templates
│   └── accounts/         # Account templates
├── elibrary/             # Project settings
│   ├── settings.py       # Configuration
│   ├── urls.py           # URL routing
│   └── celery.py         # Celery configuration
└── manage.py             # Django management script
```

## Next Steps

1. **Customize Publication Types**: Add or modify types in Admin
2. **Add Real Data**: Import your actual publications and items
3. **Configure Email**: Set up SMTP for real email notifications
4. **Add Users**: Create staff and borrower accounts
5. **Configure Policies**: Adjust loan periods, renewal limits, etc.
6. **Backup**: Set up regular database backups

## Support

For Django documentation: https://docs.djangoproject.com/
For Celery documentation: https://docs.celeryproject.org/

## Security Reminder

Before deploying to production:
1. Change `SECRET_KEY` in settings.py
2. Set `DEBUG = False`
3. Configure `ALLOWED_HOSTS`
4. Use production database (PostgreSQL/MySQL)
5. Set up SSL/HTTPS
6. Configure production email backend
