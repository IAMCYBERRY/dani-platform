#!/usr/bin/env python
"""
Script to fix job title migration issues by handling data conversion manually.
Run this inside the Django container.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hris_platform.settings')
django.setup()

from django.db import connection, transaction

def fix_job_titles():
    """
    Fix the job title migration by updating existing data properly.
    """
    print("🔧 Fixing job title migration...")
    
    with connection.cursor() as cursor:
        try:
            # Check if JobTitle table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'job_titles'
                );
            """)
            job_titles_table_exists = cursor.fetchone()[0]
            
            if not job_titles_table_exists:
                print("❌ JobTitle table doesn't exist yet. Run migrations first.")
                return False
            
            # Get all unique job titles from users table
            print("📊 Collecting existing job titles...")
            cursor.execute("""
                SELECT DISTINCT job_title 
                FROM users 
                WHERE job_title IS NOT NULL 
                AND job_title != ''
                AND job_title ~ '^[0-9]+$' = FALSE;
            """)
            user_job_titles = [row[0] for row in cursor.fetchall() if row[0]]
            
            # Get all unique job titles from employee_profiles table
            cursor.execute("""
                SELECT DISTINCT job_title 
                FROM employee_profiles 
                WHERE job_title IS NOT NULL 
                AND job_title != ''
                AND job_title ~ '^[0-9]+$' = FALSE;
            """)
            profile_job_titles = [row[0] for row in cursor.fetchall() if row[0]]
            
            # Combine all job titles
            all_job_titles = list(set(user_job_titles + profile_job_titles))
            print(f"📝 Found {len(all_job_titles)} unique job titles: {all_job_titles}")
            
            # Create JobTitle records for each unique title
            job_title_mapping = {}
            for title in all_job_titles:
                if title:
                    cursor.execute("""
                        INSERT INTO job_titles (title, description, is_active, created_at, updated_at)
                        VALUES (%s, %s, %s, NOW(), NOW())
                        ON CONFLICT (title) DO NOTHING
                        RETURNING id;
                    """, [title, f'Migrated from existing data', True])
                    
                    result = cursor.fetchone()
                    if result:
                        job_title_id = result[0]
                        print(f"✓ Created JobTitle: {title} (ID: {job_title_id})")
                    else:
                        # Job title already exists, get its ID
                        cursor.execute("SELECT id FROM job_titles WHERE title = %s;", [title])
                        job_title_id = cursor.fetchone()[0]
                        print(f"⚪ JobTitle already exists: {title} (ID: {job_title_id})")
                    
                    job_title_mapping[title] = job_title_id
            
            print("🔄 Updating user records...")
            # Update users table - set job_title_id where job_title is text
            for title, job_title_id in job_title_mapping.items():
                cursor.execute("""
                    UPDATE users 
                    SET job_title_id = %s 
                    WHERE job_title = %s 
                    AND job_title ~ '^[0-9]+$' = FALSE;
                """, [job_title_id, title])
                updated = cursor.rowcount
                if updated > 0:
                    print(f"✓ Updated {updated} user records for '{title}'")
            
            print("🔄 Updating employee profile records...")
            # Update employee_profiles table - set job_title_id where job_title is text
            for title, job_title_id in job_title_mapping.items():
                cursor.execute("""
                    UPDATE employee_profiles 
                    SET job_title_id = %s 
                    WHERE job_title = %s 
                    AND job_title ~ '^[0-9]+$' = FALSE;
                """, [job_title_id, title])
                updated = cursor.rowcount
                if updated > 0:
                    print(f"✓ Updated {updated} employee profile records for '{title}'")
            
            print("✅ Data migration completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            return False

if __name__ == "__main__":
    try:
        with transaction.atomic():
            if fix_job_titles():
                print("\n🎉 Job title fix completed successfully!")
            else:
                print("\n❌ Job title fix failed!")
                sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)