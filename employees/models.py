"""
Employee management models for HRIS functionality.

This module contains models for managing employee profiles, organizational structure,
and HR-related information beyond basic user authentication.
"""

from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator, EmailValidator
from accounts.models import User


class JobTitle(models.Model):
    """
    Job title model for standardized position management.
    """
    title = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, help_text='Job description and responsibilities')
    department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_titles',
        help_text='Primary department for this job title'
    )
    level = models.CharField(
        max_length=50,
        blank=True,
        help_text='Job level (e.g., Entry, Mid, Senior, Lead, Manager)'
    )
    min_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Minimum salary range for this position'
    )
    max_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Maximum salary range for this position'
    )
    required_skills = models.TextField(
        blank=True,
        help_text='Comma-separated list of required skills'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'job_titles'
        verbose_name = 'Job Title'
        verbose_name_plural = 'Job Titles'
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['department', 'is_active']),
            models.Index(fields=['level']),
        ]
        ordering = ['title']
    
    def __str__(self):
        return self.title
    
    @property
    def employee_count(self):
        """Return the number of employees with this job title."""
        return self.employees.filter(is_active=True).count()
    
    @property
    def salary_range_display(self):
        """Display salary range as a formatted string."""
        if self.min_salary and self.max_salary:
            return f"${self.min_salary:,.0f} - ${self.max_salary:,.0f}"
        elif self.min_salary:
            return f"${self.min_salary:,.0f}+"
        elif self.max_salary:
            return f"Up to ${self.max_salary:,.0f}"
        return "Not specified"


class Department(models.Model):
    """
    Department model for organizational structure.
    """
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(
        max_length=10,
        unique=True,
        validators=[RegexValidator(
            regex=r'^[A-Z0-9]+$',
            message='Department code must contain only uppercase letters and numbers'
        )]
    )
    description = models.TextField(blank=True)
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments',
        limit_choices_to={'role__in': ['hr_manager', 'hiring_manager', 'admin']}
    )
    parent_department = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sub_departments'
    )
    budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'departments'
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    @property
    def employee_count(self):
        """Return the number of employees in this department."""
        return self.employees.filter(is_active=True).count()


