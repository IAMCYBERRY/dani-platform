"""
Azure AD admin actions for the Django admin interface.
"""

from django.contrib import messages
from django.contrib.admin import action
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from accounts.azure_ad_service import azure_ad_service
from accounts.models import AzureADSettings, User


@action(description="🔄 Sync selected users to Azure AD")
def sync_users_to_azure_ad(modeladmin, request, queryset):
    """Sync selected users to Azure AD."""
    
    # Check if Azure AD is configured
    settings = AzureADSettings.get_settings()
    if not settings.is_configured:
        messages.error(request, "❌ Azure AD is not configured. Please configure Azure AD settings first.")
        return
    
    if not settings.enabled or not settings.sync_enabled:
        messages.error(request, "❌ Azure AD sync is disabled. Please enable it in Azure AD settings.")
        return
    
    success_count = 0
    error_count = 0
    results = []
    
    for user in queryset:
        if not user.azure_ad_sync_enabled:
            results.append(f"⏭️  {user.email}: Sync disabled for user")
            continue
            
        # Attempt to sync
        success, result = azure_ad_service.sync_user_from_hris(user, force_create=True)
        
        if success:
            success_count += 1
            temp_password = result.get('temporary_password', '')
            if temp_password:
                results.append(f"✅ {user.email}: Synced successfully (Temp password: {temp_password})")
            else:
                results.append(f"✅ {user.email}: Updated successfully")
        else:
            error_count += 1
            error_msg = result.get('error', 'Unknown error')
            results.append(f"❌ {user.email}: {error_msg}")
    
    # Show results
    if success_count > 0:
        messages.success(request, f"✅ Successfully synced {success_count} users to Azure AD")
    
    if error_count > 0:
        messages.error(request, f"❌ Failed to sync {error_count} users")
    
    # Show detailed results
    if results:
        detailed_message = "<br>".join(results)
        messages.info(request, mark_safe(f"<strong>Sync Results:</strong><br>{detailed_message}"))


@action(description="🔄 Force sync selected users (ignore current status)")
def force_sync_users_to_azure_ad(modeladmin, request, queryset):
    """Force sync selected users to Azure AD, ignoring current sync status."""
    
    settings = AzureADSettings.get_settings()
    if not settings.is_configured:
        messages.error(request, "❌ Azure AD is not configured.")
        return
    
    success_count = 0
    error_count = 0
    results = []
    
    for user in queryset:
        # Reset status to pending and enable sync
        user.azure_ad_sync_enabled = True
        user.azure_ad_sync_status = 'pending'
        user.save()
        
        # Attempt to sync
        success, result = azure_ad_service.sync_user_from_hris(user, force_create=True)
        
        if success:
            success_count += 1
            temp_password = result.get('temporary_password', '')
            if temp_password:
                results.append(f"✅ {user.email}: Force synced (Temp password: {temp_password})")
            else:
                results.append(f"✅ {user.email}: Force updated")
        else:
            error_count += 1
            error_msg = result.get('error', 'Unknown error')
            results.append(f"❌ {user.email}: {error_msg}")
    
    if success_count > 0:
        messages.success(request, f"✅ Force synced {success_count} users")
    
    if error_count > 0:
        messages.error(request, f"❌ Failed to force sync {error_count} users")
    
    if results:
        detailed_message = "<br>".join(results)
        messages.info(request, mark_safe(f"<strong>Force Sync Results:</strong><br>{detailed_message}"))


@action(description="🔄 Reset sync status to pending")
def reset_sync_status_to_pending(modeladmin, request, queryset):
    """Reset selected users' sync status to pending."""
    
    updated_count = queryset.update(
        azure_ad_sync_status='pending',
        azure_ad_sync_error='',
        azure_ad_sync_enabled=True
    )
    
    messages.success(request, f"✅ Reset {updated_count} users to pending sync status")


@action(description="❌ Disable Azure AD sync for selected users")
def disable_azure_ad_sync(modeladmin, request, queryset):
    """Disable Azure AD sync for selected users."""
    
    updated_count = queryset.update(
        azure_ad_sync_enabled=False,
        azure_ad_sync_status='disabled'
    )
    
    messages.success(request, f"✅ Disabled Azure AD sync for {updated_count} users")


