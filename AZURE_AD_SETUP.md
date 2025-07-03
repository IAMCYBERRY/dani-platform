# Azure AD / Microsoft Entra Integration Setup for D.A.N.I

This guide explains how to set up the Microsoft Graph API integration to sync users between your D.A.N.I platform (Domain Access & Navigation Interface) and Azure AD (Microsoft Entra).

## Overview

The Azure AD integration provides:
- **Bidirectional user sync**: Create/update users in Azure AD when created/modified in HRIS
- **Automatic password generation**: Secure temporary passwords for new Azure AD users
- **Background processing**: All sync operations happen asynchronously via Celery tasks
- **Comprehensive tracking**: Detailed sync status and error handling
- **Admin controls**: Enable/disable sync per user and bulk operations

## Prerequisites

1. **Azure AD tenant** with administrative access
2. **App registration** in Azure AD with Microsoft Graph API permissions
3. **Client credentials** (Tenant ID, Client ID, Client Secret)

## Step 1: Azure AD App Registration

### 1.1 Create App Registration

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **New registration**
4. Configure:
   - **Name**: `D.A.N.I Platform Integration`
   - **Supported account types**: Accounts in this organizational directory only
   - **Redirect URI**: Leave blank for now
5. Click **Register**

### 1.2 Configure API Permissions

1. In your app registration, go to **API permissions**
2. Click **Add a permission** → **Microsoft Graph** → **Application permissions**
3. Add the following permissions:
   ```
   User.ReadWrite.All          # Create, read, update users
   User.ManageIdentities.All   # Manage user identities
   Directory.ReadWrite.All     # Read/write directory data
   Group.ReadWrite.All         # Manage group memberships (optional)
   ```
4. Click **Grant admin consent** for your tenant

### 1.3 Create Client Secret

1. Go to **Certificates & secrets**
2. Click **New client secret**
3. Configure:
   - **Description**: `D.A.N.I Platform Secret`
   - **Expires**: Choose appropriate duration (recommend 12-24 months)
4. **Copy the secret value immediately** - you won't see it again!

### 1.4 Note Required Information

Copy these values from your app registration:
- **Tenant ID** (Directory ID): Found in **Overview** tab
- **Client ID** (Application ID): Found in **Overview** tab  
- **Client Secret**: The value you just created

## Step 2: Configure D.A.N.I Platform

### 2.1 Environment Variables

Add these variables to your `.env` file:

```bash
# Azure AD Configuration
AZURE_AD_ENABLED=true
AZURE_AD_TENANT_ID=your-tenant-id-here
AZURE_AD_CLIENT_ID=your-client-id-here
AZURE_AD_CLIENT_SECRET=your-client-secret-here

# Optional: Customize these settings
AZURE_AD_AUTHORITY=https://login.microsoftonline.com/
AZURE_AD_SCOPE=https://graph.microsoft.com/.default
GRAPH_API_VERSION=v1.0

# Sync Behavior
AZURE_AD_SYNC_ENABLED=true
AZURE_AD_SYNC_ON_USER_CREATE=true
AZURE_AD_SYNC_ON_USER_UPDATE=true
AZURE_AD_SYNC_ON_USER_DISABLE=true
AZURE_AD_DEFAULT_PASSWORD_LENGTH=12
```

### 2.2 Docker Environment

Update your `docker-compose.yml` to include the Azure AD environment variables:

```yaml
services:
  web:
    environment:
      # ... existing environment variables ...
      - AZURE_AD_ENABLED=${AZURE_AD_ENABLED}
      - AZURE_AD_TENANT_ID=${AZURE_AD_TENANT_ID}
      - AZURE_AD_CLIENT_ID=${AZURE_AD_CLIENT_ID}
      - AZURE_AD_CLIENT_SECRET=${AZURE_AD_CLIENT_SECRET}
      - AZURE_AD_SYNC_ENABLED=${AZURE_AD_SYNC_ENABLED}
      - AZURE_AD_SYNC_ON_USER_CREATE=${AZURE_AD_SYNC_ON_USER_CREATE}
      - AZURE_AD_SYNC_ON_USER_UPDATE=${AZURE_AD_SYNC_ON_USER_UPDATE}
      - AZURE_AD_SYNC_ON_USER_DISABLE=${AZURE_AD_SYNC_ON_USER_DISABLE}
```

### 2.3 Install Dependencies

Rebuild your Docker containers to include the new Microsoft Graph dependencies:

```bash
docker-compose down
docker-compose build
docker-compose up -d
```

### 2.4 Run Database Migrations

Create and apply migrations for the new Azure AD fields:

```bash
docker-compose exec web python manage.py makemigrations accounts employees
docker-compose exec web python manage.py migrate
```

## Step 3: Test the Integration

### 3.1 Test API Connection

Use the test endpoint to verify connectivity:

```bash
curl -X GET http://localhost:8000/api/accounts/azure-ad/test/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3.2 View Sync Dashboard

Check the sync status dashboard:

```bash
curl -X GET http://localhost:8000/api/accounts/azure-ad/dashboard/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3.3 Test User Sync

Sync a specific user to Azure AD:

```bash
curl -X POST http://localhost:8000/api/accounts/azure-ad/sync/user/1/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "create"}'
```

## Step 4: User Management Workflows

### 4.1 Creating Users

