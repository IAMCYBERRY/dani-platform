"""
Comprehensive Azure AD admin actions for the Django admin interface.

This module provides a full suite of admin actions for managing Azure AD synchronization
directly from the Django admin panel, eliminating the need for command-line operations.
"""

from django.contrib import messages
from django.utils import timezone
from .azure_ad_service import azure_ad_service


def sync_users_to_azure_ad(modeladmin, request, queryset):
    """Sync selected users to Azure AD (respects individual sync settings)."""
    synced_count = 0
    failed_count = 0
    
    for user in queryset:
        if user.azure_ad_sync_enabled:
            success, result = azure_ad_service.sync_user_from_hris(user)
            if success:
                synced_count += 1
            else:
                failed_count += 1
    
    if synced_count > 0:
        messages.success(request, f"Successfully synced {synced_count} user(s) to Azure AD.")
    if failed_count > 0:
        messages.error(request, f"Failed to sync {failed_count} user(s). Check individual user sync status for details.")

sync_users_to_azure_ad.short_description = "🔄 Sync selected users to Azure AD"


def force_sync_users_to_azure_ad(modeladmin, request, queryset):
    """Force sync selected users to Azure AD (ignores individual sync settings)."""
    synced_count = 0
    failed_count = 0
    
    for user in queryset:
        success, result = azure_ad_service.sync_user_from_hris(user, force_create=True)
        if success:
            synced_count += 1
        else:
            failed_count += 1
    
    if synced_count > 0:
        messages.success(request, f"Successfully force-synced {synced_count} user(s) to Azure AD.")
    if failed_count > 0:
        messages.error(request, f"Failed to force-sync {failed_count} user(s). Check individual user sync status for details.")

force_sync_users_to_azure_ad.short_description = "⚡ Force sync selected users to Azure AD"


def reset_sync_status_to_pending(modeladmin, request, queryset):
    """Reset Azure AD sync status to pending for selected users."""
    updated = queryset.update(
        azure_ad_sync_status='pending',
        azure_ad_sync_error=''
    )
    messages.success(request, f"Reset sync status to pending for {updated} user(s).")

reset_sync_status_to_pending.short_description = "⏳ Reset sync status to pending"


def disable_azure_ad_sync(modeladmin, request, queryset):
    """Disable Azure AD sync for selected users."""
    updated = queryset.update(
        azure_ad_sync_enabled=False,
        azure_ad_sync_status='disabled'
    )
    messages.success(request, f"Disabled Azure AD sync for {updated} user(s).")

disable_azure_ad_sync.short_description = "🚫 Disable Azure AD sync"


def enable_azure_ad_sync(modeladmin, request, queryset):
    """Enable Azure AD sync for selected users."""
    updated = queryset.update(
        azure_ad_sync_enabled=True,
        azure_ad_sync_status='pending'
    )
    messages.success(request, f"Enabled Azure AD sync for {updated} user(s).")

enable_azure_ad_sync.short_description = "✅ Enable Azure AD sync"


def remove_azure_ad_link(modeladmin, request, queryset):
    """Remove Azure AD link for selected users (does not delete from Azure AD)."""
    updated = queryset.update(
        azure_ad_object_id=None,
        azure_ad_sync_status='disabled',
        azure_ad_sync_error=''
    )
    messages.warning(request, f"Removed Azure AD link for {updated} user(s). Users still exist in Azure AD but are no longer linked.")

remove_azure_ad_link.short_description = "🔗 Remove Azure AD link"


def test_azure_ad_connection(modeladmin, request, queryset):
    """Test Azure AD connection."""
    success, result = azure_ad_service.test_connection()
    
    if success:
        messages.success(request, "✅ Azure AD connection test successful!")
    else:
        error_msg = result.get('error', 'Unknown error')
        messages.error(request, f"❌ Azure AD connection test failed: {error_msg}")

test_azure_ad_connection.short_description = "🔧 Test Azure AD connection"