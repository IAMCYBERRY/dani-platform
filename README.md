# D.A.N.I - Domain Access & Navigation Interface

A comprehensive self-hosted Human Resources Information System (HRIS) and Applicant Tracking System (ATS) built with Django and designed for deployment via Docker. D.A.N.I features Azure AD/Microsoft Entra integration for seamless user management and domain access control.

## Features

### HRIS (Human Resources Information System)
- **User Management**: Role-based access control (Admin, HR Manager, Hiring Manager, Employee, Candidate)
- **Employee Profiles**: Comprehensive employee data management
- **Department Management**: Organizational structure and hierarchy
- **Job Titles Management**: Standardized job title system with salary ranges and skill requirements
- **Performance Reviews**: Employee evaluation and feedback system
- **Time-off Management**: Leave request and approval workflow
- **Azure AD Integration**: Seamless sync with Microsoft Entra/Azure AD
- **Microsoft Sentinel**: Security monitoring and threat detection
- **Reporting & Analytics**: HR metrics and insights

### ATS (Applicant Tracking System)
- **Job Posting Management**: Create and manage job openings
- **Application Tracking**: Full candidate pipeline management
- **Interview Scheduling**: Coordinate and track interviews
- **Offer Management**: Generate and track job offers
- **Recruitment Analytics**: Hiring metrics and pipeline insights
- **Multi-source Applications**: Support for various application sources

## Technology Stack

- **Backend**: Django 4.2 + Django REST Framework
- **Database**: PostgreSQL 15
- **Cache/Queue**: Redis + Celery
- **Authentication**: JWT with role-based permissions
- **Azure Integration**: Microsoft Graph API + Sentinel
- **API Documentation**: Django REST Framework browsable API
- **Deployment**: Docker + Docker Compose
- **Web Server**: Gunicorn + Nginx (production)

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- At least 4GB RAM available
- Port 8000 available (or modify docker-compose.yml)

### 30-Second Setup

1. **Clone and navigate to directory**
   ```bash
   git clone https://github.com/IAMCYBERRY/dani-platform.git
   cd dani-platform
   ```

2. **One-command setup** (recommended)
   ```bash
   make init
   ```
   
   **OR manually run:**
   ```bash
   # Create required directories
   mkdir -p logs media staticfiles
   
   # Copy environment file
   cp .env.example .env
   
   # Build and start all services
   docker-compose up -d --build
   ```

3. **Access your D.A.N.I platform**
   The setup will display your access URLs automatically. You can also access:
   
   **For Local Development:**
   - **Main Application**: http://localhost:8000/
   - **Admin Panel**: http://localhost:8000/admin/
   - **API Docs**: http://localhost:8000/api/
   
   **For Server Deployment:**
   - **Main Application**: http://YOUR_SERVER_IP:8000/
   - **Admin Panel**: http://YOUR_SERVER_IP:8000/admin/
   - **API Docs**: http://YOUR_SERVER_IP:8000/api/
   
   💡 **Tip**: The `make init` command will automatically detect and display your server's IP address

4. **Login with default admin account**
   - **Email**: `admin@hris.local`
   - **Password**: `admin123`
   - ⚠️ **Change this password immediately after first login!**

### What You Get
✅ Complete D.A.N.I platform (HRIS + ATS)  
✅ Role-based user management  
✅ Employee profiles and departments  
✅ Standardized job titles with salary ranges  
✅ Job postings and applicant tracking  
✅ Interview scheduling  
✅ Performance reviews  
✅ Time-off management  
✅ Azure AD integration ready  
✅ Microsoft Sentinel integration
✅ REST API with documentation

### 🔧 Deployment Scenarios

| Scenario | Command | Best For |
|----------|---------|----------|
| **Local Development** | `make init` | Testing, development, learning |
| **Quick Server Deploy** | `make init` | Quick production setup |
| **Production with Nginx** | `make up-prod` | High-traffic production |
| **Development with Tools** | `make up-tools` | Development with pgAdmin/Redis tools |
| **HTTPS/SSL Production** | `make up-https` | Production with domain & SSL |

