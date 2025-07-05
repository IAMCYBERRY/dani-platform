#!/bin/bash

# DANI Platform - Fresh Deployment Script
# This script sets up a complete DANI HRIS platform on a fresh Ubuntu VM
#
# Usage Options:
# 1. With environment variables (recommended for automation):
#    ADMIN_EMAIL="you@domain.com" DOMAIN_NAME="your-domain.com" \
#    curl -sSL https://raw.githubusercontent.com/IAMCYBERRY/dani-platform/main/deploy-fresh.sh | bash
#
# 2. Download and run interactively:
#    wget https://raw.githubusercontent.com/IAMCYBERRY/dani-platform/main/deploy-fresh.sh
#    chmod +x deploy-fresh.sh
#    ./deploy-fresh.sh
#    # Will prompt for email and domain
#
# 3. Minimal automation (without SSL):
#    ADMIN_EMAIL="you@domain.com" \
#    curl -sSL https://raw.githubusercontent.com/IAMCYBERRY/dani-platform/main/deploy-fresh.sh | bash

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root. Please run as a regular user with sudo privileges."
fi

# Configuration variables - can be set via environment variables or modified here
DOMAIN_NAME="${DOMAIN_NAME:-}"  # Set your domain name (optional)
DB_PASSWORD="${DB_PASSWORD:-}"  # Will be generated if empty
SECRET_KEY="${SECRET_KEY:-}"   # Will be generated if empty
ADMIN_EMAIL="${ADMIN_EMAIL:-}"  # Required for SSL certificate
DEPLOY_PATH="${DEPLOY_PATH:-/opt/dani}"
SERVICE_NAME="${SERVICE_NAME:-dani-platform}"

log "Starting DANI Platform fresh deployment..."

# Check Ubuntu version
if ! grep -q "Ubuntu" /etc/os-release; then
    error "This script is designed for Ubuntu. Please use Ubuntu 20.04 or later."
fi

# Check for required configuration
if [ -z "$ADMIN_EMAIL" ]; then
    # Try to read from terminal if available
    if [ -t 0 ]; then
        read -p "Enter admin email address: " ADMIN_EMAIL
        if [ -z "$ADMIN_EMAIL" ]; then
            error "Admin email is required for SSL certificate setup"
        fi
    else
        error "Admin email is required. Set it as: ADMIN_EMAIL='you@domain.com' curl ... | bash"
    fi
fi

if [ -z "$DOMAIN_NAME" ]; then
    if [ -t 0 ]; then
        read -p "Enter domain name (optional, press enter to skip): " DOMAIN_NAME
    else
        log "No domain name provided - SSL will not be configured automatically"
    fi
fi

# Generate secure passwords and keys
if [ -z "$DB_PASSWORD" ]; then
    DB_PASSWORD=$(openssl rand -base64 32)
fi

if [ -z "$SECRET_KEY" ]; then
    SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
fi

log "Updating system packages..."
sudo apt update && sudo apt upgrade -y

log "Installing system dependencies..."
sudo apt install -y \
    git \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    postgresql \
    postgresql-contrib \
    nginx \
    certbot \
    python3-certbot-nginx \
    redis-server \
    supervisor \
    htop \
    curl \
    wget \
    unzip \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    pkg-config

log "Configuring PostgreSQL..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE dani_platform;"
sudo -u postgres psql -c "CREATE USER dani_user WITH PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE dani_platform TO dani_user;"
sudo -u postgres psql -c "ALTER USER dani_user CREATEDB;"

log "Creating application directory..."
sudo mkdir -p $DEPLOY_PATH
cd $DEPLOY_PATH

log "Cloning DANI platform from GitHub..."
sudo git clone https://github.com/IAMCYBERRY/dani-platform.git .

# Verify repository contents
if [ ! -f "manage.py" ]; then
    error "Repository does not contain manage.py. Please check the repository structure."
fi

