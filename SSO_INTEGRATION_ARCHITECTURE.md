# SSO Integration Architecture for DANI HRIS Platform

## Table of Contents
- [Overview](#overview)
- [Architecture Design](#architecture-design)
- [Supported SSO Protocols](#supported-sso-protocols)
- [Implementation Plan](#implementation-plan)
- [Security Architecture](#security-architecture)
- [Risk Assessment](#risk-assessment)
- [Integration Points](#integration-points)
- [Configuration Management](#configuration-management)
- [Monitoring & Logging](#monitoring--logging)
- [Fallback Mechanisms](#fallback-mechanisms)

---

## Overview

### **Purpose**
Implement enterprise-grade Single Sign-On (SSO) authentication for the DANI HRIS platform to provide seamless user access across multiple enterprise systems while maintaining security and compliance standards.

### **Scope**
- SAML 2.0 integration with enterprise Identity Providers (IdPs)
- OIDC/OAuth 2.0 support for modern cloud-based authentication
- Azure AD native integration (leveraging existing implementation)
- Multi-tenant SSO support for enterprise customers
- Just-In-Time (JIT) user provisioning
- Role mapping and attribute-based access control

### **Business Benefits**
- Reduced password fatigue and security incidents
- Centralized user management and deprovisioning
- Compliance with enterprise security policies
- Improved user experience and adoption
- Reduced IT support overhead

---

## Architecture Design

### **High-Level Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Enterprise    │    │   DANI HRIS     │    │   External      │
│   Identity      │    │   Platform      │    │   Systems       │
│   Provider      │    │                 │    │                 │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Azure AD      │◄──►│ • SSO Gateway   │◄──►│ • Microsoft     │
│ • Okta          │    │ • Auth Manager  │    │   Graph API     │
│ • ADFS          │    │ • User Mapper   │    │ • Google APIs   │
│ • Generic SAML  │    │ • Session Mgmt  │    │ • Third-party   │
│ • OIDC Provider │    │ • Security      │    │   Integrations  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Component Architecture**

#### **1. SSO Gateway Layer**
```python
# New Django app: sso_auth/
├── models.py          # SSO Provider configurations
├── views.py           # SSO authentication endpoints
├── services/
│   ├── saml_service.py     # SAML 2.0 implementation
│   ├── oidc_service.py     # OIDC/OAuth 2.0 implementation
│   ├── azure_sso.py        # Azure AD SSO (enhanced)
│   └── user_mapper.py      # Attribute mapping service
├── middleware.py      # SSO session management
├── backends.py        # Custom authentication backends
└── utils/
    ├── validators.py       # Security validators
    ├── encryption.py       # Token encryption/decryption
    └── metadata.py         # SAML metadata generation
```

#### **2. Authentication Flow**

**SAML 2.0 Flow:**
```
1. User → DANI Login Page
2. DANI → Redirect to IdP (SAML AuthnRequest)
3. IdP → User Authentication
4. IdP → SAML Response with assertions
5. DANI → Validate SAML Response
6. DANI → Extract user attributes
7. DANI → JIT provisioning (if needed)
8. DANI → Create session & redirect to app
```

**OIDC Flow:**
```
1. User → DANI Login Page
2. DANI → Redirect to IdP authorization endpoint
3. IdP → User Authentication & Consent
4. IdP → Authorization code callback
5. DANI → Exchange code for tokens
6. DANI → Validate ID token & get user info
7. DANI → JIT provisioning (if needed)
8. DANI → Create session & redirect to app
```

---

## Supported SSO Protocols

### **1. SAML 2.0**
- **Use Case**: Enterprise on-premises and hybrid environments
- **Providers**: ADFS, Shibboleth, PingFederate, Custom SAML IdPs
- **Features**:
  - Signed assertions and responses
  - Encrypted assertions support
  - SP-initiated and IdP-initiated flows
  - SLO (Single Logout) support
  - Attribute mapping from SAML assertions

### **2. OpenID Connect (OIDC)**
- **Use Case**: Modern cloud-native applications
- **Providers**: Azure AD, Google, Okta, Auth0, Custom OIDC providers
- **Features**:
  - JWT ID tokens with claims
  - Authorization code flow with PKCE
  - Refresh token support
  - UserInfo endpoint integration
  - Discovery document support

### **3. Azure AD Native (Enhanced)**
- **Use Case**: Microsoft 365 environments
- **Features**:
  - Microsoft Graph API integration
  - Conditional Access policy support
  - MFA enforcement
  - Group-based role mapping
  - Seamless Office 365 integration

---

## Implementation Plan

### **Phase 1: Core SSO Infrastructure (Weeks 1-2)**

#### **Database Models**
```python
class SSOProvider(models.Model):
    """SSO Identity Provider configuration"""
    name = models.CharField(max_length=100)
    provider_type = models.CharField(choices=[
        ('saml2', 'SAML 2.0'),
        ('oidc', 'OpenID Connect'),
        ('azure_ad', 'Azure AD Native'),
    ])
    enabled = models.BooleanField(default=True)
    domain_restriction = models.CharField(max_length=255, blank=True)
    
    # SAML Configuration
    saml_entity_id = models.URLField(blank=True)
    saml_sso_url = models.URLField(blank=True)
    saml_slo_url = models.URLField(blank=True)
    saml_x509_cert = models.TextField(blank=True)
    
    # OIDC Configuration
    oidc_issuer = models.URLField(blank=True)
    oidc_client_id = models.CharField(max_length=255, blank=True)
    oidc_client_secret = models.CharField(max_length=500, blank=True)
    oidc_scope = models.CharField(max_length=255, default='openid profile email')
    
    # User Mapping
    attribute_mapping = models.JSONField(default=dict)
    role_mapping = models.JSONField(default=dict)
    auto_provision = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class SSOSession(models.Model):
    """Track SSO sessions for security auditing"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.ForeignKey(SSOProvider, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=255, unique=True)
    idp_session_id = models.CharField(max_length=255, blank=True)
    login_time = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    is_active = models.BooleanField(default=True)
```

#### **Authentication Backend**
```python
class SSOAuthenticationBackend(BaseBackend):
    """Custom authentication backend for SSO"""
    
    def authenticate(self, request, sso_data=None, provider=None):
        if not sso_data or not provider:
            return None
            
        # Extract user attributes from SSO response
        user_attributes = self.extract_user_attributes(sso_data, provider)
        
        # Get or create user
        user = self.get_or_create_user(user_attributes, provider)
        
        # Map roles and permissions
        self.map_user_roles(user, user_attributes, provider)
        
        # Create SSO session record
        self.create_sso_session(user, provider, request)
        
        return user
```

### **Phase 2: SAML 2.0 Integration (Weeks 3-4)**

#### **SAML Service Implementation**
```python
class SAMLService:
    """SAML 2.0 authentication service"""
    
    def __init__(self, provider_config):
        self.provider = provider_config
        self.sp_config = self.build_sp_config()
    
    def initiate_login(self, request, relay_state=None):
        """Initiate SAML SSO login"""
        # Generate SAML AuthnRequest
        # Redirect user to IdP
        
    def process_response(self, request):
        """Process SAML Response from IdP"""
        # Validate SAML Response
        # Extract assertions
        # Return user attributes
        
    def initiate_logout(self, request):
        """Initiate SAML SLO (Single Logout)"""
        # Generate SAML LogoutRequest
        # Clear local session
        
    def get_metadata(self):
        """Generate SP metadata for IdP configuration"""
        # Return SAML metadata XML
```

### **Phase 3: OIDC Integration (Weeks 5-6)**

#### **OIDC Service Implementation**
```python
class OIDCService:
    """OpenID Connect authentication service"""
    
    def __init__(self, provider_config):
        self.provider = provider_config
        self.client = self.build_oidc_client()
    
    def initiate_login(self, request, redirect_uri):
        """Initiate OIDC authentication"""
        # Generate authorization URL with state/nonce
        # Redirect user to IdP
        
    def process_callback(self, request):
        """Process OIDC callback with authorization code"""
        # Exchange code for tokens
        # Validate ID token
        # Get user info from UserInfo endpoint
        # Return user attributes
        
    def refresh_token(self, refresh_token):
        """Refresh access token"""
        # Exchange refresh token for new access token
```

### **Phase 4: User Provisioning & Mapping (Week 7)**

#### **User Mapper Service**
```python
class UserMappingService:
    """Map SSO attributes to DANI user model"""
    
    def __init__(self, provider):
        self.provider = provider
        self.attribute_map = provider.attribute_mapping
        self.role_map = provider.role_mapping
    
    def map_user_attributes(self, sso_attributes):
        """Map SSO attributes to User model fields"""
        mapped_data = {}
        
        # Standard attribute mapping
        mapped_data['email'] = sso_attributes.get(
            self.attribute_map.get('email', 'email')
        )
        mapped_data['first_name'] = sso_attributes.get(
            self.attribute_map.get('first_name', 'given_name')
        )
        mapped_data['last_name'] = sso_attributes.get(
            self.attribute_map.get('last_name', 'family_name')
        )
        
        # Custom attribute mapping
        for local_field, sso_field in self.attribute_map.items():
            if sso_field in sso_attributes:
                mapped_data[local_field] = sso_attributes[sso_field]
        
        return mapped_data
    
    def map_user_roles(self, sso_attributes):
        """Map SSO groups/roles to DANI roles"""
        user_groups = sso_attributes.get('groups', [])
        
        for group in user_groups:
            if group in self.role_map:
                return self.role_map[group]
        
        return 'employee'  # Default role
```

---

## Security Architecture

### **Security Controls**

#### **1. Token Security**
- **JWT Validation**: Signature verification, expiration checks, audience validation
- **SAML Assertion Security**: XML signature validation, timestamp validation, replay protection
- **Token Encryption**: Sensitive tokens encrypted at rest using Django's encryption
- **Secure Storage**: SSO secrets stored in encrypted database fields

#### **2. Session Management**
```python
class SSOSessionMiddleware:
    """Enhanced session security for SSO users"""
    
    def process_request(self, request):
        # Validate SSO session is still active
        # Check for session timeout
        # Verify IdP session status (if supported)
        # Implement concurrent session limits
```

#### **3. Input Validation**
- **SAML Response Validation**: XML schema validation, signature verification
- **OIDC Token Validation**: JWT signature and claims validation
- **Attribute Sanitization**: Clean and validate all user attributes from IdP

#### **4. Audit & Monitoring**
```python
class SSOAuditLogger:
    """Comprehensive SSO audit logging"""
    
    def log_sso_event(self, event_type, user, provider, request, **kwargs):
        # Log all SSO authentication events
        # Track failed authentication attempts
        # Monitor suspicious activity patterns
        # Integration with security monitoring tools
```

---

## Risk Assessment

### **High-Risk Areas**

#### **1. Identity Provider Compromise (Risk: HIGH)**
- **Description**: If the external IdP is compromised, attackers could gain access to DANI
- **Mitigation**:
  - Implement certificate pinning for SAML
  - Regular rotation of OIDC client secrets
  - Monitor IdP security advisories
  - Implement additional MFA requirements for admin roles

#### **2. Token Interception (Risk: MEDIUM)**
- **Description**: SAML assertions or OIDC tokens intercepted in transit
- **Mitigation**:
  - Enforce HTTPS/TLS 1.3 for all SSO communications
  - Short token lifetimes (5-15 minutes)
  - Token binding where supported
  - Network-level monitoring for SSL/TLS anomalies

#### **3. Session Hijacking (Risk: MEDIUM)**
- **Description**: SSO session cookies stolen or replayed
- **Mitigation**:
  - Secure, HttpOnly, SameSite cookie flags
  - Session fingerprinting (IP, User-Agent validation)
  - Concurrent session limits
  - Regular session rotation

#### **4. Privilege Escalation (Risk: MEDIUM)**
- **Description**: Incorrect role mapping grants excessive privileges
- **Mitigation**:
  - Principle of least privilege in role mapping
  - Regular audit of role assignments
  - Manual approval for admin role assignments
  - Detailed logging of privilege changes

### **Medium-Risk Areas**

#### **1. JIT Provisioning Abuse (Risk: MEDIUM)**
- **Description**: Unauthorized users creating accounts through SSO
- **Mitigation**:
  - Domain restrictions for auto-provisioning
  - Manual approval workflow for new users
  - Account approval queues for non-standard domains
  - Rate limiting on account creation

#### **2. Metadata Tampering (Risk: MEDIUM)**
- **Description**: SAML metadata modified to redirect authentication
- **Mitigation**:
  - Metadata signature validation
  - Out-of-band metadata verification
  - Regular metadata integrity checks
  - Secure metadata storage and transmission

### **Low-Risk Areas**

#### **1. Service Availability (Risk: LOW)**
- **Description**: SSO provider downtime affecting user access
- **Mitigation**:
  - Fallback to local authentication
  - Multiple SSO provider support
  - Clear user communication during outages
  - SLA monitoring and alerting

---

## Integration Points

### **1. Frontend Integration**
```javascript
// SSO Login Component
class SSOLoginComponent {
    displayProviders() {
        // Show available SSO providers based on user's email domain
        // Redirect to appropriate SSO initiation endpoint
    }
    
    handleSSOCallback() {
        // Process SSO callback and redirect to dashboard
        // Handle error cases gracefully
    }
}
```

### **2. API Integration**
```python
# SSO-aware API authentication
class SSOTokenAuthentication(BaseAuthentication):
    """API authentication using SSO-issued tokens"""
    
    def authenticate(self, request):
        # Validate SSO token in API requests
        # Support for Bearer tokens from OIDC
        # SAML assertion validation for API calls
```

### **3. Existing Systems Integration**
- **Azure AD Sync**: Enhanced to support SSO attributes
- **User Management**: Automatic role assignment from SSO
- **Audit Logging**: Extended to include SSO events
- **Permissions**: Role-based access using SSO group memberships

---

## Configuration Management

### **Admin Interface Enhancements**
```python
@admin.register(SSOProvider)
class SSOProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider_type', 'enabled', 'domain_restriction']
    fieldsets = (
        ('Basic Configuration', {
            'fields': ('name', 'provider_type', 'enabled', 'domain_restriction')
        }),
        ('SAML Configuration', {
            'fields': ('saml_entity_id', 'saml_sso_url', 'saml_slo_url', 'saml_x509_cert'),
            'classes': ('collapse',)
        }),
        ('OIDC Configuration', {
            'fields': ('oidc_issuer', 'oidc_client_id', 'oidc_client_secret', 'oidc_scope'),
            'classes': ('collapse',)
        }),
        ('User Mapping', {
            'fields': ('attribute_mapping', 'role_mapping', 'auto_provision'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['test_sso_connection', 'download_metadata']
```

### **Environment Configuration**
```python
# settings.py additions
SSO_SETTINGS = {
    'ENABLED': env.bool('SSO_ENABLED', False),
    'DEFAULT_PROVIDER': env.str('SSO_DEFAULT_PROVIDER', None),
    'ALLOW_LOCAL_LOGIN': env.bool('SSO_ALLOW_LOCAL_LOGIN', True),
    'SESSION_TIMEOUT': env.int('SSO_SESSION_TIMEOUT', 3600),
    'CONCURRENT_SESSIONS': env.int('SSO_CONCURRENT_SESSIONS', 3),
    'AUTO_PROVISION': env.bool('SSO_AUTO_PROVISION', True),
    'REQUIRE_SSL': env.bool('SSO_REQUIRE_SSL', True),
}
```

---

## Monitoring & Logging

### **Security Monitoring**
```python
class SSOSecurityMonitor:
    """Real-time SSO security monitoring"""
    
    def monitor_authentication_patterns(self):
        # Detect unusual login patterns
        # Monitor for brute force attempts via SSO
        # Alert on failed authentication spikes
        
    def validate_session_integrity(self):
        # Check for session anomalies
        # Detect concurrent session violations
        # Monitor for session hijacking indicators
        
    def audit_role_assignments(self):
        # Track role changes from SSO
        # Alert on privilege escalations
        # Monitor for unauthorized admin access
```

### **Compliance Logging**
- **Authentication Events**: All SSO login/logout events
- **Authorization Changes**: Role and permission modifications
- **Configuration Changes**: SSO provider configuration updates
- **Security Events**: Failed authentications, session anomalies
- **Data Access**: API calls using SSO authentication

---

## Fallback Mechanisms

### **1. Local Authentication Fallback**
```python
class HybridAuthenticationView:
    """Support both SSO and local authentication"""
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
            
        # Show SSO options if available
        sso_providers = SSOProvider.objects.filter(enabled=True)
        
        # Always show local login option for emergencies
        return render(request, 'login.html', {
            'sso_providers': sso_providers,
            'allow_local_login': settings.SSO_ALLOW_LOCAL_LOGIN
        })
```

### **2. Emergency Access**
- **Local Admin Account**: Always maintain local superuser access
- **Emergency Bypass**: Temporary SSO disable capability
- **Recovery Procedures**: Clear documentation for SSO failures

### **3. Graceful Degradation**
- **Provider Downtime**: Automatic fallback to local authentication
- **Partial Integration**: Continue operation if some SSO features fail
- **User Communication**: Clear messaging during SSO issues

---

## Implementation Timeline

### **Week 1-2: Infrastructure Setup**
- Database models and migrations
- Basic admin interface
- Authentication backend framework
- Security middleware implementation

### **Week 3-4: SAML 2.0 Integration**
- SAML service implementation
- Metadata generation and validation
- SP-initiated and IdP-initiated flows
- Single Logout (SLO) support

### **Week 5-6: OIDC Integration**
- OIDC client implementation
- Authorization code flow with PKCE
- Token validation and refresh
- UserInfo endpoint integration

### **Week 7: User Provisioning**
- Attribute mapping service
- JIT provisioning logic
- Role mapping implementation
- User profile synchronization

### **Week 8: Testing & Security**
- Comprehensive security testing
- Penetration testing
- Performance optimization
- Documentation completion

---

## Dependencies

### **Python Packages**
```requirements
# SSO-specific dependencies
python3-saml==1.15.0      # SAML 2.0 support
authlib==1.2.1             # OIDC/OAuth 2.0 support
cryptography==41.0.0       # Enhanced cryptographic functions
PyJWT[crypto]==2.8.0       # JWT token handling
xmlsec==1.3.13             # XML security for SAML
```

### **External Services**
- **Identity Providers**: Azure AD, Okta, ADFS, custom SAML/OIDC providers
- **Certificate Authority**: For SSL/TLS certificates
- **Time Synchronization**: NTP for accurate timestamp validation
- **DNS**: Proper DNS configuration for metadata URLs

---

## Success Criteria

### **Functional Requirements**
- ✅ Support for SAML 2.0 and OIDC protocols
- ✅ JIT user provisioning with attribute mapping
- ✅ Role-based access control from SSO groups
- ✅ Single Logout (SLO) functionality
- ✅ Multi-provider support with domain-based routing

### **Security Requirements**
- ✅ All communications over HTTPS/TLS 1.3
- ✅ Token validation and encryption at rest
- ✅ Comprehensive audit logging
- ✅ Session security and timeout enforcement
- ✅ Fallback authentication mechanisms

### **Performance Requirements**
- ✅ SSO authentication < 3 seconds end-to-end
- ✅ Support for 1000+ concurrent SSO sessions
- ✅ 99.9% uptime with proper fallback mechanisms
- ✅ Horizontal scalability for enterprise deployments

---

**Document Version**: 1.0  
**Last Updated**: July 2025  
**Review Schedule**: Quarterly security review required