"""
Django settings for D.A.N.I (Domain Access & Navigation Interface).

This is a production-ready configuration for a self-hosted HRIS + ATS SaaS platform.
"""

import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

# Dynamic ALLOWED_HOSTS configuration
import socket
import subprocess

def get_server_ip():
    """Get the server's IP address for ALLOWED_HOSTS (prioritize internal IP for self-hosted deployment)"""
    
    # For self-hosted applications, prioritize internal/private IP addresses
    try:
        # Method 1: Socket method (gets internal IP used for outbound connections)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        # Prefer this internal IP for self-hosted deployments
        return ip
    except:
        pass
    
    try:
        # Method 2: Get internal IP via routing table
        result = subprocess.run(['ip', 'route', 'get', '8.8.8.8'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            for line in result.stdout.split():
                if line.startswith('src'):
                    continue
                if '.' in line and len(line.split('.')) == 4:
                    return line
    except:
        pass
    
    try:
        # Method 3: Only try external IP as last resort (for public deployments)
        # Note: This is commented out to prioritize internal IPs for self-hosted tools
        # Uncomment if you need external IP detection for public-facing deployments
        # result = subprocess.run(['curl', '-s', '-4', 'ifconfig.me'], 
        #                       capture_output=True, text=True, timeout=5)
        # if result.returncode == 0 and result.stdout.strip():
        #     return result.stdout.strip()
        pass
    except:
        pass
    
    return None

# Base allowed hosts from environment
allowed_hosts = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,0.0.0.0').split(',')
allowed_hosts = [host.strip() for host in allowed_hosts if host.strip()]

# Add server IP if we can detect it
server_ip = get_server_ip()
if server_ip and server_ip not in allowed_hosts:
    allowed_hosts.append(server_ip)

# Allow all hosts in DEBUG mode
if DEBUG:
    allowed_hosts.append('*')

ALLOWED_HOSTS = allowed_hosts

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
]

LOCAL_APPS = [
    'accounts',
    'employees',
    'recruitment',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'recruitment.middleware.PowerAppsCorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'hris_platform.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'hris_platform.wsgi.application'

# Database configuration for PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='hris_platform'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
# Only add to STATICFILES_DIRS if the directory exists
STATICFILES_DIRS = []
if (BASE_DIR / 'static').exists():
    STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files (User uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# JWT Configuration
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# CORS configuration
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS', 
    default='http://localhost:3000,http://127.0.0.1:3000'
).split(',')

CORS_ALLOW_CREDENTIALS = True

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Email configuration (for production)
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

# Celery configuration for background tasks
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Azure AD / Microsoft Graph API Configuration
AZURE_AD_ENABLED = config('AZURE_AD_ENABLED', default=False, cast=bool)
AZURE_AD_TENANT_ID = config('AZURE_AD_TENANT_ID', default='')
AZURE_AD_CLIENT_ID = config('AZURE_AD_CLIENT_ID', default='')
AZURE_AD_CLIENT_SECRET = config('AZURE_AD_CLIENT_SECRET', default='')
AZURE_AD_AUTHORITY = config('AZURE_AD_AUTHORITY', default='https://login.microsoftonline.com/')
AZURE_AD_SCOPE = config('AZURE_AD_SCOPE', default='https://graph.microsoft.com/.default')

# Microsoft Graph API settings
GRAPH_API_VERSION = config('GRAPH_API_VERSION', default='v1.0')
GRAPH_API_BASE_URL = f'https://graph.microsoft.com/{GRAPH_API_VERSION}'

# Azure AD sync settings (disabled by default until properly configured)
AZURE_AD_SYNC_ENABLED = config('AZURE_AD_SYNC_ENABLED', default=False, cast=bool)
AZURE_AD_SYNC_ON_USER_CREATE = config('AZURE_AD_SYNC_ON_USER_CREATE', default=False, cast=bool)
AZURE_AD_SYNC_ON_USER_UPDATE = config('AZURE_AD_SYNC_ON_USER_UPDATE', default=False, cast=bool)
AZURE_AD_SYNC_ON_USER_DISABLE = config('AZURE_AD_SYNC_ON_USER_DISABLE', default=False, cast=bool)
AZURE_AD_DEFAULT_PASSWORD_LENGTH = config('AZURE_AD_DEFAULT_PASSWORD_LENGTH', default=12, cast=int)

# Admin branding
ADMIN_SITE_HEADER = 'D.A.N.I Administration'
ADMIN_SITE_TITLE = 'D.A.N.I Admin Portal'
ADMIN_INDEX_TITLE = 'Welcome to D.A.N.I - Domain Access & Navigation Interface'

# Container-friendly logging configuration
import logging.handlers

# Determine logging configuration based on environment
USE_FILE_LOGGING = config('USE_FILE_LOGGING', default=True, cast=bool)
LOG_LEVEL = config('LOG_LEVEL', default='INFO')

# Create logs directory safely
LOGS_DIR = BASE_DIR / 'logs'
try:
    LOGS_DIR.mkdir(exist_ok=True)
    # Test if we can write to the logs directory
    test_file = LOGS_DIR / 'test.log'
    test_file.touch()
    test_file.unlink()
    file_logging_available = USE_FILE_LOGGING
except (PermissionError, OSError):
    file_logging_available = False

# Configure logging handlers
LOGGING_HANDLERS = {
    'console': {
        'level': LOG_LEVEL,
        'class': 'logging.StreamHandler',
        'formatter': 'verbose',
    },
}

# Add file handler only if available and enabled
if file_logging_available:
    LOGGING_HANDLERS['file'] = {
        'level': LOG_LEVEL,
        'class': 'logging.handlers.RotatingFileHandler',
        'filename': LOGS_DIR / 'django.log',
        'maxBytes': 1024*1024*10,  # 10MB
        'backupCount': 5,
        'formatter': 'verbose',
    }

# Choose handlers based on availability
if file_logging_available:
    DEFAULT_HANDLERS = ['console', 'file']
else:
    DEFAULT_HANDLERS = ['console']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': LOGGING_HANDLERS,
    'loggers': {
        'django': {
            'handlers': DEFAULT_HANDLERS,
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'hris_platform': {
            'handlers': DEFAULT_HANDLERS,
            'level': LOG_LEVEL,
            'propagate': True,
        },
    },
    'root': {
        'handlers': DEFAULT_HANDLERS,
        'level': LOG_LEVEL,
    },
}