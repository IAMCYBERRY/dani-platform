#!/bin/bash

# Robust entrypoint script for D.A.N.I
set -e

echo "🚀 Starting D.A.N.I application..."

# Function to handle errors gracefully
handle_error() {
    echo "❌ Error occurred: $1"
    echo "Attempting to continue with console-only mode..."
}

# Create required directories with proper permissions
echo "📁 Creating required directories..."
mkdir -p /app/logs /app/media /app/staticfiles

# Try to set permissions, but don't fail if we can't (mounted volumes)
echo "🔧 Setting permissions..."
chmod 755 /app/logs /app/media /app/staticfiles 2>/dev/null || echo "⚠️  Could not change permissions (likely mounted volumes), continuing..."

# Ensure proper ownership if running as root, then switch to app user
if [ "$(id -u)" = "0" ]; then
    echo "👤 Setting proper ownership..."
    chown -R app:app /app/logs /app/media /app/staticfiles 2>/dev/null || echo "⚠️  Could not change ownership (likely mounted volumes), continuing..."
    
    # If we have su-exec, use it to switch to app user
    if command -v su-exec >/dev/null 2>&1; then
        echo "🔄 Switching to app user..."
        exec su-exec app "$0" "$@"
    fi
fi

# Test database connectivity
echo "🔍 Checking database connectivity..."
max_attempts=30
attempt=1
until python manage.py dbshell --command="\q" 2>/dev/null; do
    if [ $attempt -eq $max_attempts ]; then
        echo "❌ Could not connect to database after $max_attempts attempts"
        exit 1
    fi
    echo "⏳ Waiting for database... (attempt $attempt/$max_attempts)"
    sleep 2
    attempt=$((attempt + 1))
done
echo "✅ Database connection established"

# Run database migrations with error handling
echo "🔧 Running database migrations..."
if ! python manage.py migrate --noinput; then
    handle_error "Database migration failed"
    echo "📋 Attempting to show migration status..."
    python manage.py showmigrations || echo "Could not show migration status"
fi

# Collect static files with error handling
echo "📦 Collecting static files..."
if ! python manage.py collectstatic --noinput --clear 2>/dev/null; then
    echo "⚠️  Static file collection failed, trying without --clear..."
    if ! python manage.py collectstatic --noinput; then
        handle_error "Static file collection failed"
        echo "Continuing without static files..."
    fi
fi

# Create superuser if it doesn't exist
echo "👨‍💼 Creating superuser if needed..."
python manage.py shell << 'EOF' || handle_error "Superuser creation failed"
import os
import sys

try:
    from accounts.models import User
    
    email = os.environ.get('SUPERUSER_EMAIL', 'admin@hris.local')
    password = os.environ.get('SUPERUSER_PASSWORD', 'admin123')
    
    if not User.objects.filter(email=email).exists():
        User.objects.create_superuser(
            email=email,
            password=password,
            first_name='System',
            last_name='Administrator',
            role='admin'
        )
        print(f"✅ Superuser {email} created successfully!")
    else:
        print(f"ℹ️  Superuser {email} already exists.")
        
except Exception as e:
    print(f"⚠️  Error creating superuser: {e}")
    sys.exit(0)  # Don't fail the entire startup
EOF

# Load initial data if specified
if [ "$LOAD_INITIAL_DATA" = "true" ]; then
    echo "📊 Loading initial data..."
    python manage.py loaddata initial_data.json 2>/dev/null || echo "ℹ️  No initial data file found"
fi

echo "🎉 D.A.N.I initialization complete!"
echo "🌐 Application will be available on port 8000"

# Start the application
if [ "$1" = "gunicorn" ]; then
    echo "🚀 Starting Gunicorn server..."
    exec gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 30 --keep-alive 2 hris_platform.wsgi:application
elif [ "$1" = "runserver" ]; then
    echo "🚀 Starting Django development server..."
    exec python manage.py runserver 0.0.0.0:8000
else
    echo "🚀 Starting application with command: $@"
    exec "$@"
fi