💡 **Most users should start with `make init` - it works for both local and server deployment!**  

### Troubleshooting Quick Start
If you encounter issues:
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs web

# Restart services
docker-compose restart

# Clean restart
docker-compose down -v && docker-compose up -d --build
```

**📚 For comprehensive troubleshooting guide, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)**

**Common fixes:**
- Docker permissions: `sudo usermod -aG docker $USER && newgrp docker`
- Missing directories: `mkdir -p logs media staticfiles && chmod 755 logs media staticfiles`
- Port conflicts: External ports used are 8000 (web), 5433 (postgres), and 6380 (redis)
- Network issues: Check that your firewall allows access to port 8000
- **Container name conflicts**: Run `make clean` then `make init` to restart fresh
- **Stuck containers**: If containers won't remove, run `docker rm -f $(docker ps -aq --filter "name=hris_")` then `make init`
- **IP detection issues**: If setup shows `http://:8000/`, use `http://localhost:8000/` instead

---

## 🖥️ Ubuntu Server Deployment

### Prerequisites for Ubuntu Server
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install make
sudo apt install make -y
```

### Deployment Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/IAMCYBERRY/dani-platform.git
   cd dani-platform
   ```

2. **Configure environment settings**
   ```bash
   # Copy the environment template
   cp .env.example .env
   
   # Edit the environment file
   nano .env
   ```
   
   **Essential production settings to update:**
   ```bash
   # Security Settings (REQUIRED for production)
   DEBUG=False
   SECRET_KEY=your-super-secure-secret-key-here
   ALLOWED_HOSTS=your-domain.com,www.your-domain.com,your-server-ip
   
   # Database Security (RECOMMENDED)
   DB_PASSWORD=your-secure-database-password
   
   # Admin Credentials (Change after first login)
   SUPERUSER_EMAIL=admin@hris.local
   SUPERUSER_PASSWORD=admin123
   
   # Email Configuration (OPTIONAL - for notifications)
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-email@company.com
   EMAIL_HOST_PASSWORD=your-app-password
   
   # SSL/HTTPS Settings (For production with domain)
   SECURE_SSL_REDIRECT=True
   SECURE_HSTS_SECONDS=31536000
   ```
   
   💡 **Quick Setup**: For testing, you can use the default `.env.example` settings

3. **Deploy the platform**
   ```bash
   # Option 1: Quick deployment (recommended)
   make init
   
   # Option 2: Manual production deployment
   make clean
   make up-prod
   
   # Wait for services to start
   sleep 45
   
   # Run migrations
   make migrate
   
   # Create admin user (if not using make init)
   make createsuperuser
   ```

4. **Configure firewall**
   ```bash
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw allow 8000  # If not using nginx
   sudo ufw enable
   ```

5. **Set up SSL (optional but recommended)**
   ```bash
   # Install certbot
   sudo apt install certbot python3-certbot-nginx -y
   
   # Get SSL certificate
   sudo certbot --nginx -d your-domain.com
   ```

### Access Your Deployed Platform
- **Web Interface**: http://your-server-ip:8000/ or https://your-domain.com
- **Admin Panel**: http://your-server-ip:8000/admin/

## 🔒 HTTPS/SSL Setup (Recommended for Production)

For production deployments, enable HTTPS with automatic SSL certificates:

### Option 1: Automated HTTPS Setup
```bash
# Set up HTTPS with Let's Encrypt (requires domain pointing to your server)
make setup-https DOMAIN=dani.yourdomain.com EMAIL=admin@yourdomain.com

# Or run the script directly
chmod +x setup-https.sh
./setup-https.sh dani.yourdomain.com admin@yourdomain.com
```

### Option 2: Manual HTTPS Setup
```bash
# 1. Point your domain's A record to your server's IP
# 2. Update your .env file with your domain
echo "DOMAIN=dani.yourdomain.com" >> .env

# 3. Start with HTTPS
make up-https

# 4. Generate SSL certificate
docker-compose -f docker-compose.yml -f docker-compose.https.yml run --rm certbot \
    certbot certonly --webroot --webroot-path=/var/www/certbot \
    --email admin@yourdomain.com --agree-tos --no-eff-email \
    -d dani.yourdomain.com
```

