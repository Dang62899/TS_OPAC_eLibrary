#!/bin/bash

echo "================================================"
echo "e-Library Quick Start Script"
echo "================================================"
echo ""

echo "Step 1: Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "Error creating virtual environment"
    exit 1
fi
echo "Virtual environment created successfully!"
echo ""

echo "Step 2: Activating virtual environment..."
source venv/bin/activate
echo ""

echo "Step 3: Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error installing dependencies"
    exit 1
fi
echo "Dependencies installed successfully!"
echo ""

echo "Step 4: Running database migrations..."
python manage.py makemigrations
python manage.py migrate
if [ $? -ne 0 ]; then
    echo "Error running migrations"
    exit 1
fi
echo "Database migrations completed!"
echo ""

echo "Step 5: Creating superuser..."
echo "Please enter superuser credentials:"
python manage.py createsuperuser
echo ""

echo "Step 6: Creating initial data..."
python manage.py create_initial_data
echo ""

echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "To start the development server, run:"
echo "   python manage.py runserver"
echo ""
echo "To start Celery worker (in a separate terminal):"
echo "   celery -A elibrary worker -l info"
echo ""
echo "To start Celery beat scheduler (in another terminal):"
echo "   celery -A elibrary beat -l info"
echo ""
echo "Access the application at: http://localhost:8000"
echo "Admin interface at: http://localhost:8000/admin"
echo ""
echo "Default test accounts:"
echo "  Staff: username=staff, password=staff123"
echo "  Borrower: username=borrower, password=borrower123"
echo ""
