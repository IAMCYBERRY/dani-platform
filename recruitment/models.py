"""
Recruitment and Applicant Tracking System (ATS) models.

This module contains models for managing job postings, applications, interviews,
and the complete hiring pipeline.
"""

from django.db import models
from django.utils import timezone
from django.core.validators import EmailValidator, FileExtensionValidator
from accounts.models import User
from employees.models import Department


class JobPosting(models.Model):
    """
    Job posting model for managing open positions.
    """
    
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        ACTIVE = 'active', 'Active'
        PAUSED = 'paused', 'Paused'
        CLOSED = 'closed', 'Closed'
        FILLED = 'filled', 'Filled'
    
    class JobType(models.TextChoices):
        FULL_TIME = 'full_time', 'Full Time'
        PART_TIME = 'part_time', 'Part Time'
        CONTRACT = 'contract', 'Contract'
        TEMPORARY = 'temporary', 'Temporary'
        INTERN = 'intern', 'Internship'
    
    class ExperienceLevel(models.TextChoices):
        ENTRY = 'entry', 'Entry Level'
        JUNIOR = 'junior', 'Junior'
        MID = 'mid', 'Mid Level'
        SENIOR = 'senior', 'Senior'
        LEAD = 'lead', 'Lead'
        EXECUTIVE = 'executive', 'Executive'
    
    # Basic job information
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(help_text='Detailed job description')
    requirements = models.TextField(help_text='Job requirements and qualifications')
    responsibilities = models.TextField(help_text='Key responsibilities')
    
    # Organizational details
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='job_postings'
    )
    hiring_manager = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='managed_job_postings',
        limit_choices_to={'role__in': ['hiring_manager', 'hr_manager', 'admin']}
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_job_postings'
    )
    
    # Job details
    job_type = models.CharField(
        max_length=20,
        choices=JobType.choices,
        default=JobType.FULL_TIME
    )
    experience_level = models.CharField(
        max_length=20,
        choices=ExperienceLevel.choices,
        default=ExperienceLevel.MID
    )
    location = models.CharField(max_length=200)
    remote_work_allowed = models.BooleanField(default=False)
    
    # Compensation
    salary_min = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Minimum salary range'
    )
    salary_max = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Maximum salary range'
    )
    benefits = models.TextField(blank=True, help_text='Benefits and perks')
    
    # Status and timeline
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    application_deadline = models.DateField(null=True, blank=True)
    expected_start_date = models.DateField(null=True, blank=True)
    
    # SEO and visibility
    is_featured = models.BooleanField(default=False)
    external_job_board_url = models.URLField(blank=True)
    
    # Tracking
    views_count = models.PositiveIntegerField(default=0)
    applications_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'job_postings'
        verbose_name = 'Job Posting'
        verbose_name_plural = 'Job Postings'
        indexes = [
            models.Index(fields=['status', 'department']),
            models.Index(fields=['slug']),
            models.Index(fields=['created_at']),
            models.Index(fields=['application_deadline']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.department.name}"
    
    @property
    def is_active(self):
        """Check if job posting is currently accepting applications."""
        return (
            self.status == self.Status.ACTIVE and
            (not self.application_deadline or 
             self.application_deadline >= timezone.now().date())
        )
    
    @property
    def days_since_posted(self):
        """Calculate days since job was published."""
        if self.published_at:
            return (timezone.now() - self.published_at).days
        return 0
    
    def save(self, *args, **kwargs):
        """Set published_at when status changes to active and auto-generate slug."""
        # Auto-generate slug if not provided
        if not self.slug and self.title:
            from django.utils.text import slugify
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            # Exclude current instance when checking for duplicates
            existing_slugs = JobPosting.objects.exclude(pk=self.pk).values_list('slug', flat=True)
            while slug in existing_slugs:
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Set published_at when status changes to active
        if self.status == self.Status.ACTIVE and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)


