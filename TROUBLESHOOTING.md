# D.A.N.I Troubleshooting Guide

This guide covers common issues encountered during D.A.N.I deployment and their solutions.

---

## 🔧 Common Deployment Issues

### 1. Docker Permission Denied

**Problem:**
```
permission denied while trying to connect to the Docker daemon socket
```

**Solution:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Apply group changes (choose one):
# Option A: Log out and back in
exit
# Then SSH back in

# Option B: Use newgrp for current session
newgrp docker

# Verify Docker access
docker ps
```

---

### 2. PostgreSQL Container Exits with Error

**Problem:**
```
dependency failed to start: container hris_postgres exited (1)
```

**Common Causes & Solutions:**

#### A. Port Conflict (Most Common)
```bash
# Check if port 5432 is in use
sudo netstat -tlnp | grep 5432

# Solution: Update docker-compose.yml
nano docker-compose.yml

# Change postgres port mapping to:
ports:
  - "5433:5432"  # Use 5433 to avoid conflicts
```

#### B. init-db.sql Directory Issue
```bash
# Check logs
docker-compose logs postgres

# If you see: "could not read from input file: Is a directory"
# Remove problematic init-db.sql mount from docker-compose.yml
sed -i '/init-db.sql/d' docker-compose.yml

# Clean restart
docker-compose down -v
make init
```

#### C. Volume Permission Issues
```bash
# Clean up volumes and restart
docker-compose down -v
docker volume prune -f
make init
```

---

### 3. Django Logging Permission Error

**Problem:**
```
PermissionError: [Errno 13] Permission denied: '/app/logs/django.log'
```

**Solution:**
```bash
# Method 1: Create logs directory with proper permissions
mkdir -p ./logs
chmod 755 ./logs

# Method 2: Fix via container (if web service is running)
docker-compose exec --user root web bash -c "
mkdir -p /app/logs
chmod 755 /app/logs
touch /app/logs/django.log
chmod 644 /app/logs/django.log
"

# Method 3: Disable file logging temporarily
echo "LOGGING_DISABLE_FILE=True" >> .env

# Restart services
docker-compose down
docker-compose up -d
```

---

### 4. Web Service Not Starting

**Problem:**
```
service "web" is not running
```

**Diagnosis:**
```bash
# Check web service logs
docker-compose logs web

# Check all service status
docker-compose ps

# Common fixes:
# 1. Logging permissions (see section 3)
# 2. Database connection issues
# 3. Missing environment variables
```

**Solutions:**
```bash
# Ensure logs directory exists
mkdir -p ./logs
chmod 755 ./logs

# Restart services in order
docker-compose up -d postgres redis
sleep 10
docker-compose up -d web
```

---

### 5. Missing .env.example File

**Problem:**
```
cp: cannot stat '.env.example': No such file or directory
```

**Solution:**
```bash
# Create .env.example file
cat > .env.example << 'EOF'
# Django Configuration
DEBUG=True
SECRET_KEY=your-secret-key-here-generate-with-python-secrets
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_NAME=hris_platform
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=postgres
DB_PORT=5432

# Redis Configuration
CELERY_BROKER_URL=redis://redis:6380/0
CELERY_RESULT_BACKEND=redis://redis:6380/0

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

# Azure AD Configuration (Optional)
AZURE_AD_ENABLED=false
AZURE_AD_TENANT_ID=
AZURE_AD_CLIENT_ID=
AZURE_AD_CLIENT_SECRET=
AZURE_AD_AUTHORITY=https://login.microsoftonline.com/
AZURE_AD_SCOPE=https://graph.microsoft.com/.default

# Security Settings
SECURE_SSL_REDIRECT=False
SECURE_HSTS_SECONDS=0
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Superuser Configuration
SUPERUSER_EMAIL=admin@dani.local
SUPERUSER_PASSWORD=admin123
EOF

# Now run make init
make init
```

---

### 6. Network/Firewall Issues

**Problem:**
```
Can't access application from browser
```

**Solutions:**
```bash
# Check if port 8000 is open
sudo ufw status
sudo ufw allow 8000

# For cloud VMs, also check:
# - Security group rules (AWS)
# - Firewall rules (GCP)
# - Network security groups (Azure)

# Test local access first
curl http://localhost:8000

