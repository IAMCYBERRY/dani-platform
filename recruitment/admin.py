"""
Django admin configuration for recruitment app.
"""

from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import secrets
import string
from .models import JobPosting, Applicant, Interview, JobOfferment, PowerAppsConfiguration


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'department', 'status', 'job_type', 'location',
        'applications_count', 'views_count', 'created_at'
    ]
    list_filter = [
        'status', 'job_type', 'experience_level', 'department',
        'remote_work_allowed', 'is_featured'
    ]
    search_fields = ['title', 'description', 'location']
    readonly_fields = [
        'views_count', 'applications_count', 'created_at', 
        'updated_at', 'published_at'
    ]
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'email', 'job', 'status', 'source', 
        'rating', 'applied_at'
    ]
    list_filter = [
        'status', 'source', 'job__department', 'willing_to_relocate',
        'applied_at'
    ]
    search_fields = [
        'first_name', 'last_name', 'email', 'current_location',
        'job__title'
    ]
    readonly_fields = ['full_name', 'days_in_pipeline', 'applied_at', 'last_activity']


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = [
        'applicant', 'interviewer', 'interview_type', 'scheduled_date',
        'scheduled_time', 'status', 'overall_score'
    ]
    list_filter = [
        'interview_type', 'status', 'scheduled_date', 'is_final_round'
    ]
    search_fields = [
        'applicant__first_name', 'applicant__last_name',
        'interviewer__first_name', 'interviewer__last_name'
    ]
    readonly_fields = ['scheduled_datetime', 'created_at', 'updated_at', 'completed_at']


@admin.register(JobOfferment)
class JobOffermentAdmin(admin.ModelAdmin):
    list_display = [
        'applicant', 'job', 'offered_salary', 'status',
        'offer_expiry_date', 'extended_by'
    ]
    list_filter = ['status', 'extended_at', 'offer_expiry_date']
    search_fields = [
        'applicant__first_name', 'applicant__last_name',
        'job__title'
    ]
    readonly_fields = [
        'is_expired', 'days_until_expiry', 'extended_at', 
        'responded_at', 'created_at', 'updated_at'
    ]


