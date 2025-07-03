"""
Django admin configuration for accounts app.

This module configures the Django admin interface for user management.
Only included for development and emergency access.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from .models import User, UserSession, PasswordResetToken, AzureADSettings


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin interface for User model.
    """
    list_display = ['email', 'first_name', 'last_name', 'role', 'department', 'is_active', 'azure_ad_sync_status', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff', 'department', 'azure_ad_sync_status', 'azure_ad_sync_enabled', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name', 'department', 'azure_ad_object_id']
    ordering = ['email']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'phone_number', 'profile_picture')}),
        (_('Organization'), {'fields': ('role', 'department', 'job_title')}),
        (_('Azure AD Integration'), {
            'fields': ('azure_ad_object_id', 'azure_ad_sync_enabled', 'azure_ad_sync_status', 'azure_ad_last_sync'),
            'classes': ('collapse',)
        }),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login', 'azure_ad_object_id', 'azure_ad_last_sync']
    
    actions = ['sync_to_azure_ad', 'disable_azure_sync', 'enable_azure_sync']
    
    def sync_to_azure_ad(self, request, queryset):
        """Admin action to sync selected users to Azure AD."""
        from .tasks import sync_user_to_azure_ad
        
        synced_count = 0
        for user in queryset:
            if user.azure_ad_sync_enabled:
                action = 'update' if user.azure_ad_object_id else 'create'
                sync_user_to_azure_ad.delay(user.id, action)
                synced_count += 1
        
        self.message_user(request, f"Queued {synced_count} users for Azure AD sync.")
    sync_to_azure_ad.short_description = "Sync selected users to Azure AD"
    
    def disable_azure_sync(self, request, queryset):
        """Admin action to disable Azure AD sync for selected users."""
        updated = queryset.update(azure_ad_sync_enabled=False, azure_ad_sync_status='disabled')
        self.message_user(request, f"Disabled Azure AD sync for {updated} users.")
    disable_azure_sync.short_description = "Disable Azure AD sync"
    
    def enable_azure_sync(self, request, queryset):
        """Admin action to enable Azure AD sync for selected users."""
        updated = queryset.update(azure_ad_sync_enabled=True, azure_ad_sync_status='pending')
        self.message_user(request, f"Enabled Azure AD sync for {updated} users.")
    enable_azure_sync.short_description = "Enable Azure AD sync"


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """
    Admin interface for UserSession model.
    """
    list_display = ['user', 'ip_address', 'created_at', 'last_activity', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__email', 'ip_address']
    readonly_fields = ['user', 'session_key', 'ip_address', 'user_agent', 'created_at']
    ordering = ['-last_activity']


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """
    Admin interface for PasswordResetToken model.
    """
    list_display = ['user', 'created_at', 'expires_at', 'is_used']
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['user', 'token', 'created_at']
    ordering = ['-created_at']


@admin.register(AzureADSettings)
class AzureADSettingsAdmin(admin.ModelAdmin):
    """
    Admin interface for Azure AD Settings.
    """
    list_display = ['enabled', 'sync_enabled', 'connection_status', 'last_test_date', 'updated_at']
    readonly_fields = ['connection_status', 'last_test_date', 'test_error_message', 'created_at', 'updated_at', 'updated_by']
    
    fieldsets = (
        (_('Basic Configuration'), {
            'fields': ('enabled', 'tenant_id', 'client_id', 'client_secret'),
            'description': 'Basic Azure AD configuration. Get these values from your Azure AD app registration.'
        }),
        (_('Sync Settings'), {
            'fields': ('sync_enabled', 'sync_on_user_create', 'sync_on_user_update', 'sync_on_user_disable'),
            'description': 'Configure when users should be automatically synchronized to Azure AD.'
        }),
        (_('Advanced Settings'), {
            'fields': ('authority', 'scope', 'default_password_length'),
            'classes': ('collapse',),
            'description': 'Advanced settings. Only change these if you know what you\'re doing.'
        }),
        (_('Connection Status'), {
            'fields': ('connection_status', 'last_test_date', 'test_error_message'),
            'classes': ('collapse',),
            'description': 'Connection test results and status information.'
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at', 'updated_by'),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['test_connection']
    
    def test_connection(self, request, queryset):
        """Test the Azure AD connection."""
        from .azure_ad_service import azure_ad_service
        from django.utils import timezone
        
        for settings in queryset:
            try:
                settings.connection_status = 'testing'
                settings.save()
                
                success, result = azure_ad_service.test_connection()
                
                if success:
                    settings.connection_status = 'connected'
                    settings.test_error_message = ''
                    self.message_user(request, f"Azure AD connection test successful!", messages.SUCCESS)
                else:
                    settings.connection_status = 'failed'
                    settings.test_error_message = str(result.get('error', 'Unknown error'))
                    self.message_user(request, f"Azure AD connection test failed: {settings.test_error_message}", messages.ERROR)
                
                settings.last_test_date = timezone.now()
                settings.save()
                
            except Exception as e:
                settings.connection_status = 'failed'
                settings.test_error_message = str(e)
                settings.last_test_date = timezone.now()
                settings.save()
                
                self.message_user(request, f"Azure AD connection test failed: {str(e)}", messages.ERROR)
    
    test_connection.short_description = "Test Azure AD connection"
    
    def save_model(self, request, obj, form, change):
        """Save the model and track who made the changes."""
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
        
        if obj.enabled and obj.is_configured:
            self.message_user(
                request, 
                "Azure AD integration is now enabled. You can test the connection using the 'Test Azure AD connection' action.",
                messages.SUCCESS
            )
        elif obj.enabled and not obj.is_configured:
            self.message_user(
                request,
                "Azure AD is enabled but not fully configured. Please fill in all required fields (Tenant ID, Client ID, Client Secret).",
                messages.WARNING
            )
    
    def has_add_permission(self, request):
        """Only allow one Azure AD settings record."""
        return not AzureADSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Don't allow deletion of Azure AD settings."""
        return False