class Applicant(models.Model):
    """
    Applicant model for job candidates.
    """
    
    class Source(models.TextChoices):
        WEBSITE = 'website', 'Company Website'
        LINKEDIN = 'linkedin', 'LinkedIn'
        INDEED = 'indeed', 'Indeed'
        GLASSDOOR = 'glassdoor', 'Glassdoor'
        REFERRAL = 'referral', 'Employee Referral'
        RECRUITER = 'recruiter', 'Recruiter'
        JOB_FAIR = 'job_fair', 'Job Fair'
        OTHER = 'other', 'Other'
    
    class Status(models.TextChoices):
        NEW = 'new', 'New Application'
        SCREENING = 'screening', 'Initial Screening'
        PHONE_INTERVIEW = 'phone_interview', 'Phone Interview'
        TECHNICAL_TEST = 'technical_test', 'Technical Test'
        ONSITE_INTERVIEW = 'onsite_interview', 'Onsite Interview'
        FINAL_INTERVIEW = 'final_interview', 'Final Interview'
        REFERENCE_CHECK = 'reference_check', 'Reference Check'
        OFFER_EXTENDED = 'offer_extended', 'Offer Extended'
        OFFER_ACCEPTED = 'offer_accepted', 'Offer Accepted'
        OFFER_DECLINED = 'offer_declined', 'Offer Declined'
        HIRED = 'hired', 'Hired'
        REJECTED = 'rejected', 'Rejected'
        WITHDRAWN = 'withdrawn', 'Withdrawn'
    
    # Personal information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(validators=[EmailValidator()])
    phone = models.CharField(max_length=20)
    
    # Application details
    job = models.ForeignKey(
        JobPosting,
        on_delete=models.CASCADE,
        related_name='applicants'
    )
    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.WEBSITE
    )
    referrer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referred_applicants',
        help_text='Employee who referred this candidate'
    )
    
    # Documents and links
    resume = models.FileField(
        upload_to='resumes/%Y/%m/',
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'doc', 'docx']
        )]
    )
    cover_letter = models.FileField(
        upload_to='cover_letters/%Y/%m/',
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'doc', 'docx']
        )],
        blank=True,
        null=True
    )
    portfolio_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    
    # Status and pipeline
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW
    )
    stage_notes = models.TextField(blank=True)
    
    # Experience and qualifications
    years_of_experience = models.PositiveIntegerField(null=True, blank=True)
    current_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    expected_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    notice_period_days = models.PositiveIntegerField(null=True, blank=True)
    
    # Location and availability
    current_location = models.CharField(max_length=200, blank=True)
    willing_to_relocate = models.BooleanField(default=False)
    available_start_date = models.DateField(null=True, blank=True)
    
    # Screening questions responses
    screening_responses = models.JSONField(
        default=dict,
        blank=True,
        help_text='Responses to job-specific screening questions'
    )
    
    # Internal tracking
    assigned_recruiter = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_applicants',
        limit_choices_to={'role__in': ['hr_manager', 'hiring_manager', 'admin']}
    )
    internal_notes = models.TextField(blank=True)
    rating = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Rating from 1-10'
    )
    
    # Timestamps
    applied_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'applicants'
        verbose_name = 'Applicant'
        verbose_name_plural = 'Applicants'
        indexes = [
            models.Index(fields=['job', 'status']),
            models.Index(fields=['email']),
            models.Index(fields=['applied_at']),
            models.Index(fields=['assigned_recruiter']),
        ]
        unique_together = ['email', 'job']  # Prevent duplicate applications
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.job.title}"
    
    @property
    def full_name(self):
        """Return applicant's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def days_in_pipeline(self):
        """Calculate days since application."""
        if not self.applied_at:
            return 0
        return (timezone.now() - self.applied_at).days


class Interview(models.Model):
    """
    Interview scheduling and feedback model.
    """
    
    class Type(models.TextChoices):
        PHONE = 'phone', 'Phone Interview'
        VIDEO = 'video', 'Video Interview'
        ONSITE = 'onsite', 'Onsite Interview'
        PANEL = 'panel', 'Panel Interview'
        TECHNICAL = 'technical', 'Technical Interview'
        BEHAVIORAL = 'behavioral', 'Behavioral Interview'
        FINAL = 'final', 'Final Interview'
    
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        NO_SHOW = 'no_show', 'No Show'
        RESCHEDULED = 'rescheduled', 'Rescheduled'
    
    class Recommendation(models.TextChoices):
        STRONG_YES = 'strong_yes', 'Strong Yes'
        YES = 'yes', 'Yes'
        MAYBE = 'maybe', 'Maybe'
        NO = 'no', 'No'
        STRONG_NO = 'strong_no', 'Strong No'
    
    # Core interview details
    applicant = models.ForeignKey(
        Applicant,
        on_delete=models.CASCADE,
        related_name='interviews'
    )
    interviewer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='conducted_interviews'
    )
    additional_interviewers = models.ManyToManyField(
        User,
        blank=True,
        related_name='panel_interviews',
        help_text='Additional interviewers for panel interviews'
    )
    
    # Interview logistics
    interview_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.PHONE
    )
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    location = models.CharField(
        max_length=200,
        blank=True,
        help_text='Physical location or video call link'
    )
    
    # Status and outcomes
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED
    )
    
    # Feedback and evaluation
    technical_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Technical skills rating (1-10)'
    )
    communication_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Communication skills rating (1-10)'
    )
    cultural_fit_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Cultural fit rating (1-10)'
    )
    overall_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Overall rating (1-10)'
    )
    
    strengths = models.TextField(blank=True)
    weaknesses = models.TextField(blank=True)
    detailed_feedback = models.TextField(blank=True)
    recommendation = models.CharField(
        max_length=20,
        choices=Recommendation.choices,
        null=True,
        blank=True
    )
    
    # Interview preparation and notes
    preparation_notes = models.TextField(
        blank=True,
        help_text='Notes for interviewer preparation'
    )
    questions_asked = models.TextField(blank=True)
    
    # Administrative
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='scheduled_interviews'
    )
    is_final_round = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'interviews'
        verbose_name = 'Interview'
        verbose_name_plural = 'Interviews'
        indexes = [
            models.Index(fields=['applicant', 'status']),
            models.Index(fields=['interviewer', 'scheduled_date']),
            models.Index(fields=['scheduled_date', 'scheduled_time']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.applicant.full_name} - {self.interview_type} with {self.interviewer.get_full_name()}"
    
    @property
    def scheduled_datetime(self):
        """Return combined datetime for the interview."""
        if not self.scheduled_date or not self.scheduled_time:
            return None
        return timezone.datetime.combine(
            self.scheduled_date,
            self.scheduled_time
        )
    
    @property
    def is_upcoming(self):
        """Check if interview is scheduled for the future."""
        if not self.scheduled_datetime:
            return False
        return (
            self.status == self.Status.SCHEDULED and
            self.scheduled_datetime > timezone.now()
        )
    
    def save(self, *args, **kwargs):
        """Set completed_at when status changes to completed."""
        if self.status == self.Status.COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)


class JobOfferment(models.Model):
    """
    Job offer management for successful candidates.
    """
    
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        EXTENDED = 'extended', 'Extended'
        ACCEPTED = 'accepted', 'Accepted'
        DECLINED = 'declined', 'Declined'
        WITHDRAWN = 'withdrawn', 'Withdrawn'
        EXPIRED = 'expired', 'Expired'
    
    applicant = models.ForeignKey(
        Applicant,
        on_delete=models.CASCADE,
        related_name='offers'
    )
    job = models.ForeignKey(
        JobPosting,
        on_delete=models.CASCADE,
        related_name='offers'
    )
    
    # Offer details
    offered_salary = models.DecimalField(max_digits=10, decimal_places=2)
    signing_bonus = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    benefits_summary = models.TextField()
    start_date = models.DateField()
    
    # Status and timeline
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    offer_expiry_date = models.DateField()
    
    # Communication
    offer_letter = models.FileField(
        upload_to='offer_letters/%Y/%m/',
        null=True,
        blank=True
    )
    notes = models.TextField(blank=True)
    
    # Tracking
    extended_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='extended_offers'
    )
    extended_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'job_offers'
        verbose_name = 'Job Offer'
        verbose_name_plural = 'Job Offers'
        indexes = [
            models.Index(fields=['applicant', 'status']),
            models.Index(fields=['job']),
            models.Index(fields=['offer_expiry_date']),
        ]
    
    def __str__(self):
        return f"Offer for {self.applicant.full_name} - {self.job.title}"
    
    @property
    def is_expired(self):
        """Check if offer has expired."""
        if not self.offer_expiry_date:
            return False
        return timezone.now().date() > self.offer_expiry_date
    
    @property
    def days_until_expiry(self):
        """Calculate days until offer expires."""
        if not self.offer_expiry_date:
            return 0
        return (self.offer_expiry_date - timezone.now().date()).days


class PowerAppsConfiguration(models.Model):
    """
    Configuration for PowerApps form integration with DANI HRIS recruitment.
    
    This model stores settings for connecting PowerApps forms to the DANI recruitment
    system, including field mappings, authentication, and workflow settings.
    """
    
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        TESTING = 'testing', 'Testing'
    
    # Basic configuration
    name = models.CharField(
        max_length=100, 
        help_text="Configuration name for identification"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of this PowerApps integration"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.INACTIVE,
        help_text="Current status of this configuration"
    )
    
    # API connection details
    api_key = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        help_text="Unique API key for PowerApps authentication"
    )
    allowed_origins = models.JSONField(
        default=list,
        blank=True,
        help_text="Allowed origins for CORS (PowerApps URLs)"
    )
    
    # Form field mapping
    field_mapping = models.JSONField(
        default=dict,
        help_text="JSON mapping of PowerApps form fields to DANI applicant fields"
    )
    required_fields = models.JSONField(
        default=list,
        help_text="List of required PowerApps form fields"
    )
    
    # File handling
    resume_field_name = models.CharField(
        max_length=100,
        default='resume_file',
        help_text="PowerApps field name for resume upload"
    )
    cover_letter_field_name = models.CharField(
        max_length=100,
        default='cover_letter_file',
        blank=True,
        help_text="PowerApps field name for cover letter upload"
    )
    max_file_size_mb = models.PositiveIntegerField(
        default=10,
        help_text="Maximum file size in MB for uploaded files"
    )
    allowed_file_types = models.JSONField(
        default=list,
        help_text="Allowed file extensions (e.g., ['pdf', 'doc', 'docx'])"
    )
    
    # Job assignment
    auto_assign_to_job = models.ForeignKey(
        JobPosting,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Automatically assign applications to this job posting"
    )
    default_application_source = models.CharField(
        max_length=50,
        default='PowerApps Form',
        help_text="Default source to assign to applications from this form"
    )
    
    # Validation and security
    allowed_email_domains = models.JSONField(
        default=list,
        blank=True,
        help_text="Restrict applications to specific email domains"
    )
    require_email_verification = models.BooleanField(
        default=False,
        help_text="Require email verification before processing application"
    )
    enable_duplicate_detection = models.BooleanField(
        default=True,
        help_text="Prevent duplicate applications based on email and job"
    )
    
    # Workflow settings
    auto_send_confirmation = models.BooleanField(
        default=True,
        help_text="Automatically send confirmation email to applicants"
    )
    confirmation_email_template = models.TextField(
        blank=True,
        help_text="Custom email template for application confirmations"
    )
    notification_emails = models.JSONField(
        default=list,
        blank=True,
        help_text="Email addresses to notify when new applications arrive"
    )
    
    # Advanced settings
    rate_limit_per_hour = models.PositiveIntegerField(
        default=100,
        help_text="Maximum applications per hour from this configuration"
    )
    custom_validation_rules = models.JSONField(
        default=dict,
        blank=True,
        help_text="Custom validation rules for form data"
    )
    webhook_url = models.URLField(
        blank=True,
        help_text="Optional webhook URL to call after successful application submission"
    )
    
    # Tracking and analytics
    total_submissions = models.PositiveIntegerField(
        default=0,
        help_text="Total number of applications received through this configuration"
    )
    successful_submissions = models.PositiveIntegerField(
        default=0,
        help_text="Number of successfully processed applications"
    )
    last_submission_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date and time of last application submission"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_powerapps_configs',
        help_text="User who created this configuration"
    )
    
    class Meta:
        db_table = 'powerapps_configurations'
        verbose_name = 'PowerApps Configuration'
        verbose_name_plural = 'PowerApps Configurations'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['api_key']),
            models.Index(fields=['auto_assign_to_job']),
        ]
    
    def __str__(self):
        status_display = self.get_status_display()
        return f"PowerApps Config: {self.name} ({status_display})"
    
    @property
    def is_active(self):
        """Check if configuration is active."""
        return self.status == self.Status.ACTIVE
    
    @property
    def success_rate(self):
        """Calculate success rate percentage."""
        if self.total_submissions == 0:
            return 0
        return (self.successful_submissions / self.total_submissions) * 100
    
    def get_api_endpoint_url(self, request=None):
        """Get the full API endpoint URL for PowerApps integration."""
        if request:
            return request.build_absolute_uri(f'/api/recruitment/powerapps/{self.api_key}/')
        return f'/api/recruitment/powerapps/{self.api_key}/'
    
    def increment_submission_count(self, successful=True):
        """Increment submission counters."""
        self.total_submissions += 1
        if successful:
            self.successful_submissions += 1
        self.last_submission_date = timezone.now()
        self.save(update_fields=['total_submissions', 'successful_submissions', 'last_submission_date'])
    
    def validate_required_fields(self, form_data):
        """Validate that all required fields are present in form data."""
        missing_fields = []
        for field in self.required_fields:
            if field not in form_data or not form_data[field]:
                missing_fields.append(field)
        return missing_fields
    
    def transform_form_data(self, powerapps_data):
        """Transform PowerApps form data to DANI applicant format."""
        transformed_data = {}
        
        for powerapps_field, dani_field in self.field_mapping.items():
            if powerapps_field in powerapps_data:
                transformed_data[dani_field] = powerapps_data[powerapps_field]
        
        # Add default values
        if self.auto_assign_to_job:
            transformed_data['job'] = self.auto_assign_to_job.id
        
        transformed_data['source'] = self.default_application_source
        
        return transformed_data