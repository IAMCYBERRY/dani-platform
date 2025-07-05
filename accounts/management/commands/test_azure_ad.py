"""
Django management command for testing Azure AD connectivity.

Usage:
    python manage.py test_azure_ad
"""

from django.core.management.base import BaseCommand
from accounts.azure_ad_service import azure_ad_service
from accounts.models import AzureADSettings


class Command(BaseCommand):
    help = 'Test Azure AD connection and display configuration status'

    def handle(self, *args, **options):
        self.stdout.write('🔧 Testing Azure AD Connection...\n')
        
        # Check configuration
        settings = AzureADSettings.get_settings()
        
        self.stdout.write('📋 Configuration Status:')
        self.stdout.write(f'  - Enabled: {settings.enabled}')
        self.stdout.write(f'  - Sync Enabled: {settings.sync_enabled}')
        self.stdout.write(f'  - Configured: {settings.is_configured}')
        self.stdout.write(f'  - Tenant ID: {"✅ Set" if settings.tenant_id else "❌ Missing"}')
        self.stdout.write(f'  - Client ID: {"✅ Set" if settings.client_id else "❌ Missing"}')
        self.stdout.write(f'  - Client Secret: {"✅ Set" if settings.client_secret else "❌ Missing"}')
        self.stdout.write('')
        
        if not settings.is_configured:
            self.stdout.write(
                self.style.ERROR('❌ Azure AD is not properly configured. Please check your settings.')
            )
            return
        
        # Test connection
        self.stdout.write('🔍 Testing connection to Microsoft Graph API...')
        success, result = azure_ad_service.test_connection()
        
        if success:
            self.stdout.write(
                self.style.SUCCESS('✅ Connection successful!')
            )
            self.stdout.write('📊 Organization Info:')
            if 'organization_info' in result and result['organization_info'].get('value'):
                org = result['organization_info']['value'][0]
                self.stdout.write(f'  - Name: {org.get("displayName", "N/A")}')
                self.stdout.write(f'  - Domain: {org.get("verifiedDomains", [{}])[0].get("name", "N/A")}')
                self.stdout.write(f'  - Country: {org.get("countryLetterCode", "N/A")}')
        else:
            self.stdout.write(
                self.style.ERROR('❌ Connection failed!')
            )
            error_details = result.get('details', {})
            if isinstance(error_details, dict):
                if 'error' in error_details:
                    self.stdout.write(f'Error: {error_details["error"]}')
                if 'details' in error_details:
                    self.stdout.write(f'Details: {error_details["details"]}')
            else:
                self.stdout.write(f'Error: {error_details}')
            
            self.stdout.write('\n🛠️  Troubleshooting Tips:')
            self.stdout.write('1. Verify your Tenant ID, Client ID, and Client Secret')
            self.stdout.write('2. Ensure the application has proper permissions in Azure AD')
            self.stdout.write('3. Check that the application secret has not expired')
            self.stdout.write('4. Verify network connectivity to Microsoft Graph API')