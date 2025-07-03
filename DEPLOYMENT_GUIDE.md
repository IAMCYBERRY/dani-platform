# D.A.N.I Deployment Guide

This comprehensive guide covers two deployment methods:
1. **GitHub Repository Setup** - Version control and collaboration
2. **Docker Hub Distribution** - Easy VM deployment via Docker images

---

## Part 1: GitHub Repository Setup

### Step 1: Prepare Repository for GitHub

1. **Create .gitignore file**
   ```bash
   cd /Users/ryanwright/Desktop/hris_platform
   cat > .gitignore << 'EOF'
   # Python
   __pycache__/
   *.py[cod]
   *$py.class
   *.so
   .Python
   build/
   develop-eggs/
   dist/
   downloads/
   eggs/
   .eggs/
   lib/
   lib64/
   parts/
   sdist/
   var/
   wheels/
   pip-wheel-metadata/
   share/python-wheels/
   *.egg-info/
   .installed.cfg
   *.egg
   MANIFEST

   # Django
   *.log
   local_settings.py
   db.sqlite3
   db.sqlite3-journal
   /media/
   /staticfiles/
   /static/

   # Environment variables
   .env
   .env.local
   .env.production

   # Docker
   postgres_data/
   redis_data/

   # IDE
   .vscode/
   .idea/
   *.swp
   *.swo
   *~

   # macOS
   .DS_Store

   # Logs
   logs/
   *.log

   # Backup files
   backup_*.sql

   # Temporary files
   tmp/
   temp/
   EOF
   ```

2. **Create environment template**
   ```bash
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

   # Email Configuration (Production)
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

   # Microsoft Sentinel Integration (Optional)
   SENTINEL_ENABLED=false
   SENTINEL_WORKSPACE_ID=
   SENTINEL_SHARED_KEY=
   SENTINEL_LOG_TYPE=DANISecurityEvents

   # Security Settings (Production)
   SECURE_SSL_REDIRECT=False
   SECURE_HSTS_SECONDS=0
   CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
   EOF
   ```

### Step 2: Initialize Git Repository

1. **Initialize Git**
   ```bash
   cd /Users/ryanwright/Desktop/hris_platform
   git init
   git add .
   git commit -m "Initial commit: D.A.N.I HRIS+ATS platform with Azure AD integration

   🔐 Generated with [Claude Code](https://claude.ai/code)

   Co-Authored-By: Claude <noreply@anthropic.com>"
   ```

### Step 3: Create GitHub Repository

1. **Option A: Using GitHub CLI (Recommended)**
   ```bash
   # Install GitHub CLI if not installed
   brew install gh  # macOS
   # or
   # sudo apt install gh  # Ubuntu

   # Login to GitHub
   gh auth login

   # Create repository
   gh repo create dani-platform --private --description "D.A.N.I - Domain Access & Navigation Interface: Self-hosted HRIS+ATS with Azure AD integration"

   # Push to GitHub
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/dani-platform.git
   git push -u origin main
   ```

