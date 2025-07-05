"""
Django management command for Azure AD user synchronization.

Usage:
    python manage.py sync_azure_ad --user email@domain.com
    python manage.py sync_azure_ad --all-pending
    python manage.py sync_azure_ad --all-pending --dry-run
    python manage.py sync_azure_ad --user email@domain.com --force
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from accounts.azure_ad_service import azure_ad_service

User = get_user_model()


class Command(BaseCommand):
    help = 'Sync users with Azure AD'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Email of specific user to sync'
        )
        parser.add_argument(
            '--all-pending',
            action='store_true',
            help='Sync all users with pending status'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without actually syncing'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force sync even if user sync is disabled'
        )

    def handle(self, *args, **options):
        if options['user']:
            self.sync_specific_user(options['user'], options['dry_run'], options['force'])
        elif options['all_pending']:
            self.sync_pending_users(options['dry_run'], options['force'])
        else:
            raise CommandError('Must specify either --user or --all-pending')

    def sync_specific_user(self, email, dry_run, force):
        """Sync a specific user by email."""
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f'User with email "{email}" does not exist')

        if dry_run:
            self.stdout.write(f'Would sync user: {user.email} (Status: {user.azure_ad_sync_status})')
            return

        self.stdout.write(f'Syncing user: {user.email}...')
        success, result = azure_ad_service.sync_user_from_hris(user, force_create=force)
        
        if success:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Successfully synced {user.email}')
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to sync {user.email}: {result.get("error", result)}')
            )

    def sync_pending_users(self, dry_run, force):
        """Sync all users with pending status."""
        if force:
            users = User.objects.filter(azure_ad_sync_enabled=True)
            self.stdout.write(f'Found {users.count()} users with sync enabled')
        else:
            users = User.objects.filter(
                azure_ad_sync_enabled=True,
                azure_ad_sync_status='pending'
            )
            self.stdout.write(f'Found {users.count()} users with pending sync status')

        if dry_run:
            for user in users:
                self.stdout.write(f'Would sync: {user.email} (Status: {user.azure_ad_sync_status})')
            return

        synced_count = 0
        failed_count = 0

        for user in users:
            self.stdout.write(f'Syncing: {user.email}...')
            success, result = azure_ad_service.sync_user_from_hris(user, force_create=force)
            
            if success:
                synced_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Successfully synced {user.email}')
                )
            else:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f'❌ Failed to sync {user.email}: {result.get("error", result)}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n📊 Sync Summary: {synced_count} succeeded, {failed_count} failed')
        )