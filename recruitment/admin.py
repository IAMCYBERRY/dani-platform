"""
Django admin configuration for recruitment app.
"""

from django.contrib import admin
from .models import JobPosting, Applicant, Interview, JobOfferment


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
        'slug', 'views_count', 'applications_count', 'created_at', 
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