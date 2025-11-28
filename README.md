# e-Library Management System

A comprehensive Django-based library management system for managing Manuals, SOPs, Capstone Projects, and TTPs.

## Features

### Circulation System Features
 - **Transaction Management**
   - Check-Out / Check-In using Item ID or ISBN (barcode scanning optional)
  - Automated due date calculation
  - Renewals with configurable limits
  - Item status tracking (Available, On Loan, In Transit, etc.)
  - In-Transit management between locations

- **Borrower Management**
  - User registration and profile management
  - Borrowing limits enforcement
  - Automatic blocking/suspension for policy violations
  - Borrower search and activity tracking

- **Holds & Reserves**
  - Hold queue management with position tracking
  - Automated hold notifications
  - Hold shelf management
  - Priority-based hold fulfillment

- **Notifications & Reporting**
  - Automated email notices (pre-due, overdue, hold ready)
  - Statistical reports (circulation stats, overdue items)
  - Borrower demographics and activity reports

### Public Access Catalog (OPAC) Features
- **Search & Discovery**
  - Keyword search across all fields
  - Field-specific search (Title, Author, Subject, Call Number)
  - Advanced search with Boolean operators
  - Faceted search by Type, Language, Publication Date

- **Item Record Display**
  - Complete bibliographic information
  - Call number and location details
  - Abstracts and summaries
  - Cover images

- **Real-Time Integration**
  - Live status display for all copies
  - Availability information with due dates
  - Hold queue position visibility

- **Personal Account Access**
  - View current loans and due dates
  - Online renewal capability
  - Manage hold requests
  - View borrowing history

### Publication Types Supported
- Manuals
- SOPs (Standard Operating Procedures)
- Capstone Projects
- TTPs (Tactics, Techniques, and Procedures)

## Installation

### Prerequisites
- Python 3.8 or higher
- Redis (for Celery task queue)

### Setup Instructions

1. **Clone or extract the project**
   ```
   cd e-library
   ```

2. **Create a virtual environment**
   ```
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

4. **Run database migrations**
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create a superuser**
   ```
   python manage.py createsuperuser
   ```

6. **Load initial data (optional)**
   ```
   python manage.py create_initial_data
   ```

7. **Run the development server**
   ```
   python manage.py runserver
   ```

8. **Start Celery worker (in a separate terminal)**
   ```
   celery -A elibrary worker -l info
   ```

9. **Start Celery beat scheduler (in another terminal)**
   ```
   celery -A elibrary beat -l info
   ```

## Usage

### Access Points

- **Public Catalog**: http://localhost:8000/
- **Admin Interface**: http://localhost:8000/admin/
- **Circulation Dashboard**: http://localhost:8000/circulation/ (staff only)
- **My Account**: http://localhost:8000/accounts/my-account/

### Initial Setup

1. Log in to the admin interface with your superuser credentials
2. Add Publication Types (Manuals, SOPs, Capstone Projects, TTPs)
3. Add Locations (e.g., Main Library, Digital Collection)
4. Add Authors, Publishers, and Subjects
5. Add Publications and their Items (copies)

### User Types

- **Borrower**: Can search catalog, place holds, check out items
- **Staff**: Can perform circulation tasks (checkout, checkin, manage holds)
- **Admin**: Full system access

### Circulation Workflow

1. **Check Out**:
   - Go to Circulation > Check Out
   - Select Item ID from the dropdown or enter the publication ISBN (barcode scanning is optional and gated by feature flag)
   - Enter borrower card number or username
   - System automatically calculates due date

2. **Check In**:
   - Go to Circulation > Check In
   - Select Item ID or enter barcode/ISBN (barcode optional)
   - System checks for holds and overdue status

3. **Renewals**:
   - Staff can renew from borrower detail page
   - Borrowers can renew online from "My Account"
   - Subject to renewal limits and hold restrictions

4. **Holds**:
   - Borrowers place holds from publication detail page
   - Staff manages holds from Circulation > Manage Holds
   - System automatically places items on hold shelf when returned

## Configuration

Key settings in `elibrary/settings.py`:

```python
LIBRARY_NAME = 'Digital e-Library'
MAX_ITEMS_PER_BORROWER = 5
LOAN_PERIOD_DAYS = 14
RENEWAL_LIMIT = 2
PRE_DUE_NOTICE_DAYS = 2
OVERDUE_GRACE_PERIOD_DAYS = 7
```

### Email Configuration

Update email settings for production:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'your-smtp-server.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-password'
DEFAULT_FROM_EMAIL = 'noreply@yourlibrary.com'
```

## Scheduled Tasks

The system uses Celery Beat for scheduled tasks:

- **Daily at 9:00 AM**: Send overdue notices
- **Daily at 9:00 AM**: Send pre-due notices
- **On-demand**: Send hold ready notices

## Reports Available

1. **Overdue Report**: List of all overdue items with borrower information
2. **Circulation Statistics**: 
   - Total checkouts/returns (last 30 days)
   - Most borrowed items
   - Most active borrowers
   - Circulation by publication type

## Technology Stack

- **Framework**: Django 4.2
- **Database**: SQLite (development) / PostgreSQL or MySQL (production)
- **Task Queue**: Celery with Redis
- **Frontend**: Bootstrap 5
- **Forms**: django-crispy-forms

## Security Notes

⚠️ **Before deploying to production**:

1. Change `SECRET_KEY` in settings.py
2. Set `DEBUG = False`
3. Configure `ALLOWED_HOSTS`
4. Use a production database (PostgreSQL/MySQL)
5. Set up proper email backend
6. Configure HTTPS/SSL
7. Set up proper static/media file serving
8. Implement backup procedures

## Project Structure

```
e-library/
├── accounts/           # User authentication and profiles
├── catalog/           # OPAC and publication management
├── circulation/       # Circulation system
├── elibrary/         # Project settings
├── templates/        # HTML templates
├── static/          # Static files (CSS, JS, images)
├── media/           # Uploaded files (cover images)
├── manage.py        # Django management script
└── requirements.txt # Python dependencies
```

## Support

For issues or questions, please refer to the Django documentation at https://docs.djangoproject.com/

## License

This project is provided as-is for educational and library management purposes.
