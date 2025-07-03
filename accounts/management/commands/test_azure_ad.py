"""
Management command to test Azure AD connection and troubleshoot issues.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.azure_ad_service import azure_ad_service
from accounts.models import AzureADSettings
import json


class Command(BaseCommand):
    help = 'Test Azure AD connection and display troubleshooting information'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Display detailed troubleshooting information',
        )
        parser.add_argument(
            '--update-status',
            action='store_true',
            help='Update the connection status in the database',
        )

    def handle(self, *args, **options):
        self.stdout.write("🔍 Testing Azure AD Connection...")
        self.stdout.write("=" * 50)
        
        # Get current settings
        settings = AzureADSettings.get_settings()
        
        # Display current configuration
        self.stdout.write(f"✅ Configuration Status:")
        self.stdout.write(f"   Enabled: {settings.enabled}")
        self.stdout.write(f"   Sync Enabled: {settings.sync_enabled}")
        self.stdout.write(f"   Tenant ID: {'Set' if settings.tenant_id else 'Not set'}")
        self.stdout.write(f"   Client ID: {'Set' if settings.client_id else 'Not set'}")
        self.stdout.write(f"   Client Secret: {'Set' if settings.client_secret else 'Not set'}")
        self.stdout.write(f"   Authority: {settings.authority}")
        self.stdout.write(f"   Scope: {settings.scope}")
        self.stdout.write("")
        
        if not settings.is_configured:
            self.stdout.write(self.style.ERROR("❌ Azure AD is not properly configured"))
            self.stdout.write("Please configure the following in the admin panel:")
            self.stdout.write("1. Go to admin → Azure AD Settings")
            self.stdout.write("2. Set Tenant ID, Client ID, and Client Secret")
            self.stdout.write("3. Enable Azure AD integration")
            return
        
        # Test the connection
        self.stdout.write("🔄 Testing connection to Microsoft Graph API...")
        success, result = azure_ad_service.test_connection()
        
        if success:
            self.stdout.write(self.style.SUCCESS("✅ Connection successful!"))
            self.stdout.write(f"Message: {result.get('message', 'Connected')}")
            
            if options['verbose']:
                tenant_info = result.get('tenant_info', {})
                if tenant_info:
                    self.stdout.write("\n📊 Tenant Information:")
                    self.stdout.write(f"   Name: {tenant_info.get('displayName', 'N/A')}")
                    self.stdout.write(f"   ID: {tenant_info.get('id', 'N/A')}")
                    self.stdout.write(f"   Country: {tenant_info.get('countryLetterCode', 'N/A')}")
            
            # Update status if requested
            if options['update_status']:
                settings.connection_status = 'connected'
                settings.last_test_date = timezone.now()
                settings.test_error_message = ''
                settings.save()
                self.stdout.write("✅ Updated connection status in database")
                
        else:
            self.stdout.write(self.style.ERROR("❌ Connection failed!"))
            self.stdout.write(f"Error: {result.get('error', 'Unknown error')}")
            self.stdout.write(f"Details: {result.get('details', 'No details available')}")
            
            if 'troubleshooting' in result:
                self.stdout.write("\n🔧 Troubleshooting Information:")
                troubleshooting = result['troubleshooting']
                for key, value in troubleshooting.items():
                    self.stdout.write(f"   {key.replace('_', ' ').title()}: {value}")
            
            # Common troubleshooting steps
            self.stdout.write("\n🛠️ Common Solutions:")
            self.stdout.write("1. Verify your Azure AD app registration:")
            self.stdout.write("   - Go to https://portal.azure.com")
            self.stdout.write("   - Navigate to Azure Active Directory → App registrations")
            self.stdout.write("   - Check your app's API permissions")
            self.stdout.write("")
            self.stdout.write("2. Required API Permissions:")
            self.stdout.write("   - Organization.Read.All (to test connection)")
            self.stdout.write("   - User.ReadWrite.All (to sync users)")
            self.stdout.write("   - Directory.ReadWrite.All (for full sync)")
            self.stdout.write("")
            self.stdout.write("3. Grant admin consent for your organization")
            self.stdout.write("4. Verify client secret hasn't expired")
            
            # Update status if requested
            if options['update_status']:
                settings.connection_status = 'failed'
                settings.last_test_date = timezone.now()
                settings.test_error_message = f"{result.get('error', '')}: {result.get('details', '')}"
                settings.save()
                self.stdout.write("✅ Updated connection status in database")
        
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("Test completed.")