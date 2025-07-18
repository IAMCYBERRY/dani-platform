"""
User authentication models with role-based access control.

This module defines a custom User model with predefined roles for the HRIS + ATS platform:
- Admin: Full system access
- HR Manager: HR operations and recruitment oversight
- Hiring Manager: Department-specific hiring and team management
- Employee: Basic employee portal access
- Candidate: Limited access for application tracking
"""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.core.validators import EmailValidator
from django.core.cache import cache
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model with email as the unique identifier and role-based permissions.
    """
    
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        HR_MANAGER = 'hr_manager', 'HR Manager'
        HIRING_MANAGER = 'hiring_manager', 'Hiring Manager'
        EMPLOYEE = 'employee', 'Employee'
        CANDIDATE = 'candidate', 'Candidate'
    
    # Core user fields
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        help_text='Username/UPN for login and Azure AD User Principal Name'
    )
    business_email = models.EmailField(
        blank=True,
        validators=[EmailValidator()],
        help_text='Business email address (populates Azure AD email property)'
    )
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    
    # Role and status fields
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
        help_text='User role determining access permissions'
    )
    
    # Account status
    is_active = models.BooleanField(
        default=True,
        help_text='Designates whether this user should be treated as active'
    )
    is_staff = models.BooleanField(
        default=False,
        help_text='Designates whether the user can log into the admin site'
    )
    
    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)
    
    # Profile information
    phone_number = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True
    )
    
    # Organization context
    department = models.ForeignKey(
        'employees.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    job_title = models.ForeignKey(
        'employees.JobTitle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        help_text='User job title/position'
    )
    job_title_old = models.CharField(max_length=100, blank=True, null=True, help_text='Temporary field for migration')
    
    # Additional employee information for Azure AD sync
    company_name = models.CharField(max_length=100, blank=True, help_text='Company or organization name')
    employee_id = models.CharField(max_length=50, blank=True, unique=True, null=True, help_text='Unique employee identifier')
    employee_type = models.CharField(
        max_length=20,
        choices=[
            ('full_time', 'Full Time'),
            ('part_time', 'Part Time'),
            ('contractor', 'Contractor'),
            ('intern', 'Intern'),
            ('temporary', 'Temporary'),
        ],
        blank=True,
        help_text='Employment type'
    )
    hire_date = models.DateField(blank=True, null=True, help_text='Employee hire date')
    office_location = models.CharField(max_length=100, blank=True, help_text='Primary office or work location')
    is_manager = models.BooleanField(
        default=False,
        help_text='Designates whether this user can be assigned as a manager to other users'
    )
    manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_direct_reports',
        limit_choices_to={'is_manager': True, 'is_active': True},
        help_text='Direct manager or supervisor'
    )
    
    # Azure AD integration fields
    azure_ad_object_id = models.CharField(
        max_length=36,
        blank=True,
        null=True,
        unique=True,
        help_text='Azure AD Object ID for Microsoft Graph API integration'
    )
    azure_ad_sync_enabled = models.BooleanField(
        default=True,
        help_text='Enable automatic sync with Azure AD'
    )
    azure_ad_last_sync = models.DateTimeField(
        blank=True,
        null=True,
        help_text='Last successful sync with Azure AD'
    )
    azure_ad_sync_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('synced', 'Synced'),
            ('failed', 'Failed'),
            ('disabled', 'Disabled'),
        ],
        default='pending',
        help_text='Current Azure AD sync status'
    )
    azure_ad_sync_error = models.TextField(
        blank=True,
        help_text='Last sync error message for troubleshooting'
    )
    
    # Manager for custom user operations
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
            models.Index(fields=['azure_ad_object_id']),
            models.Index(fields=['azure_ad_sync_status']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """Return the user's first name."""
        return self.first_name
    
    @property
    def is_admin(self):
        """Check if user has admin role."""
        return self.role == self.Role.ADMIN
    
    @property
    def is_hr_manager(self):
        """Check if user has HR manager role."""
        return self.role == self.Role.HR_MANAGER
    
    @property
    def is_hiring_manager(self):
        """Check if user has hiring manager role."""
        return self.role == self.Role.HIRING_MANAGER
    
    @property
    def is_employee(self):
        """Check if user has employee role."""
        return self.role == self.Role.EMPLOYEE
    
    @property
    def is_candidate(self):
        """Check if user has candidate role."""
        return self.role == self.Role.CANDIDATE
    
    def has_permission(self, permission):
        """
        Check if user has specific permission based on role.
        This method can be extended for fine-grained permissions.
        """
        permission_map = {
            self.Role.ADMIN: ['all'],
            self.Role.HR_MANAGER: [
                'view_all_employees', 'manage_employees', 'view_all_jobs',
                'manage_jobs', 'view_all_applicants', 'manage_applicants',
                'schedule_interviews', 'view_reports'
            ],
            self.Role.HIRING_MANAGER: [
                'view_department_employees', 'view_department_jobs',
                'manage_department_jobs', 'view_department_applicants',
                'manage_department_applicants', 'schedule_interviews'
            ],
            self.Role.EMPLOYEE: [
                'view_own_profile', 'update_own_profile', 'view_company_jobs'
            ],
            self.Role.CANDIDATE: [
                'view_own_applications', 'apply_to_jobs', 'view_application_status'
            ]
        }
        
        user_permissions = permission_map.get(self.role, [])
        return 'all' in user_permissions or permission in user_permissions


