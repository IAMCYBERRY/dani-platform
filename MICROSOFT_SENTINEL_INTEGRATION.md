# Microsoft Sentinel Integration for D.A.N.I

This guide explains how to integrate D.A.N.I (Domain Access & Navigation Interface) with Microsoft Sentinel for comprehensive security monitoring and threat detection.

## Overview

D.A.N.I can send security-relevant events and logs to Microsoft Sentinel for:
- **User authentication monitoring**
- **Azure AD sync activity tracking**
- **Failed login attempt detection**
- **Privilege escalation monitoring**
- **API access pattern analysis**
- **Suspicious activity detection**

## Prerequisites

- Microsoft Sentinel workspace configured
- Log Analytics workspace
- Azure Monitor permissions
- D.A.N.I platform deployed and running

## Integration Methods

### Method 1: Azure Monitor Agent (Recommended)

**Step 1: Configure Log Analytics Workspace**

1. Go to Azure Portal → Log Analytics workspaces
2. Create or select existing workspace
3. Note the Workspace ID and Primary Key

**Step 2: Configure D.A.N.I for Azure Monitor**

Add to your `.env` file:
```bash
# Microsoft Sentinel Integration
SENTINEL_ENABLED=true
SENTINEL_WORKSPACE_ID=your-workspace-id
SENTINEL_SHARED_KEY=your-primary-key
SENTINEL_LOG_TYPE=DANISecurityEvents
```

**Step 3: Install Azure Monitor Dependencies**

Add to `requirements.txt`:
```
azure-monitor-opentelemetry==1.2.0
azure-core==1.29.5
```

### Method 2: Syslog Integration

**Step 1: Configure Syslog in D.A.N.I**

Update `settings.py`:
```python
import logging.handlers

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'sentinel': {
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
        },
    },
    'handlers': {
        'syslog': {
            'level': 'INFO',
            'class': 'logging.handlers.SysLogHandler',
            'address': ('your-sentinel-syslog-endpoint', 514),
            'formatter': 'sentinel',
        },
    },
    'loggers': {
        'dani.security': {
            'handlers': ['syslog'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### Method 3: REST API Integration

**Step 1: Create Custom Logging Service**

Create `accounts/sentinel_service.py`:
```python
import json
import base64
import hmac
import hashlib
from datetime import datetime
import requests
from django.conf import settings

class SentinelLogger:
    def __init__(self):
        self.workspace_id = settings.SENTINEL_WORKSPACE_ID
        self.shared_key = settings.SENTINEL_SHARED_KEY
        self.log_type = settings.SENTINEL_LOG_TYPE
        
    def send_event(self, event_data):
        """Send security event to Sentinel"""
        if not settings.SENTINEL_ENABLED:
            return
            
        # Build the API signature
        date_string = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        json_data = json.dumps(event_data)
        content_length = len(json_data)
        
        string_to_hash = f"POST\\n{content_length}\\napplication/json\\nx-ms-date:{date_string}\\n/api/logs"
        bytes_to_hash = bytes(string_to_hash, 'utf-8')
        decoded_key = base64.b64decode(self.shared_key)
        encoded_hash = base64.b64encode(hmac.new(decoded_key, bytes_to_hash, digestmod=hashlib.sha256).digest()).decode()
        authorization = f"SharedKey {self.workspace_id}:{encoded_hash}"
        
        # Send to Sentinel
        uri = f'https://{self.workspace_id}.ods.opinsights.azure.com/api/logs?api-version=2016-04-01'
        headers = {
            'content-type': 'application/json',
            'Authorization': authorization,
            'Log-Type': self.log_type,
            'x-ms-date': date_string
        }
        
        response = requests.post(uri, data=json_data, headers=headers)
        return response.status_code == 200

sentinel_logger = SentinelLogger()
```

## Security Events to Monitor

### Authentication Events
```python
# Login attempts
{
    "EventType": "UserLogin",
    "Timestamp": "2024-12-03T10:30:00Z",
    "UserId": "user@company.com",
    "Success": true,
    "IPAddress": "192.168.1.100",
    "UserAgent": "Mozilla/5.0...",
    "Location": "New York, US"
}

# Failed logins
{
    "EventType": "FailedLogin",
    "Timestamp": "2024-12-03T10:30:00Z",
    "UserId": "user@company.com",
    "IPAddress": "192.168.1.100",
    "Reason": "Invalid password",
    "AttemptCount": 3
}
```

### Azure AD Sync Events
```python
{
    "EventType": "AzureADSync",
    "Timestamp": "2024-12-03T10:30:00Z",
    "UserId": "user@company.com",
    "Action": "create",
    "Success": true,
    "AzureObjectId": "12345-67890-abcdef"
}
```

### Privilege Changes
```python
{
    "EventType": "PrivilegeChange",
    "Timestamp": "2024-12-03T10:30:00Z",
    "TargetUserId": "user@company.com",
    "AdminUserId": "admin@company.com",
    "OldRole": "employee",
    "NewRole": "hr_manager"
}
```

### API Access Events
```python
{
    "EventType": "APIAccess",
    "Timestamp": "2024-12-03T10:30:00Z",
    "UserId": "user@company.com",
    "Endpoint": "/api/employees/profiles/",
    "Method": "GET",
    "StatusCode": 200,
    "IPAddress": "192.168.1.100"
}
```

## Implementing Security Logging

### Step 1: Create Security Middleware

Create `accounts/middleware.py`:
```python
import json
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver
from .sentinel_service import sentinel_logger

class SecurityEventMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        # Log API access
        if request.path.startswith('/api/') and hasattr(request, 'user') and request.user.is_authenticated:
            event_data = {
                "EventType": "APIAccess",
                "Timestamp": timezone.now().isoformat(),
                "UserId": request.user.email,
                "Endpoint": request.path,
                "Method": request.method,
                "StatusCode": response.status_code,
                "IPAddress": self.get_client_ip(request),
                "UserAgent": request.META.get('HTTP_USER_AGENT', '')
            }
            sentinel_logger.send_event(event_data)
        
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    event_data = {
        "EventType": "UserLogin",
        "Timestamp": timezone.now().isoformat(),
        "UserId": user.email,
        "Success": True,
        "IPAddress": SecurityEventMiddleware().get_client_ip(request),
        "UserAgent": request.META.get('HTTP_USER_AGENT', '')
    }
    sentinel_logger.send_event(event_data)

@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    event_data = {
        "EventType": "FailedLogin",
        "Timestamp": timezone.now().isoformat(),
        "UserId": credentials.get('username', ''),
        "IPAddress": SecurityEventMiddleware().get_client_ip(request),
        "Reason": "Invalid credentials"
    }
    sentinel_logger.send_event(event_data)
```

### Step 2: Add Middleware to Settings

Update `settings.py`:
```python
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'accounts.middleware.SecurityEventMiddleware',  # Add this
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

### Step 3: Log Azure AD Events

Update `accounts/azure_ad_service.py`:
```python
def create_user(self, user: User) -> Tuple[bool, Dict]:
    # ... existing code ...
    
    if success:
        # Log Azure AD sync event
        from .sentinel_service import sentinel_logger
        event_data = {
            "EventType": "AzureADSync",
            "Timestamp": timezone.now().isoformat(),
            "UserId": user.email,
            "Action": "create",
            "Success": True,
            "AzureObjectId": result.get("id")
        }
        sentinel_logger.send_event(event_data)
    
    # ... rest of code ...
```

## Sentinel Analytics Rules

### Rule 1: Multiple Failed Logins
```kql
DANISecurityEvents_CL
| where EventType_s == "FailedLogin"
| summarize FailedAttempts = count() by UserId_s, IPAddress_s, bin(TimeGenerated, 5m)
| where FailedAttempts >= 5
| project TimeGenerated, UserId_s, IPAddress_s, FailedAttempts
```

### Rule 2: Privilege Escalation
```kql
DANISecurityEvents_CL
| where EventType_s == "PrivilegeChange"
| where NewRole_s in ("admin", "hr_manager")
| project TimeGenerated, TargetUserId_s, AdminUserId_s, OldRole_s, NewRole_s
```

### Rule 3: Unusual API Access Patterns
```kql
DANISecurityEvents_CL
| where EventType_s == "APIAccess"
| summarize APICallsCount = count() by UserId_s, bin(TimeGenerated, 1h)
| where APICallsCount > 1000  // Adjust threshold as needed
| project TimeGenerated, UserId_s, APICallsCount
```

### Rule 4: Azure AD Sync Failures
```kql
DANISecurityEvents_CL
| where EventType_s == "AzureADSync"
| where Success_b == false
| summarize FailedSyncs = count() by bin(TimeGenerated, 1h)
| where FailedSyncs >= 10
```

## Deployment Steps

1. **Configure Sentinel workspace**
2. **Update D.A.N.I environment variables**
3. **Deploy updated D.A.N.I code**
4. **Create Sentinel analytics rules**
5. **Set up alerting and automation**

## Testing Integration

```bash
# Test Sentinel logging
docker-compose exec web python manage.py shell -c "
from accounts.sentinel_service import sentinel_logger
event = {
    'EventType': 'Test',
    'Timestamp': '2024-12-03T10:30:00Z',
    'Message': 'D.A.N.I Sentinel integration test'
}
result = sentinel_logger.send_event(event)
print(f'Event sent successfully: {result}')
"
```

## Benefits

- **Real-time threat detection**
- **Automated incident response**
- **Compliance reporting**
- **User behavior analytics**
- **Integration with Microsoft security ecosystem**
- **Centralized security monitoring**

The D.A.N.I platform now provides enterprise-grade security monitoring through Microsoft Sentinel integration!