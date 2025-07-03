# D.A.N.I Local Development Guide

This guide walks you through setting up D.A.N.I for local development on your machine.

## 🖥️ Prerequisites

### Required Software
- **Docker** (20.10+) and **Docker Compose** (2.0+)
- **Git** (for cloning and version control)
- **Make** (for running development commands)
- **Code Editor** (VS Code, PyCharm, etc.)

### System Requirements
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **Ports**: 8000, 5432, 6379 should be available

## 🚀 Quick Start (5 minutes)

### 1. Clone the Repository
```bash
git clone https://github.com/IAMCYBERRY/dani-platform.git
cd dani-platform
```

### 2. Switch to Development Branch
```bash
git checkout develop
# Or work on a specific feature
git checkout feature/azure-ad-connection-fix
```

### 3. Start Development Environment
```bash
# One command setup
make init

# Or step by step:
make build    # Build Docker images
make up       # Start services
```

### 4. Access the Application
- **Main App**: http://localhost:8000/
- **Admin Panel**: http://localhost:8000/admin/
- **API Docs**: http://localhost:8000/api/

**Default Credentials:**
- Email: `admin@dani.local`
- Password: `admin123`

## 🛠️ Development Workflow

### Daily Development Commands

```bash
# Start development environment
make up

# View logs (follow mode)
make logs-f

# Access Django shell
make shell

# Run database migrations
make migrate

# Create new migrations
make makemigrations

# Run tests
make test

# Stop services
make down

# Restart services
make restart
```

### Working with Git Branches

```bash
# Create new feature branch
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name

# Make changes, then commit
git add .
git commit -m "feat: description of your changes"

# Push feature branch
git push -u origin feature/your-feature-name

# Create pull request on GitHub to merge into develop
```

### Environment Configuration

#### 1. Copy Environment Template
```bash
cp .env.example .env
```

#### 2. Edit Local Settings
```bash
nano .env
```

**Key Local Development Settings:**
```env
# Debug mode for development
DEBUG=True

# Local database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=hris_platform
DB_USER=postgres
DB_PASSWORD=postgres

# Local Redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Allowed hosts for local development
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,*

# Azure AD (optional for local testing)
AZURE_AD_ENABLED=false
AZURE_AD_TENANT_ID=your-tenant-id
AZURE_AD_CLIENT_ID=your-client-id
AZURE_AD_CLIENT_SECRET=your-client-secret
```

## 🔧 Development Tools

### Database Management

```bash
# Access PostgreSQL directly
docker-compose exec postgres psql -U postgres -d hris_platform

# Backup database
make backup-db

# Restore database
make restore-db BACKUP_FILE=backup_20231201_120000.sql

# Reset database (⚠️ Deletes all data!)
docker-compose down -v
make up
```

### Debugging

#### Django Debug Toolbar (Optional)
Add to your local requirements:
```bash
# Add to requirements-dev.txt
django-debug-toolbar==4.2.0
```

#### VS Code Development Container
Create `.devcontainer/devcontainer.json`:
```json
{
    "name": "D.A.N.I Development",
    "dockerComposeFile": ["../docker-compose.yml"],
    "service": "web",
    "workspaceFolder": "/app",
    "customizations": {
        "vscode": {
            "extensions": [
                "ms-python.python",
                "ms-python.flake8",
                "ms-python.black-formatter"
            ]
        }
    }
}
```

### Code Quality Tools

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Format code with Black
black .

# Lint with flake8
flake8 .

# Type checking with mypy
mypy .
```

## 🧪 Testing

### Run All Tests
```bash
make test
```

### Run Specific Tests
```bash
# Test specific app
docker-compose exec web python manage.py test accounts

# Test specific test case
docker-compose exec web python manage.py test accounts.tests.TestUserModel

# Run with coverage
make test-cov
```

### Test Azure AD Integration
```bash
# Test Azure AD connection
docker-compose exec web python manage.py test_azure_ad --verbose

