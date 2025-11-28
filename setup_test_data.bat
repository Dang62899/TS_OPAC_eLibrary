@echo off
REM Test Setup Script for e-Library
REM This script sets up test users and sample data

echo ========================================
echo e-Library Test Setup
echo ========================================
echo.

echo Step 1: Running migrations...
python manage.py makemigrations
python manage.py migrate
echo.

echo Step 2: Creating sample books...
python manage.py create_sample_books
echo.

echo Step 3: Creating test users...
echo Creating test users via Django shell...
python manage.py shell -c "from accounts.models import User; User.objects.filter(username='admin').delete(); admin = User.objects.create_superuser(username='admin', email='admin@example.com', password='admin123', user_type='admin', first_name='System', last_name='Administrator'); admin.library_card_number = 'ADMIN001'; admin.save(); print('✓ Admin user created: admin / admin123')"
python manage.py shell -c "from accounts.models import User; User.objects.filter(username='librarian').delete(); staff = User.objects.create_user(username='librarian', email='staff@example.com', password='staff123', user_type='staff', first_name='Sarah', last_name='Librarian'); staff.library_card_number = 'STAFF001'; staff.save(); print('✓ Staff user created: librarian / staff123')"
python manage.py shell -c "from accounts.models import User; User.objects.filter(username='student').delete(); borrower = User.objects.create_user(username='student', email='student@example.com', password='student123', user_type='borrower', first_name='John', last_name='Student'); borrower.library_card_number = 'LC001'; borrower.save(); print('✓ Borrower user created: student / student123')"
echo.

echo ========================================
echo Test Setup Complete!
echo ========================================
echo.
echo Test Users Created:
echo.
echo 1. ADMINISTRATOR
echo    Username: admin
echo    Password: admin123
echo    Library Card: ADMIN001
echo.
echo 2. STAFF/LIBRARIAN
echo    Username: librarian
echo    Password: staff123
echo    Library Card: STAFF001
echo.
echo 3. BORROWER/USER
echo    Username: student
echo    Password: student123
echo    Library Card: LC001
echo.
echo Sample Data:
echo - 10 Manuals
echo - 10 SOPs
echo - 10 Capstone Projects
echo - 10 TTPs
echo.
echo ========================================
echo Ready to test! Run: python manage.py runserver
echo ========================================
pause