# Get your VM's IP
curl -s ifconfig.me
```

---

### 7. Database Migration Errors

**Problem:**
```
django.db.utils.OperationalError: could not connect to server
```

**Solutions:**
```bash
# Wait for PostgreSQL to be ready
docker-compose exec postgres pg_isready -U postgres

# Check PostgreSQL status
docker-compose ps postgres

# Manual migration if needed
docker-compose exec web python manage.py migrate

# Reset database if corrupted
docker-compose down -v
make init
```

---

### 8. Redis Connection Issues

**Problem:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solutions:**
```bash
# Check Redis status
docker-compose ps redis
docker-compose exec redis redis-cli ping

# Check port conflicts
sudo netstat -tlnp | grep 6379

# Update .env if using different port
echo "CELERY_BROKER_URL=redis://redis:6380/0" >> .env
echo "CELERY_RESULT_BACKEND=redis://redis:6380/0" >> .env
```

---

## 🚀 Complete Reset Procedure

If you encounter multiple issues, try a complete reset:

```bash
cd ~/dani-platform

# Stop all services
docker-compose down -v

# Remove all containers and volumes
docker system prune -f
docker volume prune -f

# Ensure required directories exist
mkdir -p logs media staticfiles
chmod 755 logs media staticfiles

# Start fresh
make init

# If still having issues, check individual services:
docker-compose logs postgres
docker-compose logs redis
docker-compose logs web
```

---

## 🔍 Diagnostic Commands

### Check Service Health
```bash
# Overall status
docker-compose ps

# Individual service logs
docker-compose logs [service_name]

# Service health checks
make health

# Resource usage
docker stats
```

### Check Network Connectivity
```bash
# Test database connection
docker-compose exec web python manage.py dbshell

# Test Redis connection
docker-compose exec redis redis-cli ping

# Test web application
curl http://localhost:8000/admin/
```

### Check Permissions
```bash
# File permissions
ls -la logs/ media/ staticfiles/

# Container user
docker-compose exec web whoami
docker-compose exec web id
```

---

## 📋 VM-Specific Issues

### Getting VM IP Address
```bash
# Method 1: Public IP
curl -s ifconfig.me

# Method 2: Local network IP
hostname -I | awk '{print $1}'

# Method 3: All interfaces
ip addr show | grep "inet "
```

### Access URLs
Replace `YOUR_VM_IP` with actual IP:
- Main app: `http://YOUR_VM_IP:8000/`
- Admin: `http://YOUR_VM_IP:8000/admin/`

### Common VM Issues
1. **Firewall blocking ports** - Open 8000, 80, 443
2. **Cloud security groups** - Allow inbound traffic
3. **Insufficient resources** - Check RAM/CPU usage
4. **DNS resolution** - Use IP instead of hostname

---

## 🆘 Emergency Recovery

### If Nothing Works
```bash
# Complete cleanup and restart
cd ~/dani-platform
docker-compose down -v
docker system prune -af
docker volume prune -f

# Remove and re-clone project
cd ~
rm -rf dani-platform
git clone https://github.com/IAMCYBERRY/dani-platform.git
cd dani-platform

# Fresh setup
make init
```

### Backup Before Recovery
```bash
# Backup database (if accessible)
make backup-db

# Backup configuration
cp .env .env.backup

# Backup custom files
tar -czf backup.tar.gz media/ logs/ .env
```

---

## 📞 Getting Help

### Log Collection for Support
```bash
# Collect all logs
docker-compose logs > all-logs.txt

# System information
uname -a > system-info.txt
docker --version >> system-info.txt
docker-compose --version >> system-info.txt

# Service status
docker-compose ps > service-status.txt
```

### Common Log Locations
- Application logs: `./logs/django.log`
- Container logs: `docker-compose logs [service]`
- System logs: `/var/log/syslog` (Ubuntu)

---

**Remember**: Most issues are related to permissions, network configuration, or missing dependencies. Always check the logs first with `docker-compose logs [service_name]` to identify the root cause.

🎯 **Quick Fix Checklist:**
1. ✅ Docker permissions (`usermod -aG docker $USER`)
2. ✅ Logs directory exists (`mkdir -p logs && chmod 755 logs`)
3. ✅ Ports not conflicting (use 5433 for postgres, 6380 for redis)
4. ✅ .env.example exists
5. ✅ No init-db.sql volume mount in docker-compose.yml
6. ✅ Firewall allows port 8000