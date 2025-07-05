# Azure AD Connection Troubleshooting Guide

This guide helps resolve common Azure AD integration issues with D.A.N.I.

## 🔍 Quick Diagnosis

### Test Your Connection
```bash
# Test Azure AD connection
docker-compose exec web python manage.py test_azure_ad --verbose

# Update connection status in database
docker-compose exec web python manage.py test_azure_ad --update-status
```

## 🚨 Common Error Messages

### "Failed to connect to Microsoft Graph API"

**Possible Causes:**
1. **Invalid credentials** - Wrong Tenant ID, Client ID, or Client Secret
2. **Missing permissions** - App registration lacks required API permissions
3. **No admin consent** - Permissions not granted for organization
4. **Expired secret** - Client secret has expired

### "Authentication failed - check client ID and secret"

**Solutions:**
1. Verify Client ID and Secret in Azure Portal
2. Check if Client Secret has expired
3. Ensure you're using the correct Tenant ID

### "Access denied - check API permissions"

**Required Permissions:**
- `Organization.Read.All` (for connection testing)
- `User.ReadWrite.All` (for user synchronization)
- `Directory.ReadWrite.All` (for full directory access)

**How to Grant:**
1. Go to Azure Portal → App registrations → Your app
2. Click "API permissions" → "Add permission"
3. Select "Microsoft Graph" → "Application permissions"
4. Add the required permissions
5. Click "Grant admin consent for [Your Organization]"

## 🛠️ Step-by-Step Fix

### 1. Verify Azure AD App Registration

```bash
# Check current settings
docker-compose exec web python manage.py shell -c "
from accounts.models import AzureADSettings
settings = AzureADSettings.get_settings()
print(f'Enabled: {settings.enabled}')
print(f'Tenant ID: {settings.tenant_id[:8] if settings.tenant_id else \"Not set\"}...')
print(f'Client ID: {settings.client_id[:8] if settings.client_id else \"Not set\"}...')
print(f'Secret: {\"Set\" if settings.client_secret else \"Not set\"}')
"
```

### 2. Update Configuration via Admin Panel

1. Access admin panel: `http://your-ip:8000/admin/`
2. Go to "Azure AD Settings"
3. Configure:
   - **Enabled**: ✅ Check this
   - **Tenant ID**: Your Azure AD Directory (tenant) ID
   - **Client ID**: Your app registration Application (client) ID
   - **Client Secret**: Your app's client secret value
   - **Sync Enabled**: ✅ Check this for user synchronization

### 3. Test Configuration via Django Shell

```bash
docker-compose exec web python manage.py shell
```

```python
from accounts.azure_ad_service import azure_ad_service

# Test connection
success, result = azure_ad_service.test_connection()
print(f"Success: {success}")
print(f"Result: {result}")

# If successful, test token acquisition
if success:
    token = azure_ad_service._get_access_token()
    print(f"Token acquired: {'Yes' if token else 'No'}")
```

## 🔧 Azure Portal Configuration

### Create New App Registration

1. **Go to Azure Portal**: https://portal.azure.com
2. **Navigate**: Azure Active Directory → App registrations → New registration
3. **Configure**:
   - **Name**: `D.A.N.I HRIS Integration`
   - **Account types**: "Accounts in this organizational directory only"
   - **Redirect URI**: Leave blank
4. **Click**: Register

### Configure API Permissions

1. **In your app**: API permissions → Add permission
2. **Microsoft Graph**: Application permissions
3. **Add these permissions**:
   ```
   Organization.Read.All
   User.ReadWrite.All
   Directory.ReadWrite.All
   Group.ReadWrite.All (optional)
   ```
4. **Grant admin consent**: Click "Grant admin consent for [Organization]"

### Create Client Secret

1. **Certificates & secrets** → New client secret
2. **Description**: `D.A.N.I Integration Secret`
3. **Expires**: 12-24 months
4. **Copy the secret value immediately** (you won't see it again!)

### Copy Required Information

From the **Overview** tab, copy:
- **Directory (tenant) ID**
- **Application (client) ID**
- **Client secret value** (from previous step)

## 🧪 Testing Scenarios

### Test 1: Basic Configuration
```bash
docker-compose exec web python manage.py test_azure_ad
```

### Test 2: Detailed Diagnostics
```bash
docker-compose exec web python manage.py test_azure_ad --verbose --update-status
```

### Test 3: Manual Token Test
```bash
docker-compose exec web python manage.py shell -c "
from accounts.azure_ad_service import azure_ad_service
token = azure_ad_service._get_access_token()
print('Token acquired!' if token else 'Token acquisition failed')
"
```

## 🔄 Common Fixes

### Fix 1: Update Expired Client Secret
1. Azure Portal → Your app → Certificates & secrets
2. Create new client secret
3. Update in D.A.N.I admin panel

### Fix 2: Re-grant Admin Consent
1. Azure Portal → Your app → API permissions
2. Click "Grant admin consent for [Organization]"
3. Test connection again

### Fix 3: Verify Tenant ID
```bash
# Get your tenant ID
curl -s "https://login.microsoftonline.com/YOUR_DOMAIN/.well-known/openid_configuration" | grep "tenant"
```

### Fix 4: Reset Configuration
```bash
docker-compose exec web python manage.py shell -c "
from accounts.models import AzureADSettings
settings = AzureADSettings.get_settings()
settings.connection_status = 'unknown'
settings.test_error_message = ''
settings.save()
print('Configuration reset')
"
```

## 📊 Monitoring Azure AD Health

### Check Connection Status
```bash
docker-compose exec web python manage.py shell -c "
from accounts.models import AzureADSettings
settings = AzureADSettings.get_settings()
print(f'Status: {settings.connection_status}')
print(f'Last Test: {settings.last_test_date}')
print(f'Error: {settings.test_error_message}')
"
```

### Automated Testing (Optional)
Add to your monitoring:
```bash
# Add to crontab for periodic testing
0 */6 * * * cd /path/to/dani && docker-compose exec -T web python manage.py test_azure_ad --update-status
```

## 🆘 Still Having Issues?

1. **Check Azure AD logs**: Azure Portal → Azure Active Directory → Sign-in logs
2. **Verify network connectivity**: Ensure VM can reach `https://graph.microsoft.com`
3. **Check application logs**: `docker-compose logs web | grep azure`
4. **Try with different permissions**: Start with minimal permissions and add incrementally

## 📞 Support Resources

- **Azure AD Documentation**: https://docs.microsoft.com/en-us/azure/active-directory/
- **Microsoft Graph API**: https://docs.microsoft.com/en-us/graph/
- **D.A.N.I Issues**: https://github.com/IAMCYBERRY/dani-platform/issues