class UserSession(models.Model):
    """
    Track user sessions for security and analytics.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'user_sessions'
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_key']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.ip_address}"


class PasswordResetToken(models.Model):
    """
    Handle password reset tokens with expiration.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'password_reset_tokens'
        verbose_name = 'Password Reset Token'
        verbose_name_plural = 'Password Reset Tokens'
    
    def __str__(self):
        return f"Reset token for {self.user.email}"
    
    def is_expired(self):
        """Check if the token has expired."""
        return timezone.now() > self.expires_at


class AzureADSettings(models.Model):
    """
    Dynamic Azure AD configuration settings that can be managed through the admin panel.
    """
    
    # Basic configuration
    enabled = models.BooleanField(
        default=False,
        help_text='Enable Azure AD integration'
    )
    tenant_id = models.CharField(
        max_length=100,
        blank=True,
        help_text='Azure AD Tenant ID (Directory ID)'
    )
    client_id = models.CharField(
        max_length=100,
        blank=True,
        help_text='Azure AD Application (Client) ID'
    )
    client_secret = models.CharField(
        max_length=500,
        blank=True,
        help_text='Azure AD Client Secret'
    )
    
    # Sync settings
    sync_enabled = models.BooleanField(
        default=False,
        help_text='Enable automatic user synchronization'
    )
    sync_on_user_create = models.BooleanField(
        default=True,
        help_text='Automatically sync new users to Azure AD'
    )
    sync_on_user_update = models.BooleanField(
        default=True,
        help_text='Automatically sync user updates to Azure AD'
    )
    sync_on_user_disable = models.BooleanField(
        default=True,
        help_text='Automatically disable users in Azure AD when deactivated'
    )
    
    # Advanced settings
    authority = models.URLField(
        default='https://login.microsoftonline.com/',
        help_text='Azure AD Authority URL'
    )
    scope = models.CharField(
        max_length=200,
        default='https://graph.microsoft.com/.default',
        help_text='Microsoft Graph API scope'
    )
    default_password_length = models.PositiveIntegerField(
        default=12,
        help_text='Default password length for new Azure AD users'
    )
    
    # Automatic sync scheduling
    enable_automatic_sync = models.BooleanField(
        default=False,
        help_text='Enable automatic periodic synchronization of all users'
    )
    sync_interval_hours = models.PositiveIntegerField(
        default=24,
        help_text='Interval in hours between automatic sync operations'
    )
    last_automatic_sync = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last time automatic sync was performed'
    )
    
    # Test results
    connection_status = models.CharField(
        max_length=20,
        choices=[
            ('unknown', 'Unknown'),
            ('connected', 'Connected'),
            ('failed', 'Failed'),
            ('testing', 'Testing'),
        ],
        default='unknown',
        help_text='Last connection test result'
    )
    last_test_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last time connection was tested'
    )
    test_error_message = models.TextField(
        blank=True,
        help_text='Error message from last failed test'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='User who last updated these settings'
    )
    
    class Meta:
        db_table = 'azure_ad_settings'
        verbose_name = 'Azure AD Settings'
        verbose_name_plural = 'Azure AD Settings'
    
    def __str__(self):
        status = "Enabled" if self.enabled else "Disabled"
        return f"Azure AD Settings ({status})"
    
    def save(self, *args, **kwargs):
        # Clear cache when settings are updated
        cache.delete('azure_ad_settings')
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get cached Azure AD settings or create default if none exist."""
        settings = cache.get('azure_ad_settings')
        if settings is None:
            settings, created = cls.objects.get_or_create(
                id=1,  # Singleton pattern - only one settings record
                defaults={
                    'enabled': False,
                    'sync_enabled': False,
                }
            )
            cache.set('azure_ad_settings', settings, 300)  # Cache for 5 minutes
        return settings
    
    @property
    def is_configured(self):
        """Check if Azure AD is properly configured."""
        return (
            self.enabled and
            self.tenant_id and
            self.client_id and
            self.client_secret and
            len(self.tenant_id.strip()) > 0 and
            len(self.client_id.strip()) > 0 and
            len(self.client_secret.strip()) > 0
        )
    
    @property
    def authority_url(self):
        """Get the complete authority URL."""
        if self.tenant_id:
            return f"{self.authority.rstrip('/')}/{self.tenant_id}"
        return self.authority