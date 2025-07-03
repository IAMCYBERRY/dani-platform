"""
Django REST Framework serializers for recruitment and ATS functionality.

This module contains serializers for handling recruitment-related API operations
including job postings, applications, interviews, and offers.
"""

from rest_framework import serializers
from django.utils import timezone
from django.utils.text import slugify
from .models import JobPosting, Applicant, Interview, JobOfferment


class JobPostingSerializer(serializers.ModelSerializer):
    """
    Serializer for JobPosting model.
    """
    department_name = serializers.CharField(source='department.name', read_only=True)
    hiring_manager_name = serializers.CharField(
        source='hiring_manager.get_full_name', 
        read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name', 
        read_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    job_type_display = serializers.CharField(source='get_job_type_display', read_only=True)
    experience_level_display = serializers.CharField(
        source='get_experience_level_display', 
        read_only=True
    )
    is_active = serializers.ReadOnlyField()
    days_since_posted = serializers.ReadOnlyField()
    
    class Meta:
        model = JobPosting
        fields = [
            'id', 'title', 'slug', 'description', 'requirements', 'responsibilities',
            'department', 'department_name', 'hiring_manager', 'hiring_manager_name',
            'created_by', 'created_by_name', 'job_type', 'job_type_display',
            'experience_level', 'experience_level_display', 'location',
            'remote_work_allowed', 'salary_min', 'salary_max', 'benefits',
            'status', 'status_display', 'application_deadline', 'expected_start_date',
            'is_featured', 'external_job_board_url', 'views_count', 'applications_count',
            'is_active', 'days_since_posted', 'created_at', 'updated_at', 'published_at'
        ]
        read_only_fields = [
            'id', 'slug', 'views_count', 'applications_count', 'is_active',
            'days_since_posted', 'created_at', 'updated_at', 'published_at'
        ]
    
    def validate(self, attrs):
        """Validate job posting data."""
        salary_min = attrs.get('salary_min')
        salary_max = attrs.get('salary_max')
        application_deadline = attrs.get('application_deadline')
        expected_start_date = attrs.get('expected_start_date')
        
        # Validate salary range
        if salary_min and salary_max and salary_min > salary_max:
            raise serializers.ValidationError({
                'salary_max': 'Maximum salary must be greater than or equal to minimum salary.'
            })
        
        # Validate application deadline
        if application_deadline and application_deadline <= timezone.now().date():
            raise serializers.ValidationError({
                'application_deadline': 'Application deadline must be in the future.'
            })
        
        # Validate expected start date
        if expected_start_date and expected_start_date <= timezone.now().date():
            raise serializers.ValidationError({
                'expected_start_date': 'Expected start date must be in the future.'
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create job posting with auto-generated slug."""
        title = validated_data['title']
        validated_data['slug'] = slugify(title)
        
        # Ensure unique slug
        base_slug = validated_data['slug']
        counter = 1
        while JobPosting.objects.filter(slug=validated_data['slug']).exists():
            validated_data['slug'] = f"{base_slug}-{counter}"
            counter += 1
        
        # Set created_by from request user
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        
        return super().create(validated_data)


class JobPostingListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for job posting listings.
    """
    department_name = serializers.CharField(source='department.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    job_type_display = serializers.CharField(source='get_job_type_display', read_only=True)
    is_active = serializers.ReadOnlyField()
    
    class Meta:
        model = JobPosting
        fields = [
            'id', 'title', 'slug', 'department_name', 'location',
            'job_type', 'job_type_display', 'status', 'status_display',
            'applications_count', 'is_active', 'application_deadline',
            'created_at'
        ]


class ApplicantSerializer(serializers.ModelSerializer):
    """
    Serializer for Applicant model.
    """
    job_title = serializers.CharField(source='job.title', read_only=True)
    job_department = serializers.CharField(source='job.department.name', read_only=True)
    full_name = serializers.ReadOnlyField()
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    referrer_name = serializers.CharField(
        source='referrer.get_full_name', 
        read_only=True
    )
    assigned_recruiter_name = serializers.CharField(
        source='assigned_recruiter.get_full_name', 
        read_only=True
    )
    days_in_pipeline = serializers.ReadOnlyField()
    
    class Meta:
        model = Applicant
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'email', 'phone',
            'job', 'job_title', 'job_department', 'source', 'source_display',
            'referrer', 'referrer_name', 'resume', 'cover_letter', 'portfolio_url',
            'linkedin_url', 'status', 'status_display', 'stage_notes',
            'years_of_experience', 'current_salary', 'expected_salary',
            'notice_period_days', 'current_location', 'willing_to_relocate',
            'available_start_date', 'screening_responses', 'assigned_recruiter',
            'assigned_recruiter_name', 'internal_notes', 'rating',
            'days_in_pipeline', 'applied_at', 'last_activity'
        ]
        read_only_fields = [
            'id', 'full_name', 'days_in_pipeline', 'applied_at', 'last_activity'
        ]
    
    def validate_email(self, value):
        """Validate unique email per job."""
        job = self.initial_data.get('job')
        if job:
            if Applicant.objects.filter(email=value, job=job).exists():
                raise serializers.ValidationError(
                    'An application for this job with this email already exists.'
                )
        return value
    
    def validate(self, attrs):
        """Validate applicant data."""
        expected_salary = attrs.get('expected_salary')
        current_salary = attrs.get('current_salary')
        available_start_date = attrs.get('available_start_date')
        
        # Validate salary expectations
        if (expected_salary and current_salary and 
            expected_salary < current_salary * 0.8):
            raise serializers.ValidationError({
                'expected_salary': 'Expected salary seems unusually low compared to current salary.'
            })
        
        # Validate start date
        if (available_start_date and 
            available_start_date < timezone.now().date()):
            raise serializers.ValidationError({
                'available_start_date': 'Available start date cannot be in the past.'
            })
        
        return attrs


class ApplicantListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for applicant listings.
    """
    full_name = serializers.ReadOnlyField()
    job_title = serializers.CharField(source='job.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    assigned_recruiter_name = serializers.CharField(
        source='assigned_recruiter.get_full_name', 
        read_only=True
    )
    
    class Meta:
        model = Applicant
        fields = [
            'id', 'full_name', 'email', 'job_title', 'status', 'status_display',
            'rating', 'assigned_recruiter_name', 'applied_at'
        ]


class InterviewSerializer(serializers.ModelSerializer):
    """
    Serializer for Interview model.
    """
    applicant_name = serializers.CharField(
        source='applicant.full_name', 
        read_only=True
    )
    interviewer_name = serializers.CharField(
        source='interviewer.get_full_name', 
        read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name', 
        read_only=True
    )
    interview_type_display = serializers.CharField(
        source='get_interview_type_display', 
        read_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    recommendation_display = serializers.CharField(
        source='get_recommendation_display', 
        read_only=True
    )
    scheduled_datetime = serializers.ReadOnlyField()
    is_upcoming = serializers.ReadOnlyField()
    
    class Meta:
        model = Interview
        fields = [
            'id', 'applicant', 'applicant_name', 'interviewer', 'interviewer_name',
            'additional_interviewers', 'interview_type', 'interview_type_display',
            'scheduled_date', 'scheduled_time', 'scheduled_datetime', 'duration_minutes',
            'location', 'status', 'status_display', 'technical_score',
            'communication_score', 'cultural_fit_score', 'overall_score',
            'strengths', 'weaknesses', 'detailed_feedback', 'recommendation',
            'recommendation_display', 'preparation_notes', 'questions_asked',
            'created_by', 'created_by_name', 'is_final_round', 'is_upcoming',
            'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'scheduled_datetime', 'is_upcoming', 'created_at', 
            'updated_at', 'completed_at'
        ]
    
    def validate(self, attrs):
        """Validate interview scheduling."""
        scheduled_date = attrs.get('scheduled_date')
        scheduled_time = attrs.get('scheduled_time')
        applicant = attrs.get('applicant')
        interviewer = attrs.get('interviewer')
        
        # Validate interview is in the future
        if scheduled_date and scheduled_time:
            scheduled_datetime = timezone.datetime.combine(scheduled_date, scheduled_time)
            if scheduled_datetime <= timezone.now():
                raise serializers.ValidationError({
                    'scheduled_time': 'Interview must be scheduled for the future.'
                })
        
        # Check for interviewer availability
        if scheduled_date and scheduled_time and interviewer:
            conflicting_interviews = Interview.objects.filter(
                interviewer=interviewer,
                scheduled_date=scheduled_date,
                scheduled_time=scheduled_time,
                status__in=[Interview.Status.SCHEDULED, Interview.Status.IN_PROGRESS]
            )
            
            if self.instance:
                conflicting_interviews = conflicting_interviews.exclude(id=self.instance.id)
            
            if conflicting_interviews.exists():
                raise serializers.ValidationError({
                    'scheduled_time': 'Interviewer has a conflicting interview at this time.'
                })
        
        return attrs
    
    def create(self, validated_data):
        """Create interview with created_by from request user."""
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        
        return super().create(validated_data)


class InterviewListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for interview listings.
    """
    applicant_name = serializers.CharField(
        source='applicant.full_name', 
        read_only=True
    )
    interviewer_name = serializers.CharField(
        source='interviewer.get_full_name', 
        read_only=True
    )
    interview_type_display = serializers.CharField(
        source='get_interview_type_display', 
        read_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Interview
        fields = [
            'id', 'applicant_name', 'interviewer_name', 'interview_type',
            'interview_type_display', 'scheduled_date', 'scheduled_time',
            'status', 'status_display', 'overall_score', 'recommendation'
        ]


class JobOffermentSerializer(serializers.ModelSerializer):
    """
    Serializer for JobOfferment model.
    """
    applicant_name = serializers.CharField(
        source='applicant.full_name', 
        read_only=True
    )
    job_title = serializers.CharField(source='job.title', read_only=True)
    extended_by_name = serializers.CharField(
        source='extended_by.get_full_name', 
        read_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_expired = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()
    
    class Meta:
        model = JobOfferment
        fields = [
            'id', 'applicant', 'applicant_name', 'job', 'job_title',
            'offered_salary', 'signing_bonus', 'benefits_summary', 'start_date',
            'status', 'status_display', 'offer_expiry_date', 'offer_letter',
            'notes', 'extended_by', 'extended_by_name', 'extended_at',
            'responded_at', 'is_expired', 'days_until_expiry',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'extended_by', 'extended_at', 'responded_at', 'is_expired',
            'days_until_expiry', 'created_at', 'updated_at'
        ]
    
    def validate(self, attrs):
        """Validate job offer data."""
        offer_expiry_date = attrs.get('offer_expiry_date')
        start_date = attrs.get('start_date')
        
        # Validate expiry date
        if offer_expiry_date and offer_expiry_date <= timezone.now().date():
            raise serializers.ValidationError({
                'offer_expiry_date': 'Offer expiry date must be in the future.'
            })
        
        # Validate start date
        if start_date and start_date <= timezone.now().date():
            raise serializers.ValidationError({
                'start_date': 'Start date must be in the future.'
            })
        
        # Validate start date after expiry
        if (offer_expiry_date and start_date and 
            start_date <= offer_expiry_date):
            raise serializers.ValidationError({
                'start_date': 'Start date should be after offer expiry date.'
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create offer with extended_by from request user."""
        request = self.context.get('request')
        if request and request.user:
            validated_data['extended_by'] = request.user
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Handle status updates with timestamp tracking."""
        new_status = validated_data.get('status')
        
        if new_status and new_status != instance.status:
            if new_status == JobOfferment.Status.EXTENDED and not instance.extended_at:
                instance.extended_at = timezone.now()
            elif new_status in [JobOfferment.Status.ACCEPTED, JobOfferment.Status.DECLINED]:
                instance.responded_at = timezone.now()
        
        return super().update(instance, validated_data)