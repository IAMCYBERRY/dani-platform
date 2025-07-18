#!/bin/bash

# Job Title Migration Script
# This script handles the complete migration of job titles from CharField to ForeignKey

set -e  # Exit on any error

echo "🔄 Starting Job Title Migration Process..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${GREEN}[STEP]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Clean up conflicting migration files
print_step "1. Cleaning up conflicting migration files..."
docker-compose exec web rm -f /app/employees/migrations/0003_add_jobtitle_model.py
docker-compose exec web rm -f /app/employees/migrations/0004_migrate_job_titles_data.py
docker-compose exec web find /app -name "0003_jobtitle_alter_employeeprofile_job_title_and_more.py" -delete
docker-compose exec web find /app -name "0010_alter_user_job_title.py" -delete

# Step 2: Reset to clean migration state
print_step "2. Resetting to clean migration state..."
docker-compose exec web python manage.py migrate employees 0002
docker-compose exec web python manage.py migrate accounts 0009

# Step 3: Create new migrations
print_step "3. Creating new migrations..."
docker-compose exec web python manage.py makemigrations employees --name add_jobtitle_model
docker-compose exec web python manage.py makemigrations accounts --name add_jobtitle_fields
docker-compose exec web python manage.py makemigrations employees --name add_jobtitle_fields

# Step 4: Apply migrations
print_step "4. Applying migrations..."
docker-compose exec web python manage.py migrate

# Step 5: Data migration
print_step "5. Running data migration..."
docker-compose exec web python manage.py shell << 'EOF'
from django.db import connection, transaction
from employees.models import JobTitle
from accounts.models import User
from employees.models import EmployeeProfile

print("🔄 Starting data migration...")

with transaction.atomic():
    # Copy existing job_title data to job_title_old fields
    with connection.cursor() as cursor:
        # Update users - copy job_title to job_title_old where job_title is text
        cursor.execute("""
            UPDATE users 
            SET job_title_old = job_title 
            WHERE job_title IS NOT NULL 
            AND job_title != '' 
            AND job_title !~ '^[0-9]+$';
        """)
        print(f"✓ Copied {cursor.rowcount} user job titles to backup field")
        
        # Update employee_profiles
        cursor.execute("""
            UPDATE employee_profiles 
            SET job_title_old = job_title 
            WHERE job_title IS NOT NULL 
            AND job_title != '' 
            AND job_title !~ '^[0-9]+$';
        """)
        print(f"✓ Copied {cursor.rowcount} employee profile job titles to backup field")
        
        # Clear the old job_title fields that contain text
        cursor.execute("""
            UPDATE users 
            SET job_title_id = NULL 
            WHERE job_title !~ '^[0-9]+$' OR job_title IS NULL OR job_title = '';
        """)
        print(f"✓ Cleared {cursor.rowcount} user job_title fields")
        
        cursor.execute("""
            UPDATE employee_profiles 
            SET job_title_id = NULL 
            WHERE job_title !~ '^[0-9]+$' OR job_title IS NULL OR job_title = '';
        """)
        print(f"✓ Cleared {cursor.rowcount} employee profile job_title fields")

    # Get all unique job titles from the backup fields
    job_titles = set()
    
    # From users
    users_with_titles = User.objects.exclude(job_title_old__isnull=True).exclude(job_title_old__exact='')
    for user in users_with_titles:
        if user.job_title_old:
            job_titles.add(user.job_title_old.strip())
    
    # From employee profiles
    try:
        profiles_with_titles = EmployeeProfile.objects.exclude(job_title_old__isnull=True).exclude(job_title_old__exact='')
        for profile in profiles_with_titles:
            if profile.job_title_old:
                job_titles.add(profile.job_title_old.strip())
    except:
        print("Note: EmployeeProfile job_title_old field not found, skipping...")
    
    print(f"📊 Found {len(job_titles)} unique job titles: {list(job_titles)}")
    
    # Create JobTitle objects
    created_titles = {}
    for title in job_titles:
        if title:
            job_title_obj, created = JobTitle.objects.get_or_create(
                title=title,
                defaults={
                    'description': 'Migrated from existing data',
                    'is_active': True
                }
            )
            created_titles[title] = job_title_obj
            if created:
                print(f"✓ Created JobTitle: {title}")
            else:
                print(f"⚪ JobTitle already exists: {title}")
    
    # Update foreign key relationships
    for user in users_with_titles:
        if user.job_title_old and user.job_title_old in created_titles:
            user.job_title = created_titles[user.job_title_old]
            user.save()
    
    try:
        for profile in profiles_with_titles:
            if profile.job_title_old and profile.job_title_old in created_titles:
                profile.job_title = created_titles[profile.job_title_old]
                profile.save()
    except:
        print("Note: Skipping employee profile updates...")
    
    print("✅ Data migration completed successfully!")

EOF

print_step "6. Verifying migration..."
docker-compose exec web python manage.py shell << 'EOF'
from employees.models import JobTitle
from accounts.models import User

print(f"📊 JobTitle records created: {JobTitle.objects.count()}")
print("Job titles:")
for jt in JobTitle.objects.all():
    print(f"  - {jt.title}")

print(f"\n👥 Users with job titles: {User.objects.exclude(job_title__isnull=True).count()}")
EOF

echo ""
echo "🎉 ================================================================"
echo "🎉 Job Title Migration Complete!"
echo "🎉 ================================================================"
echo ""
print_step "You can now access Django Admin → Employee Management → Job Titles"
print_warning "Remember to remove the temporary job_title_old fields later if needed"
echo ""