#!/bin/bash
set -e

echo "🚀 Deploying D.A.N.I Platform..."

# Create deployment directory
mkdir -p ~/dani-platform
cd ~/dani-platform

# Create required directories with proper permissions
echo "📁 Creating required directories..."
mkdir -p logs media staticfiles
chmod 755 logs media staticfiles

# Download configuration files
echo "📥 Downloading configuration files..."
curl -s -O https://raw.githubusercontent.com/IAMCYBERRY/dani-platform/main/docker-compose.production.yml
curl -s -O https://raw.githubusercontent.com/IAMCYBERRY/dani-platform/main/.env.example

# Setup environment
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration"
    echo "   Then re-run this script"
    exit 1
fi

# Check Docker permissions
if ! docker ps >/dev/null 2>&1; then
    echo "❌ Docker permission denied. Please run:"
    echo "   sudo usermod -aG docker \$USER"
    echo "   Then log out and back in, or run: newgrp docker"
    exit 1
fi

# Update image names
sed -i 's/iamcyberry/YOUR_ACTUAL_USERNAME/g' docker-compose.production.yml

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
VM_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}' || echo "localhost")
echo "   Main app: http://$VM_IP:8000/"
echo "   Admin:    http://$VM_IP:8000/admin/"
echo ""
echo "🔐 Default credentials:"
echo "   Email:    admin@dani.local"
echo "   Password: ChangeMe123!"
echo ""
echo "⚠️  IMPORTANT: Change the default password immediately!"
echo ""
echo "🔧 Next steps:"
echo "   1. Visit the admin interface and change the password"
echo "   2. Configure email settings in .env if needed"
echo "   3. Set up Azure AD integration if required"
echo ""
echo "📊 Service status:"
docker-compose -f docker-compose.production.yml ps
echo ""
echo "📚 For troubleshooting, see: TROUBLESHOOTING.md"