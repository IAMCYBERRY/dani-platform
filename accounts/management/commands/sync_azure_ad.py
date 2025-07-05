"""
Management command to sync users with Azure AD.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User, AzureADSettings
from accounts.azure_ad_service import azure_ad_service


class Command(BaseCommand):
    help = 'Sync users with Azure AD'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Sync specific user by email',
        )
        parser.add_argument(
            '--all-pending',
            action='store_true',
            help='Sync all pending users',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without actually doing it',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force sync even if user already has Azure AD Object ID',
        )

    def handle(self, *args, **options):
        self.stdout.write("🔄 Azure AD User Sync")
        self.stdout.write("=" * 40)
        
        # Check if Azure AD is configured
        settings = AzureADSettings.get_settings()
        if not settings.is_configured:
            self.stdout.write(self.style.ERROR("❌ Azure AD is not configured"))
            return
        
        if not settings.enabled or not settings.sync_enabled:
            self.stdout.write(self.style.ERROR("❌ Azure AD sync is disabled"))
            return
        
        # Sync specific user
        if options['user']:
            try:
                user = User.objects.get(email=options['user'])
                self.sync_user(user, options['dry_run'], options['force'])
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"❌ User {options['user']} not found"))
            return
        
        # Sync all pending users
        if options['all_pending']:
            pending_users = User.objects.filter(
                azure_ad_sync_status='pending',
                azure_ad_sync_enabled=True
            )
            
            if not pending_users.exists():
                self.stdout.write("ℹ️  No pending users found")
                return
            
            self.stdout.write(f"📋 Found {pending_users.count()} pending users")
            
            for user in pending_users:
                self.sync_user(user, options['dry_run'], options['force'])
            
            return
        
        # Show status by default
        self.show_sync_status()

    def sync_user(self, user, dry_run=False, force=False):
        """Sync a single user with Azure AD."""
        self.stdout.write(f"\n👤 User: {user.email}")
        self.stdout.write(f"   Current Status: {user.azure_ad_sync_status}")
        self.stdout.write(f"   Azure AD ID: {user.azure_ad_object_id or 'None'}")
        self.stdout.write(f"   Sync Enabled: {user.azure_ad_sync_enabled}")
        
        if not user.azure_ad_sync_enabled:
            self.stdout.write("   ⏭️  Skipping (sync disabled for user)")
            return
        
        # Note: We now use intelligent sync that handles both create and update automatically
        # The force flag is still used to override sync_enabled=False
        
        if dry_run:
            self.stdout.write("   🏃 Would sync this user (dry run)")
            return
        
        # Perform the sync
        self.stdout.write("   🔄 Syncing...")
        success, result = azure_ad_service.sync_user_from_hris(user, force_create=True)
        
        if success:
            self.stdout.write(self.style.SUCCESS("   ✅ Sync successful"))
            if 'temporary_password' in result:
                self.stdout.write(f"   🔑 Temporary password: {result['temporary_password']}")
            
            # Refresh user data
            user.refresh_from_db()
            self.stdout.write(f"   🆔 Azure AD Object ID: {user.azure_ad_object_id}")
        else:
            self.stdout.write(self.style.ERROR("   ❌ Sync failed"))
            self.stdout.write(f"   Error: {result.get('error', 'Unknown error')}")
            if 'details' in result:
                self.stdout.write(f"   Details: {result['details']}")

    def show_sync_status(self):
        """Show overall sync status."""
        self.stdout.write("📊 Azure AD Sync Status")
        self.stdout.write("-" * 30)
        
        total_users = User.objects.count()
        sync_enabled = User.objects.filter(azure_ad_sync_enabled=True).count()
        synced_users = User.objects.filter(azure_ad_object_id__isnull=False).count()
        pending_users = User.objects.filter(azure_ad_sync_status='pending').count()
        failed_users = User.objects.filter(azure_ad_sync_status='failed').count()
        
        self.stdout.write(f"Total Users: {total_users}")
        self.stdout.write(f"Sync Enabled: {sync_enabled}")
        self.stdout.write(f"Successfully Synced: {synced_users}")
        self.stdout.write(f"Pending Sync: {pending_users}")
        self.stdout.write(f"Failed Sync: {failed_users}")
        
        if pending_users > 0:
            self.stdout.write(f"\n💡 To sync pending users, run:")
            self.stdout.write(f"   python manage.py sync_azure_ad --all-pending")
        
        if failed_users > 0:
            self.stdout.write(f"\n⚠️  To retry failed users:")
            failed_user_emails = User.objects.filter(
                azure_ad_sync_status='failed'
            ).values_list('email', flat=True)[:3]
            
            for email in failed_user_emails:
                self.stdout.write(f"   python manage.py sync_azure_ad --user {email} --force")