# Test specific Azure AD functionality
docker-compose exec web python manage.py shell
>>> from accounts.azure_ad_service import azure_ad_service
>>> success, result = azure_ad_service.test_connection()
>>> print(f"Success: {success}, Result: {result}")
```

## 📦 Adding New Features

### 1. Create Django App
```bash
docker-compose exec web python manage.py startapp your_app_name
```

### 2. Add to INSTALLED_APPS
Edit `hris_platform/settings.py`:
```python
LOCAL_APPS = [
    'accounts',
    'employees', 
    'recruitment',
    'your_app_name',  # Add your new app
]
```

### 3. Create Models
```python
# your_app_name/models.py
from django.db import models

class YourModel(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
```

### 4. Create and Run Migrations
```bash
make makemigrations
make migrate
```

### 5. Register in Admin
```python
# your_app_name/admin.py
from django.contrib import admin
from .models import YourModel

@admin.register(YourModel)
class YourModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
```

## 🐳 Docker Development

### Useful Docker Commands

```bash
# View running containers
docker-compose ps

# Check container logs
docker-compose logs web
docker-compose logs postgres
docker-compose logs redis

# Execute commands in containers
docker-compose exec web bash
docker-compose exec postgres psql -U postgres
docker-compose exec redis redis-cli

# Rebuild specific service
docker-compose build web

# Remove all containers and volumes (⚠️ Data loss!)
docker-compose down -v --rmi all
```

### Development with Hot Reload

The development setup includes:
- **Auto-reload**: Django development server automatically reloads on code changes
- **Volume mounts**: Your local code is mounted into the container
- **Debug mode**: Detailed error pages and SQL query logging

## 🔍 Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Check what's using the port
lsof -i :8000
sudo lsof -i :5432
sudo lsof -i :6379

# Kill processes if needed
sudo kill -9 <PID>
```

#### Permission Denied Errors
```bash
# Fix Docker permissions (Linux)
sudo usermod -aG docker $USER
newgrp docker

# Fix file permissions
chmod +x entrypoint.sh
chmod +x *.sh
```

#### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Reset database
docker-compose down
docker volume rm dani_postgres_data
make up
```

#### Module Import Errors
```bash
# Rebuild Python environment
docker-compose build web --no-cache
make up
```

### Performance Optimization

#### For Large Datasets
```python
# In settings.py for development
DATABASES = {
    'default': {
        # ... existing config
        'OPTIONS': {
            'MAX_CONNS': 20,
            'conn_max_age': 600,
        }
    }
}
```

#### Memory Usage
```bash
# Monitor container memory usage
docker stats

# Limit container memory
# Add to docker-compose.yml:
# deploy:
#   resources:
#     limits:
#       memory: 512M
```

## 🔄 Development Best Practices

### Code Organization
```
dani-platform/
├── accounts/           # User management
├── employees/          # Employee data
├── recruitment/        # ATS functionality
├── hris_platform/      # Django settings
├── templates/          # HTML templates
├── static/            # Static files
├── media/             # User uploads
└── tests/             # Test files
```

### Environment Variables
- Use `.env` for local development
- Never commit secrets to git
- Document all environment variables in `.env.example`

### Database Migrations
- Create descriptive migration names
- Test migrations on sample data
- Always backup before running migrations in production

### Testing Strategy
- Write tests for all new features
- Aim for >80% code coverage
- Test both success and failure scenarios
- Use factories for test data

## 📚 Learning Resources

### Django Development
- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Django Best Practices](https://django-best-practices.readthedocs.io/)

### D.A.N.I Specific
- [API Documentation](http://localhost:8000/api/)
- [Admin Interface](http://localhost:8000/admin/)
- [Azure AD Setup Guide](./AZURE_AD_SETUP.md)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)

## 🆘 Getting Help

### Local Development Issues
1. Check container logs: `make logs-f`
2. Verify services are running: `docker-compose ps`
3. Test database connectivity: `make shell`
4. Check environment variables: `cat .env`

### Community Support
- **GitHub Issues**: [Report bugs or request features](https://github.com/IAMCYBERRY/dani-platform/issues)
- **Discussions**: [Ask questions and share ideas](https://github.com/IAMCYBERRY/dani-platform/discussions)

---

**Happy Coding! 🚀**

*This guide covers the essential aspects of local D.A.N.I development. For production deployment, see [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md).*