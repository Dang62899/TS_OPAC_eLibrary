@echo off
REM Production deployment script for OPAC eLibrary (Windows)
REM Run this script after copying the project to your production server

echo =========================================
echo OPAC eLibrary - Production Setup Script
echo =========================================
echo.

REM Check if .env file exists
if not exist .env (
    echo Error: .env file not found!
    echo Please copy .env.example to .env and configure it first.
    echo.
    echo Run: copy .env.example .env
    echo Then edit .env with your production settings.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo.
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Create necessary directories
echo.
echo Creating required directories...
if not exist logs mkdir logs
if not exist media\covers mkdir media\covers
if not exist media\documents mkdir media\documents
if not exist staticfiles mkdir staticfiles

REM Run migrations
echo.
echo Running database migrations...
python manage.py migrate

REM Create superuser (if needed)
echo.
set /p createsu="Do you want to create a superuser? (y/n): "
if /i "%createsu%"=="y" (
    python manage.py createsuperuser
)

REM Load initial data
echo.
set /p loaddata="Do you want to load initial data (publication types, locations)? (y/n): "
if /i "%loaddata%"=="y" (
    python manage.py create_initial_data
)

REM Collect static files
echo.
echo Collecting static files...
python manage.py collectstatic --noinput

REM Test configuration
echo.
echo Testing Django configuration...
python manage.py check --deploy

echo.
echo =========================================
echo Setup complete!
echo =========================================
echo.
echo Next steps:
echo 1. Configure your web server (IIS/Apache)
echo 2. Set up Gunicorn or Waitress
echo 3. Start Celery worker and beat
echo 4. Configure SSL certificate
echo 5. Set up database backups
echo.
echo See DEPLOYMENT.md for detailed instructions.
echo.
pause