@action(description="✅ Enable Azure AD sync for selected users")
def enable_azure_ad_sync(modeladmin, request, queryset):
    """Enable Azure AD sync for selected users."""
    
    updated_count = queryset.update(
        azure_ad_sync_enabled=True,
        azure_ad_sync_status='pending'
    )
    
    messages.success(request, f"✅ Enabled Azure AD sync for {updated_count} users")


@action(description="🗑️ Remove Azure AD Object ID (unlink from Azure AD)")
def remove_azure_ad_link(modeladmin, request, queryset):
    """Remove Azure AD Object ID from selected users (unlink them from Azure AD)."""
    
    updated_count = queryset.update(
        azure_ad_object_id=None,
        azure_ad_sync_status='pending',
        azure_ad_sync_error='',
        azure_ad_last_sync=None
    )
    
    messages.warning(request, f"⚠️  Unlinked {updated_count} users from Azure AD. They will be treated as new users on next sync.")


@action(description="🧪 Test Azure AD connection")
def test_azure_ad_connection(modeladmin, request, queryset):
    """Test the Azure AD connection."""
    
    success, result = azure_ad_service.test_connection()
    
    if success:
        messages.success(request, f"✅ Azure AD connection successful: {result.get('message', 'Connected')}")
    else:
        error_msg = result.get('error', 'Unknown error')
        details = result.get('details', '')
        messages.error(request, f"❌ Azure AD connection failed: {error_msg} - {details}")


@action(description="🔄 Sync ALL users to Azure AD")
def sync_all_users_to_azure_ad(modeladmin, request, queryset):
    """Sync ALL users in the system to Azure AD (not just selected ones)."""
    
    # Check if Azure AD is configured
    settings = AzureADSettings.get_settings()
    if not settings.is_configured:
        messages.error(request, "❌ Azure AD is not configured. Please configure Azure AD settings first.")
        return
    
    if not settings.enabled or not settings.sync_enabled:
        messages.error(request, "❌ Azure AD sync is disabled. Please enable it in Azure AD settings.")
        return
    
    # Get all users with sync enabled
    all_users = User.objects.filter(azure_ad_sync_enabled=True, is_active=True)
    total_users = all_users.count()
    
    if total_users == 0:
        messages.warning(request, "⚠️  No users found with Azure AD sync enabled.")
        return
    
    # Confirmation check - only process if less than 50 users for safety
    if total_users > 50:
        messages.error(request, f"❌ Too many users ({total_users}) for bulk sync. Please use selective sync for safety.")
        return
    
    success_count = 0
    error_count = 0
    
    messages.info(request, f"🔄 Starting sync of {total_users} users...")
    
    for user in all_users:
        # Attempt to sync
        success, result = azure_ad_service.sync_user_from_hris(user, force_create=True)
        
        if success:
            success_count += 1
        else:
            error_count += 1
    
    # Show summary results
    if success_count > 0:
        messages.success(request, f"✅ Successfully synced {success_count} of {total_users} users to Azure AD")
    
    if error_count > 0:
        messages.error(request, f"❌ Failed to sync {error_count} users")


@action(description="👤 Sync individual user now")
def sync_individual_user_now(modeladmin, request, queryset):
    """Immediate sync for individual users."""
    
    # Check if Azure AD is configured
    settings = AzureADSettings.get_settings()
    if not settings.is_configured:
        messages.error(request, "❌ Azure AD is not configured.")
        return
    
    if not settings.enabled or not settings.sync_enabled:
        messages.error(request, "❌ Azure AD sync is disabled.")
        return
    
    # Limit to single user for individual sync
    if queryset.count() > 1:
        messages.error(request, "❌ Please select only one user for individual sync.")
        return
    
    user = queryset.first()
    if not user.azure_ad_sync_enabled:
        messages.error(request, f"❌ Azure AD sync is disabled for {user.email}")
        return
    
    # Attempt to sync
    success, result = azure_ad_service.sync_user_from_hris(user, force_create=True)
    
    if success:
        temp_password = result.get('temporary_password', '')
        if temp_password:
            messages.success(request, f"✅ {user.email} synced successfully! Temporary password: {temp_password}")
        else:
            messages.success(request, f"✅ {user.email} updated successfully in Azure AD")
    else:
        error_msg = result.get('error', 'Unknown error')
        messages.error(request, f"❌ Failed to sync {user.email}: {error_msg}")