When you create users in the HRIS admin panel:
1. User is created in the local database
2. If `AZURE_AD_SYNC_ON_USER_CREATE=true`, a Celery task is automatically queued
3. The task creates the user in Azure AD with a temporary password
4. User gets an `azure_ad_object_id` and sync status is updated

### 4.2 Updating Users

When user information is updated:
1. Changes are saved to the local database
2. If `AZURE_AD_SYNC_ON_USER_UPDATE=true`, an update task is queued
3. User information is synchronized to Azure AD

### 4.3 Disabling Users

When users are deactivated:
1. User is marked as inactive locally
2. If `AZURE_AD_SYNC_ON_USER_DISABLE=true`, the Azure AD account is disabled
3. The user cannot sign in to Azure AD services

## Step 5: API Endpoints

### User Sync Operations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/accounts/azure-ad/sync/user/{id}/` | POST | Sync specific user |
| `/api/accounts/azure-ad/sync/bulk/` | POST | Bulk sync multiple users |
| `/api/accounts/azure-ad/sync/retry-failed/` | POST | Retry failed syncs |
| `/api/accounts/azure-ad/user/{id}/status/` | GET | Get user sync status |
| `/api/accounts/azure-ad/user/{id}/toggle/` | POST | Enable/disable sync for user |

### Monitoring & Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/accounts/azure-ad/dashboard/` | GET | Sync statistics dashboard |
| `/api/accounts/azure-ad/test/` | GET | Test API connection |

### Example API Calls

**Sync a user:**
```bash
curl -X POST http://localhost:8000/api/accounts/azure-ad/sync/user/1/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "create",
    "force": false
  }'
```

**Bulk sync users:**
```bash
curl -X POST http://localhost:8000/api/accounts/azure-ad/sync/bulk/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_ids": [1, 2, 3],
    "action": "create"
  }'
```

**Check sync dashboard:**
```bash
curl -X GET http://localhost:8000/api/accounts/azure-ad/dashboard/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Step 6: Admin Panel Integration

### 6.1 User List View

In the Django admin panel (`/admin/accounts/user/`):
- New columns show Azure AD sync status
- Filter users by sync status and Azure AD sync enabled/disabled
- Search includes Azure AD Object ID

### 6.2 User Edit View

When editing a user:
- New "Azure AD Integration" section shows:
  - Azure AD Object ID (read-only)
  - Sync enabled/disabled toggle
  - Current sync status
  - Last successful sync timestamp

### 6.3 Bulk Actions

Select multiple users and use these actions:
- **Sync selected users to Azure AD**: Queues sync tasks
- **Disable Azure AD sync**: Turns off sync for selected users
- **Enable Azure AD sync**: Turns on sync for selected users

## Step 7: Monitoring and Troubleshooting

### 7.1 Check Celery Logs

Monitor sync task execution:

```bash
# View Celery worker logs
docker-compose logs -f celery

# Check task status in Django shell
docker-compose exec web python manage.py shell
>>> from accounts.models import User
>>> user = User.objects.get(id=1)
>>> print(f"Sync Status: {user.azure_ad_sync_status}")
>>> print(f"Last Sync: {user.azure_ad_last_sync}")
```

### 7.2 Common Issues

**Authentication Errors:**
- Verify tenant ID, client ID, and client secret
- Ensure admin consent was granted for API permissions
- Check that the client secret hasn't expired

**Permission Errors:**
- Verify Microsoft Graph API permissions are granted
- Ensure `User.ReadWrite.All` permission is present
- Check that admin consent was properly granted

**Sync Failures:**
- Check user email format (must be valid email)
- Verify required fields are present (first_name, last_name)
- Check Azure AD password policy compliance

### 7.3 Reset Sync Status

If you need to reset sync statuses:

```bash
docker-compose exec web python manage.py shell
>>> from accounts.models import User
>>> # Reset all failed syncs to pending
>>> User.objects.filter(azure_ad_sync_status='failed').update(azure_ad_sync_status='pending')
```

## Step 8: Production Considerations

### 8.1 Security

- Store client secret securely (use Azure Key Vault in production)
- Rotate client secrets regularly
- Monitor API usage and set up alerts
- Use Azure AD Conditional Access policies

### 8.2 Scalability

- Configure Celery with appropriate worker counts
- Monitor task queue length
- Set up Redis persistence for task queues
- Configure task retry policies

### 8.3 Compliance

- Document data flows for compliance requirements
- Set up audit logging for sync operations
- Configure data retention policies
- Review Azure AD audit logs regularly

## Troubleshooting Guide

### Issue: "Failed to acquire access token"
**Solution:**
1. Verify `AZURE_AD_TENANT_ID`, `AZURE_AD_CLIENT_ID`, and `AZURE_AD_CLIENT_SECRET`
2. Check that the client secret hasn't expired
3. Ensure the app registration has the correct permissions

### Issue: "User already exists in Azure AD"
**Solution:**
1. Check if the user already has an `azure_ad_object_id`
2. Use the "update" action instead of "create"
3. Use the bulk sync with appropriate action

### Issue: "Sync stuck in pending status"
**Solution:**
1. Check Celery worker logs for errors
2. Restart Celery workers: `docker-compose restart celery`
3. Use the cleanup task to reset stuck statuses

### Issue: "Permission denied" API errors
**Solution:**
1. Verify your JWT token is valid
2. Check user role permissions (Admin/HR Manager required)
3. Ensure API endpoints are properly configured

For additional support, check the application logs and Celery task results for detailed error messages.