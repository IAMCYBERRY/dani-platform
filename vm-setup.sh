#!/bin/bash
# D.A.N.I VM Setup Script
# This script prepares a fresh Ubuntu VM for D.A.N.I deployment

set -e

echo "🚀 Setting up VM for D.A.N.I deployment..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Docker
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
else
    echo "✅ Docker already installed"
fi

# Install Docker Compose
echo "🔧 Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
else
    echo "✅ Docker Compose already installed"
fi

# Add user to docker group
echo "👤 Configuring Docker permissions..."
sudo usermod -aG docker $USER

# Install additional tools
echo "🛠️ Installing additional tools..."
sudo apt install -y curl wget git make ufw

# Configure firewall
echo "🔥 Configuring firewall..."
sudo ufw allow 22   # SSH
sudo ufw allow 80   # HTTP
sudo ufw allow 443  # HTTPS
sudo ufw allow 8000 # D.A.N.I
sudo ufw --force enable

# Clone D.A.N.I repository
echo "📥 Cloning D.A.N.I repository..."
if [ ! -d "dani-platform" ]; then
    git clone https://github.com/IAMCYBERRY/dani-platform.git
    cd dani-platform
else
    echo "✅ Repository already exists"
    cd dani-platform
    git pull origin main
fi

# Create required directories
echo "📁 Creating required directories..."
mkdir -p logs media staticfiles
chmod 755 logs media staticfiles

# Create environment template if missing
if [ ! -f .env.example ]; then
    echo "⚠️  .env.example missing, creating it..."
    cat > .env.example << 'EOF'
# Django Configuration
DEBUG=True
SECRET_KEY=your-secret-key-here-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database Configuration
DB_NAME=hris_platform
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=postgres
DB_PORT=5432

# Redis/Celery Configuration
CELERY_BROKER_URL=redis://redis:6380/0
CELERY_RESULT_BACKEND=redis://redis:6380/0

# Logging Configuration
USE_FILE_LOGGING=true
LOG_LEVEL=INFO

# Superuser Configuration (for Docker setup)
SUPERUSER_EMAIL=admin@dani.local
SUPERUSER_PASSWORD=admin123

# Application Configuration
LOAD_INITIAL_DATA=False
EOF
fi

# Copy environment template
if [ ! -f .env ]; then
    cp .env.example .env
    echo "📝 Environment file created"
else
    echo "✅ Environment file already exists"
fi

# Display next steps
echo ""
echo "🎉 VM setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Log out and back in (to apply Docker group membership)"
echo "2. Edit .env file with your configuration:"
echo "   nano .env"
echo "3. Deploy D.A.N.I:"
echo "   make init"
echo ""
echo "🌐 After deployment, access at:"
# Get IPv4 address preferentially
VM_IP=$(curl -s -4 ifconfig.me 2>/dev/null || ip route get 8.8.8.8 | awk '{print $7; exit}' 2>/dev/null || hostname -I | grep -oE '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b' | head -1 || echo "YOUR_VM_IP")
echo "   http://$VM_IP:8000/admin/"
echo ""
echo "🔐 Default credentials:"
echo "   Email: admin@dani.local"
echo "   Password: admin123"
echo ""
echo "⚠️  IMPORTANT: Change the default password after first login!"
echo ""
echo "📚 For troubleshooting, see: TROUBLESHOOTING.md"