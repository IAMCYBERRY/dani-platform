# DANI Platform - Quick Admin Guide

This guide provides step-by-step instructions for deploying and maintaining the DANI HRIS platform.

## Table of Contents
- [Local Machine Deployment](#local-machine-deployment)
- [Local Machine Upgrade](#local-machine-upgrade)
- [Ubuntu VM Deployment](#ubuntu-vm-deployment)
- [Ubuntu VM Upgrade](#ubuntu-vm-upgrade)
- [Common Commands](#common-commands)
- [Troubleshooting](#troubleshooting)

---

## Local Machine Deployment

### Prerequisites
- Docker Desktop installed and running
- Git installed
- 8GB+ RAM recommended
- 10GB+ free disk space

### Step 1: Clone the Repository
```bash
git clone https://github.com/IAMCYBERRY/dani-platform.git
cd dani-platform
```

### Step 2: Configure Environment
```bash
# Copy the example environment file
cp .env.example .env

# Edit the environment file with your settings
nano .env
```

**Required Settings:**
- `POSTGRES_PASSWORD`: Set a secure database password
- `DJANGO_SECRET_KEY`: Generate a secure key (or use the provided one for testing)
- `ADMIN_EMAIL`: Set to `admin@hris.local`
- `ADMIN_PASSWORD`: Set a secure admin password

### Step 3: Deploy the Application
```bash
# Build and start all services
docker-compose up -d --build

# Wait for services to start (check logs)
docker-compose logs -f

# Create superuser (if needed)
docker-compose exec web python manage.py createsuperuser
```

### Step 4: Access the Application
- **Web Interface**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **Default Credentials**: admin@hris.local / [your_admin_password]

### Step 5: Initial Configuration
1. Access admin panel at http://localhost:8000/admin
2. Navigate to **Azure AD Settings** (if using Azure AD)
3. Configure tenant ID, client ID, and client secret
4. Test connection using admin actions

---

## Local Machine Upgrade

### Step 1: Stop the Application
```bash
cd dani-platform
docker-compose down
```

### Step 2: Backup Data (Recommended)
```bash
# Create backup directory
mkdir -p backups/$(date +%Y%m%d_%H%M%S)

# Backup database
docker-compose up -d db
docker-compose exec db pg_dump -U postgres dani_db > backups/$(date +%Y%m%d_%H%M%S)/database.sql
docker-compose down
```

### Step 3: Update Code
```bash
# Pull latest changes
git pull origin main

# If you have local changes, stash them first
git stash
git pull origin main
git stash pop
```

### Step 4: Deploy Updated Version
```bash
# Rebuild and restart with new code
docker-compose up -d --build

# Apply any new database migrations
docker-compose exec web python manage.py migrate

# Collect static files (if needed)
docker-compose exec web python manage.py collectstatic --noinput
```

### Step 5: Verify Upgrade
```bash
# Check all services are running
docker-compose ps

# Check application logs
docker-compose logs web

# Access the application
curl -I http://localhost:8000
```

---

## Ubuntu VM Deployment

### Prerequisites
- Ubuntu 20.04+ server
- 4GB+ RAM, 20GB+ disk space
- SSH access with sudo privileges
- Domain name (optional but recommended)

### Step 1: Prepare the Server
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y git curl wget ufw

# Configure firewall
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable
```

### Step 2: Install Docker
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker-compose --version
```

### Step 3: Clone and Configure
```bash
# Clone repository
git clone https://github.com/IAMCYBERRY/dani-platform.git
cd dani-platform

# Create production environment file
cp .env.example .env
nano .env
```

**Production Settings:**
```env
# Database
POSTGRES_PASSWORD=your_secure_db_password

# Django
DEBUG=False
DJANGO_SECRET_KEY=your_production_secret_key
ALLOWED_HOSTS=your-domain.com,your-server-ip

# Admin
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=your_secure_admin_password

# Optional: Azure AD
AZURE_AD_TENANT_ID=your_tenant_id
AZURE_AD_CLIENT_ID=your_client_id
AZURE_AD_CLIENT_SECRET=your_client_secret
```

### Step 4: Deploy Production
```bash
# Start services
docker-compose -f docker-compose.yml up -d --build

# Wait for startup
sleep 30

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

### Step 5: Configure Reverse Proxy (Optional)
```bash
# Install Nginx
sudo apt install -y nginx

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/dani-platform
```

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/ubuntu/dani-platform/static/;
    }

    location /media/ {
        alias /home/ubuntu/dani-platform/media/;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/dani-platform /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 6: SSL Certificate (Optional)
```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Verify auto-renewal
sudo certbot renew --dry-run
```

---

## Ubuntu VM Upgrade

### Step 1: Backup Data
```bash
cd dani-platform

# Create backup directory
mkdir -p backups/$(date +%Y%m%d_%H%M%S)

# Backup database
docker-compose exec db pg_dump -U postgres dani_db > backups/$(date +%Y%m%d_%H%M%S)/database.sql

# Backup media files
cp -r media/ backups/$(date +%Y%m%d_%H%M%S)/
```

### Step 2: Stop Application
```bash
# Stop services gracefully
docker-compose down

# Optional: Stop Nginx if using reverse proxy
sudo systemctl stop nginx
```

### Step 3: Update Code
```bash
# Backup current environment
cp .env .env.backup

# Pull latest changes
git pull origin main

# Restore environment (if needed)
cp .env.backup .env
```

### Step 4: Deploy Update
```bash
# Rebuild with latest code
docker-compose up -d --build

# Apply migrations
docker-compose exec web python manage.py migrate

# Update static files
docker-compose exec web python manage.py collectstatic --noinput

# Restart Nginx (if used)
sudo systemctl start nginx
```

### Step 5: Verify Production Upgrade
```bash
# Check service status
docker-compose ps
systemctl status nginx

# Check application health
curl -I http://your-domain.com
curl -I https://your-domain.com

# Monitor logs
docker-compose logs -f --tail=50
```

---

## Common Commands

### Application Management
```bash
# View service status
docker-compose ps

# View logs
docker-compose logs -f [service_name]

# Restart specific service
docker-compose restart [service_name]

# Access container shell
docker-compose exec web bash
docker-compose exec db psql -U postgres dani_db

# Run Django commands
docker-compose exec web python manage.py [command]
```

### Database Operations
```bash
# Create backup
docker-compose exec db pg_dump -U postgres dani_db > backup.sql

# Restore backup
docker-compose exec -T db psql -U postgres dani_db < backup.sql

# Access database
docker-compose exec db psql -U postgres dani_db
```

### Maintenance
```bash
# Update containers
docker-compose pull
docker-compose up -d

# Clean up unused images
docker system prune -f

# View disk usage
docker system df
```

---

## Troubleshooting

### Common Issues

#### 1. Service Won't Start
```bash
# Check logs
docker-compose logs [service_name]

# Restart service
docker-compose restart [service_name]

# Rebuild if needed
docker-compose up -d --build [service_name]
```

#### 2. Database Connection Issues
```bash
# Check database status
docker-compose exec db pg_isready -U postgres

# Reset database (⚠️ DATA LOSS)
docker-compose down
docker volume rm dani-platform_postgres_data
docker-compose up -d
```

#### 3. Permission Issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Fix Docker socket permissions
sudo chmod 666 /var/run/docker.sock
```

#### 4. Port Conflicts
```bash
# Check what's using port 8000
sudo netstat -tlnp | grep :8000

# Kill process using port
sudo kill -9 [PID]
```

#### 5. Azure AD Sync Issues
```bash
# Check Azure AD settings in admin panel
# Test connection using admin actions
# Review sync logs:
docker-compose logs celery
```

### Health Checks
```bash
# Application health
curl http://localhost:8000/health/

# Database health
docker-compose exec db pg_isready -U postgres

# Redis health
docker-compose exec redis redis-cli ping

# Celery health
docker-compose exec celery celery -A hris_platform status
```

### Performance Monitoring
```bash
# Resource usage
docker stats

# Disk usage
df -h
docker system df

# Service logs
docker-compose logs --tail=100 -f
```

---

## Support

For issues not covered in this guide:

1. Check application logs: `docker-compose logs -f`
2. Review GitHub issues: https://github.com/IAMCYBERRY/dani-platform/issues
3. Check database connectivity and migrations
4. Verify environment variables are correctly set
5. Ensure all required ports are open and not conflicting

---

**Last Updated:** July 2025  
**Version:** 1.0