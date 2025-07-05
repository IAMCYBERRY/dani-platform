# Azure AD Admin Interface Guide

This guide explains how to use the comprehensive Azure AD management features available in the Django admin interface.

## Overview

The enhanced admin interface provides complete Azure AD sync management without requiring command-line access. All Azure AD operations can be performed directly from the web-based admin panel.

## Features

### Visual Status Indicators

In the user list, you'll see color-coded status indicators:

- ✅ **Green "Synced"** - User is successfully synchronized
- ⏳ **Orange "Pending"** - User is queued for synchronization  
- ❌ **Red "Failed"** - Synchronization failed (hover over ⚠️ for error details)
- 🚫 **Gray "Disabled"** - Sync is disabled for this user

### Available Admin Actions

Select users and choose from these actions:

#### 1. 🔄 Sync selected users to Azure AD
- Syncs users who have sync enabled
- Respects individual user sync settings
- Creates new users or updates existing ones

#### 2. ⚡ Force sync selected users to Azure AD  
- Forces sync regardless of user sync settings
- Useful for troubleshooting or emergency syncs
- Overrides disabled sync settings

#### 3. ⏳ Reset sync status to pending
- Changes status back to "pending"
- Clears any previous error messages
- Prepares users for fresh sync attempt

#### 4. ✅ Enable Azure AD sync
- Enables sync for selected users
- Sets status to "pending"
- Users will be synced on next sync operation

#### 5. 🚫 Disable Azure AD sync
- Disables sync for selected users
- Sets status to "disabled"
- Users will be skipped in future sync operations

#### 6. 🔗 Remove Azure AD link
- Removes the Azure AD Object ID link
- Does NOT delete the user from Azure AD
- User remains in Azure AD but is no longer linked

#### 7. 🔧 Test Azure AD connection
- Tests connectivity to Microsoft Graph API
- Validates configuration settings
- Shows success/error messages

## User Details View

When editing individual users, the "Azure AD Integration" section shows:

- **Azure AD Object ID**: Unique identifier in Azure AD (read-only)
- **Azure AD Sync Enabled**: Whether sync is enabled for this user
- **Azure AD Sync Status**: Current sync status
- **Azure AD Last Sync**: Timestamp of last successful sync
- **Azure AD Sync Error**: Details of last sync error (if any)

## Error Troubleshooting

### Common Error Messages

1. **"jobTitle must be 1-128 characters"**
   - Fixed automatically - job titles are now validated and truncated

2. **"Failed to connect to Microsoft Graph API"**
   - Check Azure AD Settings configuration
   - Use "Test Azure AD connection" action to diagnose

3. **"User already exists in Azure AD"**
   - User has an Azure AD account but no Object ID stored locally
   - Use "Force sync" to resolve linking

### Sync Status Meanings

- **Pending**: User is queued for next sync operation
- **Synced**: User is successfully synchronized with Azure AD
- **Failed**: Last sync attempt failed (check error field for details)
- **Disabled**: Sync is disabled for this user

## Best Practices

### Regular Operations

1. **Weekly Sync Review**: Check for users with "Failed" status
2. **New User Setup**: Enable sync for new employees
3. **Departing Users**: Disable sync instead of deleting (preserves audit trail)

### Troubleshooting Workflow

1. Use "Test Azure AD connection" to verify configuration
2. Check failed users' error messages
3. Use "Reset sync status to pending" to retry failed syncs
4. Use "Force sync" for persistent issues

### Bulk Operations

- Select multiple users for batch operations
- Use filters to find specific user groups
- Always test with a small group first

## Azure AD Settings

Configure Azure AD integration in the "Azure AD Settings" section:

### Basic Configuration
- **Enabled**: Master switch for Azure AD integration
- **Tenant ID**: Your Azure AD Directory ID
- **Client ID**: Application (Client) ID from Azure AD
- **Client Secret**: Client secret from Azure AD app registration

### Sync Settings
- **Sync Enabled**: Master switch for automatic synchronization
- **Sync on User Create**: Auto-sync when creating new users
- **Sync on User Update**: Auto-sync when updating user details
- **Sync on User Disable**: Auto-sync when deactivating users

### Connection Testing
- **Connection Status**: Last test result
- **Last Test Date**: When connection was last tested
- **Test Error Message**: Details of connection failures

## Security Notes

- Only admin users can access Azure AD management features
- All sync operations are logged
- Sensitive configuration data is encrypted
- Failed operations don't expose credentials in error messages

## Getting Help

If you encounter issues:

1. Check the error message in the user's "Azure AD Sync Error" field
2. Use the "Test Azure AD connection" action
3. Review the Django logs for detailed error information
4. Verify your Azure AD app registration permissions

## CLI Alternatives

For advanced users, command-line tools are available:

```bash
# Test connection
python manage.py test_azure_ad

# Sync specific user
python manage.py sync_azure_ad --user email@domain.com

# Sync all pending users
python manage.py sync_azure_ad --all-pending

# Dry run (show what would be synced)
python manage.py sync_azure_ad --all-pending --dry-run
```