### HTTPS Requirements
- **Domain**: You need a domain name pointing to your server
- **Port 80/443**: Must be accessible from the internet
- **DNS**: A record must point to your server's public IP

### After HTTPS Setup
- Access via: `https://your-domain.com`
- Certificates auto-renew every 12 hours
- HTTP traffic automatically redirects to HTTPS
- Security headers are automatically added

---

## 🔐 Azure AD / Microsoft Entra Integration

### Step 1: Azure AD App Registration

1. **Go to [Azure Portal](https://portal.azure.com)**
2. **Navigate to**: Azure Active Directory → App registrations → New registration
3. **Create app registration**:
   - **Name**: `HRIS Platform Integration`
   - **Account types**: "Accounts in this organizational directory only"
   - **Redirect URI**: Leave blank
   - Click **Register**

4. **Configure API permissions**:
   - Go to **API permissions** → **Add permission** → **Microsoft Graph** → **Application permissions**
   - **Add these permissions**:
     ```
     User.ReadWrite.All          # Create, read, update users
     User.ManageIdentities.All   # Manage user identities  
     Directory.ReadWrite.All     # Read/write directory data
     Group.ReadWrite.All         # Manage group memberships (optional)
     ```
   - **Important**: Click **"Grant admin consent for [Your Organization]"**

5. **Create client secret**:
   - Go to **Certificates & secrets** → **New client secret**
   - **Description**: `HRIS Platform Secret`
   - **Expires**: 12-24 months (recommended)
   - **Copy the secret value immediately** - you won't see it again!

6. **Copy required information**:
   - **Tenant ID** (Directory ID): From **Overview** tab
   - **Client ID** (Application ID): From **Overview** tab
   - **Client Secret**: The value you just created

### Step 2: Configure Azure AD in HRIS Platform

1. **Access admin panel**:
   - Go to http://your-server:8000/admin/
   - Login with admin credentials

2. **Configure Azure AD settings**:
   - Navigate to **Accounts** → **Azure AD Settings**
   - Click **"Add Azure AD Settings"**
   - Fill in the configuration:
     ```
     ✅ Enabled: Check this box
     Tenant ID: your-tenant-id-from-azure
     Client ID: your-client-id-from-azure  
     Client Secret: your-client-secret-from-azure
     ✅ Sync Enabled: Check this box
     ✅ Sync on User Create: Check this box
     ✅ Sync on User Update: Check this box
     ✅ Sync on User Disable: Check this box
     ```

3. **Test the connection**:
   - Select the Azure AD Settings record
   - Choose **"Test Azure AD connection"** from Actions dropdown
   - Verify you see "✅ Azure AD connection test successful!"

### Step 3: Using Azure AD Integration

**When you create users in D.A.N.I:**
1. Users are automatically created in Azure AD
2. Temporary passwords are generated
3. Sync status is tracked in real-time
4. Failed syncs can be retried

**Monitoring sync status:**
- View user sync status in the Users list
- Check sync dashboard at `/api/accounts/azure-ad/dashboard/`
- Filter users by sync status

### Required Azure AD Permissions Summary

| Permission | Type | Purpose |
|------------|------|---------|
| `User.ReadWrite.All` | Application | Create, update, delete users |
| `User.ManageIdentities.All` | Application | Manage user identities and authentication |
| `Directory.ReadWrite.All` | Application | Read/write directory data |
| `Group.ReadWrite.All` | Application | Manage group memberships (optional) |

### Removing Azure AD Connection

1. **Disable sync in admin panel**:
   - Go to **Accounts** → **Azure AD Settings**
   - Uncheck **"Enabled"** and **"Sync Enabled"**
   - Save the settings

2. **Optional: Remove app registration**:
   - Go to Azure Portal → App registrations
   - Find your D.A.N.I app registration
   - Delete the registration

3. **Clean up user sync status** (optional):
   ```bash
   # Reset all sync statuses
   docker-compose exec web python manage.py shell -c "
   from accounts.models import User
   User.objects.all().update(
       azure_ad_object_id=None,
       azure_ad_sync_status='disabled',
       azure_ad_sync_enabled=False
   )
   print('Azure AD sync disabled for all users')
   "
   ```

---

## 💾 Backup and Restore

### Automated Backup Commands

```bash
# Database backup (built-in command)
make backup-db

# This creates: backup_YYYYMMDD_HHMMSS.sql

# Media files backup
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/

# Complete system backup
tar -czf hris_complete_backup_$(date +%Y%m%d).tar.gz \
  --exclude=logs \
  --exclude=staticfiles \
  --exclude=postgres_data \
  --exclude=redis_data \
  .
```

### Automated Backup Script

Create a backup script for regular backups:

```bash
# Create backup script
cat > backup_hris.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/hris"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

cd /path/to/hris_platform

# Database backup
make backup-db
mv backup_*.sql $BACKUP_DIR/database_backup_$DATE.sql

# Media backup
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz media/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x backup_hris.sh

# Schedule daily backups
(crontab -l ; echo "0 2 * * * /path/to/backup_hris.sh") | crontab -
```

### Restore Procedures

```bash
# Restore database
make restore-db BACKUP_FILE=backup_20241203_143022.sql

# Restore media files
tar -xzf media_backup_20241203.tar.gz

# Full system restore
# 1. Deploy fresh installation
make clean && make init

# 2. Stop services
make down

# 3. Restore database
make restore-db BACKUP_FILE=your_backup.sql

# 4. Restore media files
tar -xzf media_backup.tar.gz

# 5. Restart services
make up
```

### Data Storage Locations

**Docker Volumes (persistent data):**
- `postgres_data`: Database data
- `redis_data`: Cache data

**Local Directories:**
- `./media/`: User uploaded files
- `./staticfiles/`: Static web assets  
- `./logs/`: Application logs

**To backup Docker volumes:**
```bash
# Backup volumes
docker run --rm -v hris_platform_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_volume_backup.tar.gz -C /data .
docker run --rm -v hris_platform_redis_data:/data -v $(pwd):/backup alpine tar czf /backup/redis_volume_backup.tar.gz -C /data .

# Restore volumes
docker run --rm -v hris_platform_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_volume_backup.tar.gz -C /data
```

---

## 🔧 Production Deployment

### Environment Configuration

Create `.env` file for production:
```bash
# Django Production Settings
DEBUG=False
SECRET_KEY=your-super-secure-secret-key-generate-with-python-secrets
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,your-server-ip

# Database Configuration
DB_NAME=hris_platform
DB_USER=postgres
DB_PASSWORD=your-very-secure-database-password
DB_HOST=postgres
DB_PORT=5432

# Email Configuration (for notifications)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-company-email@domain.com
EMAIL_HOST_PASSWORD=your-app-password

# Security Settings
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_BROWSER_XSS_FILTER=True
SECURE_CONTENT_TYPE_NOSNIFF=True

# Azure AD Configuration (optional)
AZURE_AD_ENABLED=false
# Fill these if using Azure AD:
# AZURE_AD_TENANT_ID=your-tenant-id
# AZURE_AD_CLIENT_ID=your-client-id
# AZURE_AD_CLIENT_SECRET=your-client-secret
```

### Performance Optimization

```bash
# Increase worker processes for production
# Edit docker-compose.yml CMD line:
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "gevent", "hris_platform.wsgi:application"]

# Set up proper logging
# Logs are automatically stored in ./logs/django.log

# Configure Redis for persistence
# Redis data is automatically persisted in redis_data volume
```

---

## 📊 Monitoring and Maintenance

### Health Checks

```bash
# Check service health
make health

# Monitor logs
make logs-f

# Check database performance
docker-compose exec postgres psql -U postgres -d hris_platform -c "SELECT * FROM pg_stat_activity;"
```

### Useful Make Commands

```bash
make help           # Show all available commands
make up             # Start development environment  
make up-prod        # Start production environment
make down           # Stop all services
make restart        # Restart all services
make logs           # View logs
make logs-f         # Follow logs
make shell          # Django shell
make bash           # Container bash access
make test           # Run tests
make migrate        # Run database migrations
make backup-db      # Backup database
make clean          # Clean containers and volumes
make health         # Check service health
```

---

## 💼 Job Titles Management

### Overview
D.A.N.I includes a comprehensive job title management system that standardizes position information across your organization. This replaces free-text job title entry with a centralized, dropdown-based system.

### Features
- **Centralized Management**: Create and manage all job titles from one location
- **Salary Ranges**: Define minimum and maximum salary ranges for each position
- **Skill Requirements**: Document required skills for each role
- **Department Association**: Link job titles to specific departments
- **Job Levels**: Categorize positions by level (Entry, Mid, Senior, Lead, Manager)
- **Employee Tracking**: See how many employees have each job title

### Accessing Job Titles Management
1. **Login to Admin Interface**: http://your-server:8000/admin/
2. **Navigate to**: Employee Management → Job Titles
3. **Add/Edit**: Create new job titles or modify existing ones

### Job Title Fields
- **Title**: The official job title name (required, unique)
- **Description**: Detailed job description and responsibilities
- **Department**: Primary department for this position
- **Level**: Job level categorization
- **Salary Range**: Minimum and maximum salary (optional)
- **Required Skills**: Comma-separated list of required skills
- **Active Status**: Enable/disable job titles

### Using Job Titles
Once created, job titles automatically appear as dropdown options when:
- Creating new users in the admin interface
- Editing existing user profiles
- Creating employee profiles
- Importing user data

### Migration from Text Fields
When upgrading to the job title system, D.A.N.I automatically:
- ✅ Preserves existing job title data
- ✅ Creates JobTitle records from unique existing titles
- ✅ Links users to appropriate JobTitle records
- ✅ Maintains data integrity throughout the process

### API Endpoints
```bash
# List all job titles
GET /api/employees/job-titles/

# Create new job title
POST /api/employees/job-titles/
{
  "title": "Senior Software Engineer",
  "description": "Lead development of complex software systems",
  "department": 1,
  "level": "Senior",
  "min_salary": 90000,
  "max_salary": 120000,
  "required_skills": "Python, Django, PostgreSQL, Docker"
}

# Update job title
PUT /api/employees/job-titles/{id}/

# Get job title details
GET /api/employees/job-titles/{id}/
```

---

## 🔒 Security Considerations

### Essential Security Steps

1. **Change default credentials immediately**
2. **Use strong SECRET_KEY** (generate with: `python -c "import secrets; print(secrets.token_urlsafe(50))"`)
3. **Enable HTTPS in production** with SSL certificates
4. **Configure proper CORS settings** for your domain
5. **Set up firewall rules** to restrict access
6. **Enable database backups** and test restore procedures
7. **Monitor logs regularly** for security events
8. **Keep Docker images updated** regularly
9. **Use strong passwords** for database and admin accounts
10. **Implement proper access controls** for Azure AD

### Network Security

```bash
# Recommended firewall setup
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## 🚀 API Documentation

### Azure AD Sync Endpoints

```bash
# Sync specific user to Azure AD
POST /api/accounts/azure-ad/sync/user/{id}/
Content-Type: application/json
{
  "action": "sync",  # or "create", "update", "disable", "delete" - "sync" is intelligent create/update
  "force": false
}

# Bulk sync users
POST /api/accounts/azure-ad/sync/bulk/
{
  "user_ids": [1, 2, 3],
  "action": "sync"  # intelligent sync (default) - creates new or updates existing users
}

# Get sync dashboard
GET /api/accounts/azure-ad/dashboard/

# Test Azure AD connection
GET /api/accounts/azure-ad/test/

# Get user sync status
GET /api/accounts/azure-ad/user/{id}/status/
```

### Authentication Endpoints
```
POST /api/auth/login/          # User login
POST /api/auth/refresh/        # Refresh JWT token
```

### User Management
```
POST   /api/accounts/register/           # User registration
GET    /api/accounts/users/              # List users
GET    /api/accounts/profile/me/         # Current user profile
PUT    /api/accounts/profile/{id}/       # Update user profile
POST   /api/accounts/password/change/    # Change password
```

### Employee Management
```
GET    /api/employees/departments/       # List departments
POST   /api/employees/departments/       # Create department
GET    /api/employees/job-titles/        # List job titles
POST   /api/employees/job-titles/        # Create job title
GET    /api/employees/profiles/          # List employee profiles
POST   /api/employees/profiles/          # Create employee profile
GET    /api/employees/performance-reviews/ # List performance reviews
POST   /api/employees/performance-reviews/ # Create performance review
GET    /api/employees/time-off-requests/ # List time-off requests
POST   /api/employees/time-off-requests/ # Create time-off request
```

### Recruitment Management
```
GET    /api/recruitment/jobs/            # List job postings
POST   /api/recruitment/jobs/            # Create job posting
GET    /api/recruitment/applicants/      # List applicants
POST   /api/recruitment/applicants/      # Create application
GET    /api/recruitment/interviews/      # List interviews
POST   /api/recruitment/interviews/      # Schedule interview
GET    /api/recruitment/offers/          # List job offers
POST   /api/recruitment/offers/          # Create job offer
GET    /api/recruitment/dashboard/       # Recruitment analytics
```

---

## 🎯 User Roles & Permissions

### Admin
- Full system access
- User management
- System configuration
- Azure AD configuration
- All HR and recruitment operations

### HR Manager
- Employee management
- All recruitment operations
- Performance review oversight
- Time-off approval
- HR analytics and reporting
- Azure AD user sync management

### Hiring Manager
- Department employee management
- Department job postings
- Interview scheduling
- Candidate evaluation
- Time-off approval for direct reports

### Employee
- Personal profile management
- Time-off requests
- View company job postings
- Performance review participation

### Candidate
- Job application submission
- Application status tracking
- Interview participation

---

## 🛠️ Development

### Project Structure
```
hris_platform/
├── accounts/                 # User authentication and Azure AD
│   ├── models.py            # User model with Azure AD fields
│   ├── azure_ad_service.py  # Microsoft Graph API integration
│   ├── azure_ad_views.py    # Azure AD sync API endpoints
│   ├── tasks.py             # Celery tasks for background sync
│   └── admin.py             # Admin interface with sync actions
├── employees/               # HRIS functionality
│   ├── models.py            # Employee, Department, JobTitle models
│   ├── admin.py             # Job Titles, Employee Profiles management
│   └── views.py             # Employee management API endpoints
├── recruitment/             # ATS functionality
├── hris_platform/           # Main Django project
├── media/                   # User uploads
├── staticfiles/             # Static web assets
├── logs/                    # Application logs
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container configuration
├── docker-compose.yml       # Production deployment
├── docker-compose.dev.yml   # Development overrides
├── Makefile                 # Automation commands
├── AZURE_AD_SETUP.md        # Detailed Azure AD setup guide
└── README.md               # This file
```

### Running Tests
```bash
# Run all tests
make test

# Run specific app tests
docker-compose exec web python manage.py test accounts
docker-compose exec web python manage.py test employees  
docker-compose exec web python manage.py test recruitment

# Run with coverage
make test-cov
```

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the documentation
- Review the [Azure AD Setup Guide](AZURE_AD_SETUP.md)
- Review the [Microsoft Sentinel Integration Guide](MICROSOFT_SENTINEL_INTEGRATION.md)
- Create an issue with detailed information

## 🗺️ Roadmap

- [x] Azure AD/Microsoft Entra integration
- [x] Microsoft Sentinel security monitoring
- [x] Comprehensive backup system
- [x] Production deployment guide
- [x] Standardized Job Titles management system
- [ ] Single Sign-On (SSO) support
- [ ] Advanced reporting dashboard
- [ ] Email notifications
- [ ] Calendar integration
- [ ] Document templates
- [ ] Advanced search functionality
- [ ] API rate limiting
- [ ] Audit logging
- [ ] Mobile app support

---

**🎉 D.A.N.I is ready for enterprise deployment with Azure AD integration, comprehensive backup systems, and production-grade security!**
test
