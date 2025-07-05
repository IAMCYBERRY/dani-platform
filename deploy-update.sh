#!/bin/bash

# DANI Platform - Update Deployment Script
# This script updates an existing DANI HRIS platform deployment while preserving data
# Usage: curl -sSL https://raw.githubusercontent.com/IAMCYBERRY/dani-platform/main/deploy-update.sh | bash

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

# Configuration
DEPLOY_PATH="/opt/dani"
SERVICE_NAME="dani-platform"
BACKUP_DIR="/backups/update-$(date +%Y-%m-%d_%H-%M-%S)"

log "Starting DANI Platform update process..."

# Verify existing installation
if [ ! -d "$DEPLOY_PATH" ]; then
    error "DANI Platform not found at $DEPLOY_PATH. Use deploy-fresh.sh for new installations."
fi

if [ ! -f "$DEPLOY_PATH/manage.py" ]; then
    error "Invalid DANI Platform installation detected."
fi

# Check if service exists
if ! systemctl list-unit-files | grep -q "$SERVICE_NAME.service"; then
    error "DANI Platform service not found. Use deploy-fresh.sh for new installations."
fi

log "Creating backup before update..."
sudo mkdir -p "$BACKUP_DIR"

# Backup database
log "Backing up database..."
sudo -u postgres pg_dump dani_platform > "$BACKUP_DIR/database_backup.sql"

# Backup media files
log "Backing up media files..."
sudo cp -r "$DEPLOY_PATH/media" "$BACKUP_DIR/"

# Backup environment file
log "Backing up configuration..."
sudo cp "$DEPLOY_PATH/.env" "$BACKUP_DIR/"

# Backup current application
log "Backing up current application..."
sudo tar -czf "$BACKUP_DIR/application_backup.tar.gz" -C "$DEPLOY_PATH" --exclude='.git' --exclude='venv' --exclude='__pycache__' .

log "Stopping services..."
sudo systemctl stop "$SERVICE_NAME"

# Get current git status
cd "$DEPLOY_PATH"
CURRENT_COMMIT=$(git rev-parse HEAD)
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

log "Current version: $CURRENT_COMMIT on branch $CURRENT_BRANCH"

log "Fetching latest updates from GitHub..."
sudo git fetch origin

# Stash any local changes
if ! git diff-index --quiet HEAD --; then
    warn "Local changes detected, stashing them..."
    sudo git stash
fi

log "Updating to latest version..."
sudo git checkout main
sudo git pull origin main

NEW_COMMIT=$(git rev-parse HEAD)
log "Updated to version: $NEW_COMMIT"

# Show what changed
if [ "$CURRENT_COMMIT" != "$NEW_COMMIT" ]; then
    log "Changes in this update:"
    git log --oneline "$CURRENT_COMMIT".."$NEW_COMMIT" || true
fi

log "Updating Python dependencies..."
sudo -u www-data "$DEPLOY_PATH/venv/bin/pip" install --upgrade pip
sudo -u www-data "$DEPLOY_PATH/venv/bin/pip" install -r requirements.txt

log "Running database migrations..."
sudo -u www-data "$DEPLOY_PATH/venv/bin/python" manage.py makemigrations
sudo -u www-data "$DEPLOY_PATH/venv/bin/python" manage.py migrate

log "Collecting static files..."
sudo -u www-data "$DEPLOY_PATH/venv/bin/python" manage.py collectstatic --noinput

log "Checking for new media directories..."
sudo mkdir -p "$DEPLOY_PATH/media/profile_pictures"
sudo chown -R www-data:www-data "$DEPLOY_PATH/media"

log "Updating file permissions..."
sudo chown -R www-data:www-data "$DEPLOY_PATH"
sudo chmod -R 755 "$DEPLOY_PATH"
sudo chmod 600 "$DEPLOY_PATH/.env"

log "Testing configuration..."
sudo -u www-data "$DEPLOY_PATH/venv/bin/python" manage.py check

log "Starting services..."
sudo systemctl start "$SERVICE_NAME"

# Wait for service to start
sleep 5

log "Verifying deployment..."
if ! sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    error "Service failed to start after update. Check logs: sudo journalctl -u $SERVICE_NAME"
fi

# Test application response
if curl -f -s http://localhost/ > /dev/null; then
    log "✓ Application is responding correctly"
else
    warn "Application may not be responding. Check service status."
fi

# Test database connectivity
log "Testing database connectivity..."
sudo -u www-data "$DEPLOY_PATH/venv/bin/python" manage.py shell -c "
from accounts.models import User
from employees.models import Department
print(f'✓ Database connection successful')
print(f'✓ Users: {User.objects.count()}')
print(f'✓ Departments: {Department.objects.count()}')

# Test new fields
user = User.objects.first()
if user:
    new_fields = ['company_name', 'employee_id', 'employee_type', 'manager', 'office_location', 'hire_date', 'start_date', 'end_date']
    for field in new_fields:
        if hasattr(user, field):
            print(f'✓ New field available: {field}')
        else:
            print(f'⚠ Field missing: {field}')
"

log "Creating rollback script..."
sudo tee "$BACKUP_DIR/rollback.sh" << EOF
#!/bin/bash
echo "Rolling back DANI Platform to previous version..."

# Stop service
sudo systemctl stop $SERVICE_NAME

# Restore application
cd $DEPLOY_PATH
sudo git checkout $CURRENT_COMMIT

# Restore database
sudo -u postgres dropdb dani_platform
sudo -u postgres createdb dani_platform
sudo -u postgres psql dani_platform < $BACKUP_DIR/database_backup.sql

# Restore media files
sudo rm -rf $DEPLOY_PATH/media
sudo cp -r $BACKUP_DIR/media $DEPLOY_PATH/

# Restore environment
sudo cp $BACKUP_DIR/.env $DEPLOY_PATH/

# Set permissions
sudo chown -R www-data:www-data $DEPLOY_PATH

# Restart service
sudo systemctl start $SERVICE_NAME

echo "Rollback completed"
EOF

sudo chmod +x "$BACKUP_DIR/rollback.sh"

log "Cleaning up old backups (keeping last 5)..."
sudo find /backups -name "update-*" -type d | sort | head -n -5 | xargs -r sudo rm -rf

log "=== UPDATE COMPLETED SUCCESSFULLY ==="
echo ""
log "🎉 DANI Platform has been updated successfully!"
echo ""
log "📊 Version Information:"
log "   Previous: $CURRENT_COMMIT"
log "   Current:  $NEW_COMMIT"
echo ""
log "💾 Backup Location: $BACKUP_DIR"
log "🔄 Rollback Script: $BACKUP_DIR/rollback.sh"
echo ""
log "🔧 Service Status:"
sudo systemctl status "$SERVICE_NAME" --no-pager -l | head -10
echo ""
log "📈 Post-Update Checklist:"
log "   □ Test user creation with new fields"
log "   □ Verify department dropdown functionality"
log "   □ Test Azure AD sync if configured"
log "   □ Check admin panel functionality"
log "   □ Verify file uploads work"
echo ""
log "🚨 If issues occur:"
log "   - View logs: sudo journalctl -u $SERVICE_NAME -f"
log "   - Rollback: sudo $BACKUP_DIR/rollback.sh"
log "   - Check service: sudo systemctl status $SERVICE_NAME"