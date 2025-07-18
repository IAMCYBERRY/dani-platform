"""
Django admin configuration for employees app.
"""

from django.contrib import admin
from .models import JobTitle, Department, EmployeeProfile, PerformanceReview, TimeOffRequest


@admin.register(JobTitle)
class JobTitleAdmin(admin.ModelAdmin):
    list_display = ['title', 'department', 'level', 'salary_range_display', 'employee_count', 'is_active']
    list_filter = ['is_active', 'department', 'level']
    search_fields = ['title', 'description', 'required_skills']
    readonly_fields = ['employee_count', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'is_active')
        }),
        ('Organization', {
            'fields': ('department', 'level')
        }),
        ('Compensation', {
            'fields': ('min_salary', 'max_salary'),
            'classes': ('collapse',)
        }),
        ('Requirements', {
            'fields': ('required_skills',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('employee_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'manager', 'employee_count', 'is_active']
    list_filter = ['is_active', 'parent_department']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['employee_count', 'created_at', 'updated_at']


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = [
        'employee_id', 'user', 'department', 'job_title', 
        'employment_status', 'hire_date', 'is_active'
    ]
    list_filter = [
        'employment_status', 'employment_type', 'department', 
        'is_active', 'hire_date'
    ]
    search_fields = [
        'employee_id', 'user__first_name', 'user__last_name', 
        'user__email', 'job_title'
    ]
    readonly_fields = ['employee_id', 'tenure_days', 'created_at', 'updated_at']


@admin.register(PerformanceReview)
class PerformanceReviewAdmin(admin.ModelAdmin):
    list_display = [
        'employee', 'reviewer', 'review_type', 'overall_rating', 
        'review_period_end', 'is_final'
    ]
    list_filter = ['review_type', 'overall_rating', 'is_final']
    search_fields = [
        'employee__user__first_name', 'employee__user__last_name',
        'reviewer__first_name', 'reviewer__last_name'
    ]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TimeOffRequest)
class TimeOffRequestAdmin(admin.ModelAdmin):
    list_display = [
        'employee', 'request_type', 'start_date', 'end_date', 
        'total_days', 'status', 'approved_by'
    ]
    list_filter = ['request_type', 'status', 'start_date']
    search_fields = [
        'employee__user__first_name', 'employee__user__last_name',
        'reason'
    ]
    readonly_fields = ['total_days', 'created_at', 'updated_at']