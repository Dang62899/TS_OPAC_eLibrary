#!/bin/bash
# Production Deployment Setup Script for TS OPAC eLibrary
# Usage: bash deploy_production.sh

set -e  # Exit on error

echo "================================"
echo "TS OPAC eLibrary - Production Deployment Setup"
echo "================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running from correct directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: docker-compose.yml not found!${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi

# ============================================================================
# Step 1: Generate Secret Key
# ============================================================================
echo -e "${YELLOW}Step 1: Generating Django Secret Key...${NC}"
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
echo -e "${GREEN}✓ Secret Key Generated${NC}"
echo ""

# ============================================================================
# Step 2: Check if .env.production exists
# ============================================================================
echo -e "${YELLOW}Step 2: Setting up environment file...${NC}"

if [ ! -f ".env.production" ]; then
    echo "Creating .env.production from template..."
    cp .env.production.example .env.production
    
    # Replace placeholder with actual secret key
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/change-me-with-strong-random-key-at-least-50-chars/$SECRET_KEY/" .env.production
    else
        sed -i "s/change-me-with-strong-random-key-at-least-50-chars/$SECRET_KEY/" .env.production
    fi
    
    echo -e "${GREEN}✓ .env.production created${NC}"
    echo -e "${YELLOW}⚠ Please edit .env.production with your actual configuration${NC}"
else
    echo -e "${GREEN}✓ .env.production already exists${NC}"
fi
echo ""

# ============================================================================
# Step 3: Create necessary directories
# ============================================================================
echo -e "${YELLOW}Step 3: Creating necessary directories...${NC}"

mkdir -p ssl
mkdir -p logs
mkdir -p backups

chmod 700 ssl
chmod 755 logs
chmod 755 backups

echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# ============================================================================
# Step 4: Check SSL certificates
# ============================================================================
echo -e "${YELLOW}Step 4: Checking SSL certificates...${NC}"

if [ -f "ssl/cert.pem" ] && [ -f "ssl/key.pem" ]; then
    echo -e "${GREEN}✓ SSL certificates found${NC}"
else
    echo -e "${YELLOW}⚠ SSL certificates not found!${NC}"
    echo "Options:"
    echo "1. For Let's Encrypt (recommended):"
    echo "   sudo certbot certonly --standalone -d yourdomain.com"
    echo "   sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/cert.pem"
    echo "   sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/key.pem"
    echo ""
    echo "2. For self-signed (development only):"
    echo "   openssl req -x509 -newkey rsa:4096 -nodes -out ssl/cert.pem -keyout ssl/key.pem -days 365"
    echo ""
    echo "Please set up SSL certificates before proceeding"
    echo ""
fi
echo ""

# ============================================================================
# Step 5: Verify environment file configuration
# ============================================================================
echo -e "${YELLOW}Step 5: Verifying configuration...${NC}"

# Check critical variables
CRITICAL_VARS=("DJANGO_SECRET_KEY" "DB_PASSWORD" "EMAIL_HOST_USER" "EMAIL_HOST_PASSWORD" "ALLOWED_HOSTS")

for var in "${CRITICAL_VARS[@]}"; do
    value=$(grep "^${var}=" .env.production | cut -d'=' -f2-)
    if [[ "$value" == *"change-me"* ]] || [ -z "$value" ]; then
        echo -e "${RED}✗ $var not configured properly${NC}"
    else
        echo -e "${GREEN}✓ $var configured${NC}"
    fi
done
echo ""

# ============================================================================
# Step 6: Start Docker containers
# ============================================================================
echo -e "${YELLOW}Step 6: Starting Docker containers...${NC}"

docker-compose down 2>/dev/null || true
docker-compose up -d

# Wait for containers to be ready
echo "Waiting for containers to start..."
sleep 10

echo -e "${GREEN}✓ Containers started${NC}"
echo ""

# ============================================================================
# Step 7: Run migrations
# ============================================================================
echo -e "${YELLOW}Step 7: Running database migrations...${NC}"

docker-compose exec -T web python manage.py migrate --settings=elibrary.settings_production || {
    echo -e "${RED}✗ Migrations failed${NC}"
    echo "Check: docker-compose logs web"
    exit 1
}

echo -e "${GREEN}✓ Migrations completed${NC}"
echo ""

# ============================================================================
# Step 8: Collect static files
# ============================================================================
echo -e "${YELLOW}Step 8: Collecting static files...${NC}"

docker-compose exec -T web python manage.py collectstatic --noinput --settings=elibrary.settings_production

echo -e "${GREEN}✓ Static files collected${NC}"
echo ""

# ============================================================================
# Step 9: Create superuser (optional)
# ============================================================================
echo -e "${YELLOW}Step 9: Setting up superuser...${NC}"
echo "Run the following command to create a superuser:"
echo "docker-compose exec web python manage.py createsuperuser --settings=elibrary.settings_production"
echo ""

# ============================================================================
# Step 10: Health check
# ============================================================================
echo -e "${YELLOW}Step 10: Running health checks...${NC}"

# Wait a bit for application to be ready
sleep 5

echo "Checking application health..."
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/health/ 2>/dev/null || echo "000")

if [ "$HEALTH_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓ Application is healthy (HTTP $HEALTH_RESPONSE)${NC}"
else
    echo -e "${YELLOW}⚠ Application health check returned HTTP $HEALTH_RESPONSE${NC}"
    echo "Check: docker-compose logs web"
fi
echo ""

# ============================================================================
# Summary
# ============================================================================
echo "================================"
echo -e "${GREEN}Production Deployment Setup Completed!${NC}"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Edit .env.production with your actual configuration:"
echo "   - Set ALLOWED_HOSTS to your domain"
echo "   - Configure email settings"
echo "   - Set SENTRY_DSN if using error tracking"
echo ""
echo "2. Create superuser (if not done):"
echo "   docker-compose exec web python manage.py createsuperuser --settings=elibrary.settings_production"
echo ""
echo "3. Verify deployment:"
echo "   docker-compose ps              # Check container status"
echo "   docker-compose logs -f web     # View application logs"
echo "   curl https://localhost/        # Test application"
echo ""
echo "4. Set up monitoring:"
echo "   - Configure Sentry for error tracking"
echo "   - Set up log aggregation"
echo "   - Configure health check alerts"
echo ""
echo "5. Set up automated backups:"
echo "   ./backup_database.sh           # Manual backup"
echo "   crontab -e                     # Add to crontab: 0 2 * * * /path/to/backup_database.sh"
echo ""
echo "6. Configure SSL certificate renewal:"
echo "   sudo systemctl enable certbot.timer"
echo "   sudo systemctl start certbot.timer"
echo ""
echo "Documentation:"
echo "   - DAYS_7-8_PRODUCTION_GUIDE.md"
echo "   - QUICK_START_GUIDE.md"
echo "   - .env.production.example"
echo ""