@admin.register(PowerAppsConfiguration)
class PowerAppsConfigurationAdmin(admin.ModelAdmin):
    """
    Admin interface for PowerApps configuration management.
    """
    
    list_display = [
        'name', 'status', 'auto_assign_to_job', 'total_submissions', 
        'last_submission_date', 'created_at'
    ]
    
    list_filter = [
        'status', 'auto_assign_to_job__department', 'require_email_verification',
        'auto_send_confirmation', 'created_at'
    ]
    
    search_fields = [
        'name', 'description', 'api_key', 'auto_assign_to_job__title'
    ]
    
    readonly_fields = [
        'total_submissions', 'successful_submissions', 'last_submission_date',
        'created_at', 'updated_at', 'created_by'
    ]
    
    fieldsets = (
        ('Basic Configuration', {
            'fields': (
                'name', 'description', 'status', 'auto_assign_to_job',
                'default_application_source'
            ),
            'description': 'Basic settings for your PowerApps form integration'
        }),
        
        ('API Connection', {
            'fields': (
                'api_key', 'allowed_origins', 'rate_limit_per_hour'
            ),
            'description': 'API connection details for PowerApps integration'
        }),
        
        ('Field Mapping', {
            'fields': (
                'field_mapping', 'required_fields', 'custom_validation_rules'
            ),
            'classes': ('collapse',),
            'description': 'Map PowerApps form fields to DANI applicant fields'
        }),
        
        ('File Upload Settings', {
            'fields': (
                'resume_field_name', 'cover_letter_field_name',
                'max_file_size_mb', 'allowed_file_types'
            ),
            'classes': ('collapse',),
            'description': 'Configure file upload handling for resumes and cover letters'
        }),
        
        ('Security & Validation', {
            'fields': (
                'allowed_email_domains', 'require_email_verification',
                'enable_duplicate_detection'
            ),
            'classes': ('collapse',),
            'description': 'Security and validation settings'
        }),
        
        ('Workflow Settings', {
            'fields': (
                'auto_send_confirmation', 'confirmation_email_template',
                'notification_emails', 'webhook_url'
            ),
            'classes': ('collapse',),
            'description': 'Configure automated workflows and notifications'
        }),
        
        ('Analytics & Tracking', {
            'fields': (
                'total_submissions', 'successful_submissions', 'last_submission_date'
            ),
            'classes': ('collapse',),
            'description': 'View submission statistics and analytics'
        }),
        
        ('System Information', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',),
            'description': 'System metadata and tracking information'
        })
    )
    
    actions = ['activate_configurations', 'deactivate_configurations', 'regenerate_api_keys']
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize the form for PowerApps configuration."""
        form = super().get_form(request, obj, **kwargs)
        return form
    
    def save_model(self, request, obj, form, change):
        """Save the PowerApps configuration with additional processing."""
        
        # Set created_by for new objects
        if not change:  # Creating new object
            obj.created_by = request.user
            
            # Generate API key if not set
            if not obj.api_key:
                obj.api_key = self._generate_api_key()
        
        # Validate field mapping
        if obj.field_mapping:
            validation_errors = self._validate_field_mapping(obj.field_mapping)
            if validation_errors:
                messages.warning(
                    request,
                    f"Field mapping warnings: {', '.join(validation_errors)}"
                )
        
        super().save_model(request, obj, form, change)
        
        # Show success message with API details
        if not change:  # New configuration
            message = (
                f"PowerApps configuration '{obj.name}' created successfully!<br>"
                f"<strong>API Endpoint:</strong> {obj.get_api_endpoint_url(request)}<br>"
                f"<strong>API Key:</strong> {obj.api_key}<br>"
                f"Please save these details for your PowerApps form configuration."
            )
            messages.success(request, mark_safe(message))
    
    def api_key_display(self, obj):
        """Display API key with copy functionality."""
        if obj.api_key:
            return format_html(
                '<code style="background: #f0f0f0; padding: 4px; border-radius: 3px;">{}</code>',
                obj.api_key
            )
        return "Not generated"
    api_key_display.short_description = "API Key"
    
    def api_endpoint_display(self, obj):
        """Display API endpoint URL."""
        if obj.api_key:
            return format_html(
                '<code style="background: #f0f0f0; padding: 4px; border-radius: 3px; word-break: break-all;">'
                '/api/recruitment/powerapps/{}/</code>',
                obj.api_key
            )
        return "API key required"
    api_endpoint_display.short_description = "API Endpoint"
    
    def success_rate_display(self, obj):
        """Display success rate as a percentage with visual indicator."""
        rate = obj.success_rate
        if rate >= 90:
            color = "green"
            icon = "✅"
        elif rate >= 70:
            color = "orange"
            icon = "⚠️"
        else:
            color = "red"
            icon = "❌"
        
        return format_html(
            '<span style="color: {};">{} {:.1f}%</span>',
            color, icon, rate
        )
    success_rate_display.short_description = "Success Rate"
    
    @admin.action(description="Activate selected configurations")
    def activate_configurations(self, request, queryset):
        """Activate selected PowerApps configurations."""
        updated = queryset.update(status=PowerAppsConfiguration.Status.ACTIVE)
        messages.success(
            request,
            f"Successfully activated {updated} PowerApps configuration(s)."
        )
    
    @admin.action(description="Deactivate selected configurations")
    def deactivate_configurations(self, request, queryset):
        """Deactivate selected PowerApps configurations."""
        updated = queryset.update(status=PowerAppsConfiguration.Status.INACTIVE)
        messages.success(
            request,
            f"Successfully deactivated {updated} PowerApps configuration(s)."
        )
    
    @admin.action(description="Regenerate API keys")
    def regenerate_api_keys(self, request, queryset):
        """Regenerate API keys for selected configurations."""
        updated_count = 0
        for config in queryset:
            config.api_key = self._generate_api_key()
            config.save(update_fields=['api_key', 'updated_at'])
            updated_count += 1
        
        messages.warning(
            request,
            f"Regenerated API keys for {updated_count} configuration(s). "
            "Please update your PowerApps forms with the new API keys."
        )
    
    def _generate_api_key(self):
        """Generate a secure API key for PowerApps authentication."""
        # Generate a 32-character API key
        alphabet = string.ascii_letters + string.digits
        return 'dani_powerapps_' + ''.join(secrets.choice(alphabet) for _ in range(32))
    
    def _validate_field_mapping(self, field_mapping):
        """Validate field mapping configuration."""
        errors = []
        
        # Check for valid DANI applicant fields
        valid_dani_fields = [
            'first_name', 'last_name', 'email', 'phone', 'current_location',
            'years_of_experience', 'current_salary', 'expected_salary',
            'linkedin_url', 'portfolio_url', 'willing_to_relocate',
            'available_start_date', 'cover_letter_text'
        ]
        
        for powerapps_field, dani_field in field_mapping.items():
            if dani_field not in valid_dani_fields:
                errors.append(f"Unknown DANI field: {dani_field}")
        
        return errors