class EmployeeProfile(models.Model):
    """
    Extended employee profile with HR-specific information.
    """
    
    class EmploymentStatus(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        TERMINATED = 'terminated', 'Terminated'
        ON_LEAVE = 'on_leave', 'On Leave'
        PROBATION = 'probation', 'Probation'
    
    class EmploymentType(models.TextChoices):
        FULL_TIME = 'full_time', 'Full Time'
        PART_TIME = 'part_time', 'Part Time'
        CONTRACT = 'contract', 'Contract'
        TEMPORARY = 'temporary', 'Temporary'
        INTERN = 'intern', 'Intern'
    
    # Link to user account
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='employee_profile'
    )
    
    # Employment information
    employee_id = models.CharField(
        max_length=20,
        unique=True,
        validators=[RegexValidator(
            regex=r'^EMP\d{4,}$',
            message='Employee ID must start with EMP followed by at least 4 digits'
        )]
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='employees'
    )
    job_title = models.ForeignKey(
        JobTitle,
        on_delete=models.PROTECT,
        related_name='employees',
        null=True,
        blank=True,
        help_text='Employee job title/position'
    )
    job_title_old = models.CharField(max_length=100, blank=True, null=True, help_text='Temporary field for migration')
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='direct_reports',
        limit_choices_to={'role__in': ['hiring_manager', 'hr_manager', 'admin']}
    )
    
    # Employment details
    employment_status = models.CharField(
        max_length=20,
        choices=EmploymentStatus.choices,
        default=EmploymentStatus.ACTIVE
    )
    employment_type = models.CharField(
        max_length=20,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME
    )
    hire_date = models.DateField()
    termination_date = models.DateField(null=True, blank=True)
    probation_end_date = models.DateField(null=True, blank=True)
    
    # Compensation
    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Annual salary in base currency'
    )
    hourly_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Hourly rate for part-time/contract employees'
    )
    
    # Contact and personal information
    work_phone = models.CharField(max_length=20, blank=True)
    work_location = models.CharField(max_length=200, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)
    
    # Professional information
    skills = models.TextField(
        blank=True,
        help_text='Comma-separated list of skills'
    )
    certifications = models.TextField(
        blank=True,
        help_text='Professional certifications and qualifications'
    )
    education = models.TextField(
        blank=True,
        help_text='Educational background'
    )
    
    # Administrative
    notes = models.TextField(blank=True, help_text='Internal HR notes')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Azure AD sync tracking for employee-specific data
    azure_ad_group_memberships = models.TextField(
        blank=True,
        help_text='JSON list of Azure AD group memberships for this employee'
    )
    azure_ad_manager_sync_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('synced', 'Synced'),
            ('failed', 'Failed'),
            ('not_applicable', 'Not Applicable'),
        ],
        default='pending',
        help_text='Status of manager relationship sync with Azure AD'
    )
    azure_ad_department_sync_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('synced', 'Synced'),
            ('failed', 'Failed'),
            ('not_applicable', 'Not Applicable'),
        ],
        default='pending',
        help_text='Status of department sync with Azure AD'
    )
    
    class Meta:
        db_table = 'employee_profiles'
        verbose_name = 'Employee Profile'
        verbose_name_plural = 'Employee Profiles'
        indexes = [
            models.Index(fields=['employee_id']),
            models.Index(fields=['department', 'is_active']),
            models.Index(fields=['employment_status']),
            models.Index(fields=['hire_date']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"
    
    @property
    def tenure_days(self):
        """Calculate employee tenure in days."""
        end_date = self.termination_date or timezone.now().date()
        return (end_date - self.hire_date).days
    
    @property
    def is_on_probation(self):
        """Check if employee is currently on probation."""
        if not self.probation_end_date:
            return False
        return timezone.now().date() <= self.probation_end_date
    
    def save(self, *args, **kwargs):
        """Override save to auto-generate employee ID if not provided."""
        if not self.employee_id:
            # Generate employee ID based on department and sequence
            last_emp = EmployeeProfile.objects.filter(
                employee_id__startswith='EMP'
            ).order_by('-employee_id').first()
            
            if last_emp:
                last_num = int(last_emp.employee_id[3:])
                new_num = last_num + 1
            else:
                new_num = 1001
            
            self.employee_id = f"EMP{new_num:04d}"
        
        super().save(*args, **kwargs)


class PerformanceReview(models.Model):
    """
    Employee performance review tracking.
    """
    
    class ReviewType(models.TextChoices):
        ANNUAL = 'annual', 'Annual Review'
        QUARTERLY = 'quarterly', 'Quarterly Review'
        PROBATION = 'probation', 'Probation Review'
        PROJECT = 'project', 'Project Review'
        EXIT = 'exit', 'Exit Review'
    
    class Rating(models.TextChoices):
        OUTSTANDING = 'outstanding', 'Outstanding'
        EXCEEDS = 'exceeds', 'Exceeds Expectations'
        MEETS = 'meets', 'Meets Expectations'
        BELOW = 'below', 'Below Expectations'
        UNSATISFACTORY = 'unsatisfactory', 'Unsatisfactory'
    
    employee = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.CASCADE,
        related_name='performance_reviews'
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='conducted_reviews'
    )
    review_period_start = models.DateField()
    review_period_end = models.DateField()
    review_type = models.CharField(
        max_length=20,
        choices=ReviewType.choices,
        default=ReviewType.ANNUAL
    )
    overall_rating = models.CharField(
        max_length=20,
        choices=Rating.choices,
        null=True,
        blank=True
    )
    goals_achieved = models.TextField(blank=True)
    areas_of_improvement = models.TextField(blank=True)
    goals_next_period = models.TextField(blank=True)
    additional_comments = models.TextField(blank=True)
    employee_comments = models.TextField(blank=True)
    is_final = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'performance_reviews'
        verbose_name = 'Performance Review'
        verbose_name_plural = 'Performance Reviews'
        indexes = [
            models.Index(fields=['employee', 'review_period_end']),
            models.Index(fields=['review_type']),
            models.Index(fields=['is_final']),
        ]
    
    def __str__(self):
        return f"{self.employee.user.get_full_name()} - {self.review_type} ({self.review_period_end})"


class TimeOffRequest(models.Model):
    """
    Employee time-off request management.
    """
    
    class RequestType(models.TextChoices):
        VACATION = 'vacation', 'Vacation'
        SICK = 'sick', 'Sick Leave'
        PERSONAL = 'personal', 'Personal Leave'
        MATERNITY = 'maternity', 'Maternity Leave'
        PATERNITY = 'paternity', 'Paternity Leave'
        BEREAVEMENT = 'bereavement', 'Bereavement Leave'
        JURY_DUTY = 'jury_duty', 'Jury Duty'
        OTHER = 'other', 'Other'
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        DENIED = 'denied', 'Denied'
        CANCELLED = 'cancelled', 'Cancelled'
    
    employee = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.CASCADE,
        related_name='time_off_requests'
    )
    request_type = models.CharField(
        max_length=20,
        choices=RequestType.choices
    )
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.PositiveIntegerField()
    reason = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_time_off_requests'
    )
    approval_date = models.DateTimeField(null=True, blank=True)
    denial_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'time_off_requests'
        verbose_name = 'Time Off Request'
        verbose_name_plural = 'Time Off Requests'
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.employee.user.get_full_name()} - {self.request_type} ({self.start_date} to {self.end_date})"
    
    def save(self, *args, **kwargs):
        """Calculate total days when saving."""
        if self.start_date and self.end_date:
            self.total_days = (self.end_date - self.start_date).days + 1
        super().save(*args, **kwargs)