#!/bin/bash
# Quick fix script to create .env.example file

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

# Superuser Configuration (for Docker setup)
SUPERUSER_EMAIL=admin@dani.local
SUPERUSER_PASSWORD=admin123

# Application Configuration
LOAD_INITIAL_DATA=False
EOF

echo "✅ .env.example file created successfully!"
echo "Now you can run: make init"