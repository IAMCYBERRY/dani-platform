#!/bin/bash
set -e

echo "🚀 Deploying D.A.N.I Platform..."

# Create deployment directory
mkdir -p ~/dani-platform
cd ~/dani-platform

# Download configuration files
curl -s -O https://raw.githubusercontent.com/YOUR_USERNAME/dani-platform/main/docker-compose.production.yml
curl -s -O https://raw.githubusercontent.com/YOUR_USERNAME/dani-platform/main/.env.example

# Setup environment
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration"
    echo "   Then run: docker-compose -f docker-compose.production.yml up -d"
    exit 1
fi

# Update image names
sed -i 's/your-dockerhub-username/YOUR_ACTUAL_USERNAME/g' docker-compose.production.yml

# Pull latest images
docker-compose -f docker-compose.production.yml pull

# Start services
docker-compose -f docker-compose.production.yml up -d

# Wait for services
echo "Waiting for services to start..."
sleep 45

# Run migrations
echo "Running database migrations..."
docker-compose -f docker-compose.production.yml exec -T web python manage.py migrate

# Check if superuser exists, create if not
SUPERUSER_EXISTS=$(docker-compose -f docker-compose.production.yml exec -T web python manage.py shell -c "from accounts.models import User; print(User.objects.filter(email='admin@dani.local').exists())" 2>/dev/null | tail -1)

if [ "$SUPERUSER_EXISTS" = "False" ]; then
    echo "Creating default superuser..."
    docker-compose -f docker-compose.production.yml exec -T web python manage.py shell -c "
from accounts.models import User
User.objects.create_superuser(
    email='admin@dani.local',
    password='ChangeMe123!',
    first_name='System',
    last_name='Administrator',
    role='admin'
)
print('Superuser created successfully')
"
fi

echo ""
echo "🎉 D.A.N.I Platform deployed successfully!"
echo ""
echo "🌐 Access your platform:"
echo "   Main app: http://$(curl -s ifconfig.me):8000/"
echo "   Admin:    http://$(curl -s ifconfig.me):8000/admin/"
echo ""
echo "🔐 Default credentials:"
echo "   Email:    admin@dani.local"
echo "   Password: ChangeMe123!"
echo ""
echo "⚠️  IMPORTANT: Change the default password immediately!"
echo ""
echo "📊 Service status:"
docker-compose -f docker-compose.production.yml ps