# Azure AD Admin Interface Guide

This guide explains how to manage Azure AD synchronization through the D.A.N.I admin panel.

## 🎯 **Features Added**

### **User Management**
- ✅ **Visual sync status** with colored indicators and icons
- ✅ **Error details** shown in tooltips for failed syncs
- ✅ **Azure AD Object ID** displayed when available
- ✅ **Comprehensive admin actions** for sync management

### **Admin Actions Available**

#### **🔄 Sync Operations**
1. **Sync selected users to Azure AD** - Standard sync for enabled users
2. **Force sync selected users** - Ignores current status, forces sync
3. **Reset sync status to pending** - Resets failed/disabled users to pending

#### **⚙️ Status Management**
4. **Enable Azure AD sync** - Enables sync for selected users
5. **Disable Azure AD sync** - Disables sync for selected users  
6. **Remove Azure AD Object ID** - Unlinks users from Azure AD

#### **🧪 Testing**
7. **Test Azure AD connection** - Tests the API connection

## 🖥️ **How to Use the Interface**

### **Access the Admin Panel**
1. Go to: http://localhost:8000/admin/
2. Login with admin credentials
3. Click on **"Users"** under Accounts section

### **View Sync Status**
The **Azure AD Status** column shows:
- ✅ **Synced** (Green) - User successfully synced
- ⏳ **Pending** (Orange) - Queued for sync
- ❌ **Failed** (Red) - Sync failed (hover for error details)
- 🚫 **Disabled** (Gray) - Sync disabled for user

### **Sync Users to Azure AD**

#### **Method 1: Standard Sync**
1. Select users in the user list
2. Choose **"🔄 Sync selected users to Azure AD"** from Actions dropdown
3. Click **"Go"**
4. View results in the success/error messages

#### **Method 2: Force Sync**
1. Select users (including already synced or failed users)
2. Choose **"🔄 Force sync selected users"** from Actions dropdown
3. Click **"Go"**
4. This will sync users regardless of current status

### **Handle Failed Syncs**

#### **View Error Details**
1. Look for users with ❌ **Failed** status
2. **Hover over the status** to see the error message
3. Or **click on the user** to see detailed error in the Azure AD section

#### **Fix Common Issues**
1. **Empty Job Title Error**:
   - Edit the user
   - Add a job title (1-128 characters)
   - Use "Reset sync status to pending" action
   - Then sync again

2. **Authentication Errors**:
   - Go to **Azure AD Settings**
   - Use **"Test Azure AD connection"** action
   - Fix credentials if test fails

#### **Retry Failed Syncs**
1. Select failed users
2. Choose **"🔄 Reset sync status to pending"** 
3. Then use **"🔄 Sync selected users to Azure AD"**

### **Manage Sync Settings**

#### **Enable/Disable Sync for Specific Users**
1. Select users
2. Use **"✅ Enable Azure AD sync"** or **"❌ Disable Azure AD sync"**

#### **Unlink Users from Azure AD**
1. Select users 
2. Use **"🗑️ Remove Azure AD Object ID"**
3. This removes the link but doesn't delete from Azure AD
4. User will be treated as new on next sync

## 🔧 **Azure AD Settings Management**

### **Configure Azure AD**
1. Go to **Azure AD Settings** in admin
2. Fill in:
   - **Tenant ID** (from Azure Portal)
   - **Client ID** (from App Registration) 
   - **Client Secret** (from App Registration)
3. Enable **"Enabled"** and **"Sync enabled"**
4. Save settings

### **Test Connection**
1. In Azure AD Settings list view
2. Select the settings record
3. Choose **"Test Azure AD connection"** action
4. Check the results in messages

### **Monitor Connection Status**
The settings show:
- **Connection Status**: Connected/Failed/Testing/Unknown
- **Last Test Date**: When connection was last tested
- **Test Error Message**: Details if connection failed

## 📊 **Understanding Sync Status**

### **Status Meanings**
- **Pending**: User queued for sync, hasn't been processed yet
- **Synced**: User successfully created/updated in Azure AD
- **Failed**: Sync attempt failed (check error details)
- **Disabled**: Azure AD sync is disabled for this user

### **When Automatic Sync Occurs**
If enabled in Azure AD Settings:
- **User Create**: New users are automatically synced
- **User Update**: Changes to synced users are pushed to Azure AD
- **User Disable**: Deactivated users are disabled in Azure AD

## 🚨 **Troubleshooting**

### **Common Error Messages**

#### **"Invalid value specified for property 'jobTitle'"**
- **Cause**: Job title is empty or too long
- **Fix**: Add/edit job title (1-128 characters), then retry sync

#### **"Authentication failed - check client ID and secret"**
- **Cause**: Wrong Azure AD credentials
- **Fix**: Verify credentials in Azure AD Settings, test connection

#### **"Access denied - check API permissions"**
- **Cause**: Missing API permissions in Azure AD
- **Fix**: Grant admin consent for required permissions

### **Manual Commands**
For advanced troubleshooting, you can use management commands:

```bash
# Test Azure AD connection
docker-compose exec web python manage.py test_azure_ad --verbose

# Sync specific user
docker-compose exec web python manage.py sync_azure_ad --user user@domain.com --force

# Sync all pending users
docker-compose exec web python manage.py sync_azure_ad --all-pending
```

## 📋 **Best Practices**

### **Before Syncing Users**
1. ✅ Test Azure AD connection first
2. ✅ Ensure users have valid job titles
3. ✅ Verify email domains match your Azure AD tenant
4. ✅ Start with a few test users

### **Regular Maintenance**
1. 🔄 Monitor sync status regularly
2. 🔍 Check for failed syncs and resolve issues
3. 🧪 Test connection periodically
4. 📝 Keep Azure AD credentials updated

### **Production Deployment**
1. 🔒 Use strong, non-default passwords for temporary passwords
2. 🔐 Store Azure AD credentials securely
3. 📊 Monitor sync performance and errors
4. 🔄 Set up automated backup of user data

---

**The Azure AD interface gives you complete control over user synchronization directly from the admin panel, with detailed error reporting and troubleshooting capabilities.** 🎯