if [ ! -f "requirements.txt" ]; then
    error "Repository does not contain requirements.txt. Please check the repository structure."
fi

log "Setting up Python virtual environment..."
sudo python3 -m venv venv
sudo chown -R www-data:www-data $DEPLOY_PATH

log "Installing Python dependencies..."
sudo -u www-data $DEPLOY_PATH/venv/bin/pip install --upgrade pip
sudo -u www-data $DEPLOY_PATH/venv/bin/pip install -r requirements.txt

log "Creating environment configuration..."
sudo -u www-data tee $DEPLOY_PATH/.env << EOF
# Django Settings
DEBUG=False
SECRET_KEY=$SECRET_KEY
ALLOWED_HOSTS=localhost,127.0.0.1$([ ! -z "$DOMAIN_NAME" ] && echo ",$DOMAIN_NAME")

# Database Configuration
DATABASE_URL=postgresql://dani_user:$DB_PASSWORD@localhost:5432/dani_platform

# Azure AD Configuration
AZURE_AD_ENABLED=True
AZURE_AD_SYNC_ENABLED=True
GRAPH_API_BASE_URL=https://graph.microsoft.com/v1.0
AZURE_AD_DEFAULT_PASSWORD_LENGTH=12

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Email Configuration (SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

# Security Settings
SECURE_BROWSER_XSS_FILTER=True
SECURE_CONTENT_TYPE_NOSNIFF=True
X_FRAME_OPTIONS=DENY
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Platform Configuration
PLATFORM_NAME=D.A.N.I HRIS Platform
COMPANY_NAME=Your Organization
ADMIN_EMAIL=$ADMIN_EMAIL

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE=10485760
DATA_UPLOAD_MAX_MEMORY_SIZE=10485760
EOF

log "Running database migrations..."
sudo -u www-data $DEPLOY_PATH/venv/bin/python manage.py makemigrations
sudo -u www-data $DEPLOY_PATH/venv/bin/python manage.py migrate

log "Collecting static files..."
sudo -u www-data $DEPLOY_PATH/venv/bin/python manage.py collectstatic --noinput

log "Creating media directories..."
sudo mkdir -p $DEPLOY_PATH/media/profile_pictures
sudo chown -R www-data:www-data $DEPLOY_PATH/media

log "Creating systemd service..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=D.A.N.I HRIS Platform
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=$DEPLOY_PATH
Environment=PATH=$DEPLOY_PATH/venv/bin
ExecStart=$DEPLOY_PATH/venv/bin/gunicorn --workers 3 --max-requests 1000 --max-requests-jitter 100 --bind unix:$DEPLOY_PATH/dani.sock hris_platform.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

log "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/$SERVICE_NAME << EOF
server {
    listen 80;
    server_name $([ ! -z "$DOMAIN_NAME" ] && echo "$DOMAIN_NAME" || echo "_");

    client_max_body_size 100M;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    location = /favicon.ico { 
        access_log off; 
        log_not_found off; 
    }
    
    location /static/ {
        alias $DEPLOY_PATH/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias $DEPLOY_PATH/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:$DEPLOY_PATH/dani.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

# Enable nginx site
sudo ln -sf /etc/nginx/sites-available/$SERVICE_NAME /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t || error "Nginx configuration test failed"

log "Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME
sudo systemctl enable nginx
sudo systemctl restart nginx
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Wait for service to start
sleep 5

log "Checking service status..."
if ! sudo systemctl is-active --quiet $SERVICE_NAME; then
    error "DANI platform service failed to start. Check logs with: sudo journalctl -u $SERVICE_NAME"
fi

if ! sudo systemctl is-active --quiet nginx; then
    error "Nginx failed to start. Check logs with: sudo journalctl -u nginx"
fi

# Configure SSL if domain is provided
if [ ! -z "$DOMAIN_NAME" ]; then
    log "Configuring SSL certificate for $DOMAIN_NAME..."
    sudo certbot --nginx -d $DOMAIN_NAME --non-interactive --agree-tos --email $ADMIN_EMAIL --redirect
fi

log "Creating superuser account..."
echo "You will now create an admin account for the DANI platform:"
sudo -u www-data $DEPLOY_PATH/venv/bin/python manage.py createsuperuser

log "Setting up log rotation..."
sudo tee /etc/logrotate.d/dani-platform << EOF
$DEPLOY_PATH/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload $SERVICE_NAME
    endscript
}
EOF

# Create logs directory
sudo mkdir -p $DEPLOY_PATH/logs
sudo chown www-data:www-data $DEPLOY_PATH/logs

log "Creating backup script..."
sudo tee /usr/local/bin/backup-dani.sh << EOF
#!/bin/bash
BACKUP_DIR="/backups/dani-\$(date +%Y-%m-%d_%H-%M-%S)"
mkdir -p \$BACKUP_DIR

# Backup database
sudo -u postgres pg_dump dani_platform > \$BACKUP_DIR/database.sql

# Backup media files
cp -r $DEPLOY_PATH/media \$BACKUP_DIR/

# Backup environment
cp $DEPLOY_PATH/.env \$BACKUP_DIR/

echo "Backup completed: \$BACKUP_DIR"
EOF

sudo chmod +x /usr/local/bin/backup-dani.sh

log "Setting up automatic backup cron job..."
echo "0 2 * * * root /usr/local/bin/backup-dani.sh" | sudo tee -a /etc/crontab

log "Creating firewall rules..."
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

log "Final system verification..."

# Test database connection
sudo -u www-data $DEPLOY_PATH/venv/bin/python manage.py check --database default

# Test application
if curl -f -s http://localhost/ > /dev/null; then
    log "✓ Application is responding"
else
    warn "Application may not be responding correctly"
fi

# Show service status
echo ""
log "Service Status:"
sudo systemctl status $SERVICE_NAME --no-pager -l
sudo systemctl status nginx --no-pager -l

echo ""
log "=== DEPLOYMENT COMPLETED SUCCESSFULLY ==="
echo ""
log "🎉 DANI Platform has been deployed successfully!"
echo ""
log "📊 Access your platform:"
if [ ! -z "$DOMAIN_NAME" ]; then
    log "   Web Interface: https://$DOMAIN_NAME"
    log "   Admin Panel:   https://$DOMAIN_NAME/admin/"
else
    log "   Web Interface: http://$(curl -s ifconfig.me || hostname -I | awk '{print $1}')"
    log "   Admin Panel:   http://$(curl -s ifconfig.me || hostname -I | awk '{print $1}')/admin/"
fi

echo ""
log "🔧 Management Commands:"
log "   Check status:  sudo systemctl status $SERVICE_NAME"
log "   View logs:     sudo journalctl -u $SERVICE_NAME -f"
log "   Backup data:   sudo /usr/local/bin/backup-dani.sh"
log "   Django shell:  sudo -u www-data $DEPLOY_PATH/venv/bin/python manage.py shell"

echo ""
log "🔐 Security Notes:"
log "   - Database password: $DB_PASSWORD"
log "   - Change default admin password after first login"
log "   - Configure Azure AD settings in admin panel"
log "   - Update ALLOWED_HOSTS in .env if needed"

echo ""
log "📁 Important Paths:"
log "   - Application:   $DEPLOY_PATH"
log "   - Environment:   $DEPLOY_PATH/.env"
log "   - Media files:   $DEPLOY_PATH/media"
log "   - Logs:          $DEPLOY_PATH/logs"
log "   - Backups:       /backups/"

echo ""
warn "Remember to:"
warn "1. Configure your Azure AD application settings"
warn "2. Set up email configuration in .env file"
warn "3. Add your domain to ALLOWED_HOSTS if using a custom domain"
warn "4. Test all functionality before going live"