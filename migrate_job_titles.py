#!/usr/bin/env python
"""
Data migration script to convert job_title CharField to JobTitle ForeignKey.
This script should be run before applying the model changes.
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hris_platform.settings')

# Setup Django
django.setup()

from accounts.models import User
from employees.models import EmployeeProfile

def migrate_job_titles():
    """
    Convert existing job_title text values to JobTitle objects.
    """
    print("🔄 Starting job title migration...")
    
    # Create JobTitle model if it doesn't exist
    try:
        from employees.models import JobTitle
        print("✓ JobTitle model is available")
    except ImportError:
        print("❌ JobTitle model not found. Make sure the model changes are applied first.")
        return False
    
    # Collect all unique job titles from both User and EmployeeProfile
    job_titles_set = set()
    
    # Get job titles from User model
    users_with_titles = User.objects.exclude(job_title__isnull=True).exclude(job_title__exact='')
    for user in users_with_titles:
        if hasattr(user.job_title, 'title'):
            # Already converted to ForeignKey, skip
            continue
        job_titles_set.add(user.job_title.strip())
    
    # Get job titles from EmployeeProfile model if it exists
    try:
        profiles_with_titles = EmployeeProfile.objects.exclude(job_title__isnull=True).exclude(job_title__exact='')
        for profile in profiles_with_titles:
            if hasattr(profile.job_title, 'title'):
                # Already converted to ForeignKey, skip
                continue
            job_titles_set.add(profile.job_title.strip())
    except:
        # EmployeeProfile might not have job_title field yet
        pass
    
    print(f"📊 Found {len(job_titles_set)} unique job titles to migrate")
    
    # Create JobTitle objects for each unique title
    created_titles = {}
    for title in job_titles_set:
        if title:  # Skip empty titles
            job_title_obj, created = JobTitle.objects.get_or_create(
                title=title,
                defaults={
                    'description': f'Migrated from existing data: {title}',
                    'is_active': True
                }
            )
            created_titles[title] = job_title_obj
            if created:
                print(f"✓ Created JobTitle: {title}")
            else:
                print(f"⚪ JobTitle already exists: {title}")
    
    print(f"✅ Migration completed! Created {len(created_titles)} job title records.")
    
    return True

if __name__ == "__main__":
    try:
        migrate_job_titles()
        print("\n🎉 Job title migration completed successfully!")
        print("You can now proceed with the Django migrations.")
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)