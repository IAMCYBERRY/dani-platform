#!/bin/bash

# HRIS Platform Setup Script
# This script provides a more reliable setup process

set -e  # Exit on any error

echo "🚀 HRIS Platform Setup Starting..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
print_status "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_success "Prerequisites check passed!"

# Setup environment file
print_status "Setting up environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    print_success "Created .env file from template"
    print_warning "Please review and edit .env file if needed"
else
    print_warning ".env file already exists, skipping"
fi

# Clean up any existing containers
print_status "Cleaning up any existing containers..."
docker-compose down -v --remove-orphans 2>/dev/null || true

# Build the application
print_status "Building Docker images..."
docker-compose build

# Start the services
print_status "Starting services..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
print_status "This may take a few minutes on first run..."

# Wait for PostgreSQL
print_status "Waiting for PostgreSQL..."
for i in {1..30}; do
    if docker-compose exec -T postgres pg_isready -U postgres >/dev/null 2>&1; then
        print_success "PostgreSQL is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "PostgreSQL failed to start within 60 seconds"
        print_error "Check logs with: docker-compose logs postgres"
        exit 1
    fi
    echo -n "."
    sleep 2
done

# Wait for Django
print_status "Waiting for Django application..."
for i in {1..30}; do
    if docker-compose exec -T web python -c "import django; print('Django ready')" >/dev/null 2>&1; then
        print_success "Django application is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "Django application failed to start within 60 seconds"
        print_error "Check logs with: docker-compose logs web"
        exit 1
    fi
    echo -n "."
    sleep 2
done

# Create and run database migrations
print_status "Creating database migrations..."
docker-compose exec web python manage.py makemigrations accounts
docker-compose exec web python manage.py makemigrations employees
docker-compose exec web python manage.py makemigrations recruitment

print_status "Running database migrations..."
if docker-compose exec web python manage.py migrate; then
    print_success "Database migrations completed!"
else
    print_error "Database migrations failed!"
    print_error "Check logs with: docker-compose logs web"
    exit 1
fi

# Create superuser
print_status "Creating superuser account..."
docker-compose exec web python manage.py shell << 'EOF'
from accounts.models import User
import os

email = 'admin@hris.local'
password = 'admin123'

if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(
        email=email,
        password=password,
        first_name='System',
        last_name='Administrator',
        role='admin'
    )
    print(f"✓ Superuser {email} created successfully!")
else:
    print(f"✓ Superuser {email} already exists.")
EOF

# Collect static files
print_status "Collecting static files..."
docker-compose exec web python manage.py collectstatic --noinput >/dev/null 2>&1

# Final status check
print_status "Performing final health check..."
sleep 3

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    print_success "All services are running!"
else
    print_error "Some services are not running properly"
    docker-compose ps
    exit 1
fi

# Success message
echo ""
echo "🎉 ================================================================"
echo "🎉 HRIS Platform Setup Complete!"
echo "🎉 ================================================================"
echo ""
print_success "Application is ready to use!"
echo ""
echo "📱 Access URLs:"
echo "   • Main API:      http://localhost:8000/api/"
echo "   • Admin Panel:   http://localhost:8000/admin/"
echo "   • API Docs:      http://localhost:8000/api/ (browsable)"
echo ""
echo "🔐 Default Login Credentials:"
echo "   • Email:         admin@hris.local"
echo "   • Password:      admin123"
echo ""
echo "🛠️  Useful Commands:"
echo "   • View logs:     docker-compose logs -f"
echo "   • Stop services: docker-compose down"
echo "   • Restart:       docker-compose restart"
echo "   • Shell access:  docker-compose exec web bash"
echo ""
print_warning "⚠️  Remember to change the default admin password!"
print_warning "⚠️  Review the .env file for production deployment!"
echo ""