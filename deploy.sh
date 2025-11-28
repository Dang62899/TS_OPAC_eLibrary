#!/bin/bash

# Production deployment script for OPAC eLibrary
# Run this script after copying the project to your production server

echo "========================================="
echo "OPAC eLibrary - Production Setup Script"
echo "========================================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.example to .env and configure it first."
    echo ""
    echo "Run: cp .env.example .env"
    echo "Then edit .env with your production settings."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo ""
echo "Creating required directories..."
mkdir -p logs
mkdir -p media/covers
mkdir -p media/documents
mkdir -p staticfiles

# Set proper permissions
echo "Setting permissions..."
chmod 755 logs media staticfiles

# Run migrations
echo ""
echo "Running database migrations..."
python manage.py migrate

# Create superuser (if needed)
echo ""
read -p "Do you want to create a superuser? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python manage.py createsuperuser
fi

# Load initial data
echo ""
read -p "Do you want to load initial data (publication types, locations)? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python manage.py create_initial_data
fi

# Collect static files
echo ""
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Test configuration
echo ""
echo "Testing Django configuration..."
python manage.py check --deploy

echo ""
echo "========================================="
echo "Setup complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Configure your web server (Nginx/Apache)"
echo "2. Set up Gunicorn or uWSGI"
echo "3. Start Celery worker and beat"
echo "4. Configure SSL certificate"
echo "5. Set up database backups"
echo ""
echo "See DEPLOYMENT.md for detailed instructions."
echo ""