2. **Option B: Using GitHub Web Interface**
   - Go to [GitHub.com](https://github.com)
   - Click "New repository"
   - Repository name: `dani-platform`
   - Description: `D.A.N.I - Domain Access & Navigation Interface: Self-hosted HRIS+ATS with Azure AD integration`
   - Set to Public
   - Don't initialize with README (we already have one)
   - Click "Create repository"

   Then push your code:
   ```bash
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/dani-platform.git
   git push -u origin main
   ```

### Step 4: Configure Repository Settings

1. **Add Repository Topics** (via GitHub web interface)
   - Go to your repository on GitHub
   - Click the gear icon next to "About"
   - Add topics: `hris`, `ats`, `django`, `docker`, `azure-ad`, `hr-management`, `recruitment`, `python`, `postgresql`

2. **Set up Branch Protection** (Optional but recommended)
   - Go to Settings → Branches
   - Add rule for `main` branch
   - Require pull request reviews
   - Require status checks

---

## Part 2: Docker Hub Distribution

### Step 1: Create Multi-Architecture Dockerfile

1. **Optimize Dockerfile for production**
   ```bash
   cat > Dockerfile.production << 'EOF'
   FROM python:3.11-slim as builder

   # Set environment variables
   ENV PYTHONDONTWRITEBYTECODE=1
   ENV PYTHONUNBUFFERED=1
   ENV DEBIAN_FRONTEND=noninteractive

   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       build-essential \
       libpq-dev \
       curl \
       && rm -rf /var/lib/apt/lists/*

   # Create app directory
   WORKDIR /app

   # Install Python dependencies
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   # Production stage
   FROM python:3.11-slim

   ENV PYTHONDONTWRITEBYTECODE=1
   ENV PYTHONUNBUFFERED=1
   ENV DEBIAN_FRONTEND=noninteractive

   # Install runtime dependencies
   RUN apt-get update && apt-get install -y \
       libpq5 \
       curl \
       && rm -rf /var/lib/apt/lists/* \
       && useradd --create-home --shell /bin/bash dani

   # Copy dependencies from builder
   COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
   COPY --from=builder /usr/local/bin /usr/local/bin

   # Set work directory
   WORKDIR /app

   # Copy application code
   COPY --chown=dani:dani . .

   # Create required directories
   RUN mkdir -p logs media staticfiles && \
       chown -R dani:dani /app

   # Switch to non-root user
   USER dani

   # Collect static files
   RUN python manage.py collectstatic --noinput

   # Health check
   HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
       CMD curl -f http://localhost:8000/admin/ || exit 1

   # Expose port
   EXPOSE 8000

   # Start application
   CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "gevent", "--worker-connections", "1000", "--max-requests", "1000", "--max-requests-jitter", "100", "--timeout", "30", "--keep-alive", "2", "hris_platform.wsgi:application"]
   EOF
   ```

2. **Create production docker-compose**
   ```bash
   cat > docker-compose.production.yml << 'EOF'
   version: '3.8'

   services:
     web:
       image: your-dockerhub-username/dani-platform:latest
       container_name: dani_web
       restart: unless-stopped
       ports:
         - "8000:8000"
       environment:
         - DEBUG=False
         - DB_HOST=postgres
         - DB_PORT=5432
         - CELERY_BROKER_URL=redis://redis:6379/0
       env_file:
         - .env
       depends_on:
         - postgres
         - redis
       volumes:
         - media_files:/app/media
         - static_files:/app/staticfiles
         - app_logs:/app/logs
       networks:
         - dani_network
       healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:8000/admin/"]
         interval: 30s
         timeout: 10s
         retries: 3

     postgres:
       image: postgres:15-alpine
       container_name: dani_postgres
       restart: unless-stopped
       environment:
         POSTGRES_DB: ${DB_NAME:-hris_platform}
         POSTGRES_USER: ${DB_USER:-postgres}
         POSTGRES_PASSWORD: ${DB_PASSWORD:-postgres}
       volumes:
         - postgres_data:/var/lib/postgresql/data
       networks:
         - dani_network
       healthcheck:
         test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-postgres}"]
         interval: 10s
         timeout: 5s
         retries: 5

     redis:
       image: redis:7-alpine
       container_name: dani_redis
       restart: unless-stopped
       volumes:
         - redis_data:/data
       networks:
         - dani_network
       healthcheck:
         test: ["CMD", "redis-cli", "ping"]
         interval: 10s
         timeout: 5s
         retries: 3

     celery:
       image: your-dockerhub-username/dani-platform:latest
       container_name: dani_celery
       restart: unless-stopped
       command: celery -A hris_platform worker -l info
       environment:
         - DEBUG=False
         - DB_HOST=postgres
         - DB_PORT=5432
         - CELERY_BROKER_URL=redis://redis:6379/0
       env_file:
         - .env
       depends_on:
         - postgres
         - redis
       volumes:
         - media_files:/app/media
         - app_logs:/app/logs
       networks:
         - dani_network

     nginx:
       image: nginx:alpine
       container_name: dani_nginx
       restart: unless-stopped
       ports:
         - "80:80"
         - "443:443"
       volumes:
         - ./nginx.prod.conf:/etc/nginx/nginx.conf:ro
         - static_files:/var/www/static:ro
         - media_files:/var/www/media:ro
         - ./ssl:/etc/nginx/ssl:ro
       depends_on:
         - web
       networks:
         - dani_network

   volumes:
     postgres_data:
     redis_data:
     media_files:
     static_files:
     app_logs:

   networks:
     dani_network:
       driver: bridge
   EOF
   ```

### Step 2: Build and Push to Docker Hub

1. **Create Docker Hub account** at [hub.docker.com](https://hub.docker.com)

2. **Login to Docker Hub**
   ```bash
   docker login
   ```

3. **Build multi-architecture images**
   ```bash
   # Create and use buildx builder
   docker buildx create --name dani-builder --use
   docker buildx inspect --bootstrap

   # Build and push multi-architecture image
   docker buildx build \
     --platform linux/amd64,linux/arm64 \
     -f Dockerfile.production \
     -t your-dockerhub-username/dani-platform:latest \
     -t your-dockerhub-username/dani-platform:v1.0.0 \
     --push .
   ```

4. **Create repository description** (via Docker Hub web interface)
   - Go to your repository on Docker Hub
   - Add description: "D.A.N.I - Domain Access & Navigation Interface: Enterprise HRIS+ATS platform with Azure AD integration, built with Django and PostgreSQL."
   - Add README content from your GitHub repository

### Step 3: Automated CI/CD Pipeline

1. **Create GitHub Actions workflow**
   ```bash
   mkdir -p .github/workflows
   cat > .github/workflows/docker-publish.yml << 'EOF'
   name: Build and Push Docker Images

   on:
     push:
       branches: [ main ]
       tags: [ 'v*' ]
     pull_request:
       branches: [ main ]

   env:
     REGISTRY: docker.io
     IMAGE_NAME: your-dockerhub-username/dani-platform

   jobs:
     build:
       runs-on: ubuntu-latest
       permissions:
         contents: read
         packages: write

       steps:
       - name: Checkout repository
         uses: actions/checkout@v4

       - name: Set up Docker Buildx
         uses: docker/setup-buildx-action@v3

       - name: Log in to Docker Hub
         if: github.event_name != 'pull_request'
         uses: docker/login-action@v3
         with:
           registry: ${{ env.REGISTRY }}
           username: ${{ secrets.DOCKER_USERNAME }}
           password: ${{ secrets.DOCKER_PASSWORD }}

       - name: Extract metadata
         id: meta
         uses: docker/metadata-action@v5
         with:
           images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
           tags: |
             type=ref,event=branch
             type=ref,event=pr
             type=semver,pattern={{version}}
             type=semver,pattern={{major}}.{{minor}}
             type=raw,value=latest,enable={{is_default_branch}}

       - name: Build and push Docker image
         uses: docker/build-push-action@v5
         with:
           context: .
           file: ./Dockerfile.production
           platforms: linux/amd64,linux/arm64
           push: ${{ github.event_name != 'pull_request' }}
           tags: ${{ steps.meta.outputs.tags }}
           labels: ${{ steps.meta.outputs.labels }}
           cache-from: type=gha
           cache-to: type=gha,mode=max
   EOF
   ```

2. **Add secrets to GitHub**
   - Go to your GitHub repository
   - Settings → Secrets and variables → Actions
   - Add secrets:
     - `DOCKER_USERNAME`: Your Docker Hub username
     - `DOCKER_PASSWORD`: Your Docker Hub password or access token

---

## Part 3: VM Deployment Instructions

### Option A: Quick Deploy with Docker Compose

1. **On your VM, create deployment directory**
   ```bash
   mkdir -p ~/dani-platform
   cd ~/dani-platform
   ```

2. **Download production compose file**
   ```bash
   curl -O https://raw.githubusercontent.com/YOUR_USERNAME/dani-platform/main/docker-compose.production.yml
   curl -O https://raw.githubusercontent.com/YOUR_USERNAME/dani-platform/main/.env.example
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   nano .env  # Edit with your production values
   ```

4. **Deploy**
   ```bash
   # Update the image name in docker-compose.production.yml
   sed -i 's/your-dockerhub-username/YOUR_ACTUAL_USERNAME/g' docker-compose.production.yml

   # Start services
   docker-compose -f docker-compose.production.yml up -d

   # Wait for services to start
   sleep 30

   # Run migrations
   docker-compose -f docker-compose.production.yml exec web python manage.py migrate

   # Create superuser
   docker-compose -f docker-compose.production.yml exec web python manage.py createsuperuser
   ```

### Option B: Single Command Deployment

1. **Create deployment script**
   ```bash
   cat > deploy-dani.sh << 'EOF'
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
   EOF

   chmod +x deploy-dani.sh
   ```

2. **Deploy with one command**
   ```bash
   curl -s https://raw.githubusercontent.com/YOUR_USERNAME/dani-platform/main/deploy-dani.sh | bash
   ```

### Option C: Docker Run (Minimal Setup)

```bash
# Create network
docker network create dani-network

# Start PostgreSQL
docker run -d \
  --name dani-postgres \
  --network dani-network \
  -e POSTGRES_DB=hris_platform \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=securepassword123 \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:15-alpine

# Start Redis
docker run -d \
  --name dani-redis \
  --network dani-network \
  -v redis_data:/data \
  redis:7-alpine

# Wait for database
sleep 10

# Start D.A.N.I
docker run -d \
  --name dani-web \
  --network dani-network \
  -p 8000:8000 \
  -e DEBUG=False \
  -e DB_HOST=dani-postgres \
  -e DB_PASSWORD=securepassword123 \
  -e SECRET_KEY=$(openssl rand -base64 32) \
  -e ALLOWED_HOSTS=* \
  -v media_files:/app/media \
  -v app_logs:/app/logs \
  your-dockerhub-username/dani-platform:latest

# Run migrations
sleep 15
docker exec dani-web python manage.py migrate

# Create superuser
docker exec -it dani-web python manage.py createsuperuser
```

---

## Part 4: VM Requirements & Setup

### Minimum System Requirements

- **CPU**: 2 cores
- **RAM**: 4GB (8GB recommended)
- **Storage**: 20GB SSD
- **OS**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- **Network**: Public IP with ports 80, 443, 8000 accessible

### VM Preparation

1. **Update system**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Install Docker**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   newgrp docker
   ```

3. **Install Docker Compose**
   ```bash
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

4. **Configure firewall**
   ```bash
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw allow 8000
   sudo ufw enable
   ```

---

## Summary

After following this guide, you'll have:

✅ **GitHub Repository** with:
- Version control and collaboration
- Automated CI/CD pipeline
- Professional documentation
- Issue tracking and project management

✅ **Docker Hub Distribution** with:
- Multi-architecture images (AMD64 + ARM64)
- Automated builds from GitHub
- Easy VM deployment
- Production-ready configuration

✅ **VM Deployment Options**:
- One-command deployment script
- Docker Compose production setup
- Minimal Docker run configuration
- Comprehensive documentation

Your D.A.N.I platform is now ready for enterprise deployment! 🚀
