#!/bin/bash

# Exit on any error
set -e

# Wait for PostgreSQL to be ready (Docker handles this with depends_on)
echo "Starting application..."
sleep 5

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create superuser if it doesn't exist
echo "Creating superuser if it doesn't exist..."
python manage.py shell << EOF
from accounts.models import User
import os

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
    print(f"Superuser {email} created successfully!")
else:
    print(f"Superuser {email} already exists.")
EOF

# Load initial data if specified
if [ "$LOAD_INITIAL_DATA" = "true" ]; then
    echo "Loading initial data..."
    python manage.py loaddata initial_data.json || echo "No initial data file found"
fi

echo "Starting application..."
exec "$@"