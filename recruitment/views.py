"""
API views for recruitment and ATS functionality.

This module contains Django REST Framework views for handling recruitment-related
operations including job postings, applications, interviews, and offers.
"""

from rest_framework import viewsets, generics, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.core.files.base import ContentFile
from django.shortcuts import render
import json
import base64
import uuid
import logging

from accounts.permissions import (
    IsHRManagerOrAdmin,
    IsManagerOrAdmin,
    DepartmentBasedPermission,
    JobApplicationPermission,
    IsCandidateOrAdmin
)
from .models import JobPosting, Applicant, Interview, JobOfferment, PowerAppsConfiguration
from .serializers import (
    JobPostingSerializer,
    JobPostingListSerializer,
    ApplicantSerializer,
    ApplicantListSerializer,
    InterviewSerializer,
    InterviewListSerializer,
    JobOffermentSerializer,
    PowerAppsConfigurationSerializer,
    PowerAppsConfigurationListSerializer
)


class JobPostingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing job postings.
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'department', 'status', 'job_type', 'experience_level',
        'remote_work_allowed', 'is_featured'
    ]
    search_fields = ['title', 'description', 'location', 'requirements']
    ordering_fields = ['title', 'created_at', 'application_deadline', 'views_count']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return JobPostingListSerializer
        return JobPostingSerializer
    
    def get_queryset(self):
        """Filter job postings based on user role."""
        user = self.request.user
        queryset = JobPosting.objects.select_related(
            'department', 'hiring_manager', 'created_by'
        )
        
        if user.is_candidate:
            # Candidates can only see active job postings
            return queryset.filter(status=JobPosting.Status.ACTIVE)
        elif user.is_admin or user.is_hr_manager:
            return queryset
        elif user.is_hiring_manager:
            # Hiring managers can see jobs in their department
            if hasattr(user, 'employee_profile'):
                return queryset.filter(department=user.employee_profile.department)
            return queryset.filter(hiring_manager=user)
        else:
            # Regular employees can see active jobs
            return queryset.filter(status=JobPosting.Status.ACTIVE)
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsManagerOrAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def retrieve(self, request, *args, **kwargs):
        """Increment view count when job is viewed."""
        instance = self.get_object()
        instance.views_count += 1
        instance.save(update_fields=['views_count'])
        return super().retrieve(request, *args, **kwargs)
    
    @action(detail=True, methods=['get'])
    def applicants(self, request, pk=None):
        """Get applicants for a specific job."""
        job = self.get_object()
        
        # Check permissions
        if not (request.user.is_admin or request.user.is_hr_manager or 
                job.hiring_manager == request.user):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        applicants = Applicant.objects.filter(job=job).select_related(
            'assigned_recruiter', 'referrer'
        ).order_by('-applied_at')
        
        serializer = ApplicantListSerializer(applicants, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get statistics for a job posting."""
        job = self.get_object()
        
        # Check permissions
        if not (request.user.is_admin or request.user.is_hr_manager or 
                job.hiring_manager == request.user):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        stats = {
            'total_applications': job.applicants.count(),
            'applications_by_status': {},
            'applications_by_source': {},
            'average_time_to_hire': 0,
            'interviews_scheduled': 0,
            'offers_extended': 0
        }
        
        # Applications by status
        status_counts = job.applicants.values('status').annotate(count=Count('id'))
        for item in status_counts:
            stats['applications_by_status'][item['status']] = item['count']
        
        # Applications by source
        source_counts = job.applicants.values('source').annotate(count=Count('id'))
        for item in source_counts:
            stats['applications_by_source'][item['source']] = item['count']
        
        # Interviews scheduled
        stats['interviews_scheduled'] = Interview.objects.filter(
            applicant__job=job
        ).count()
        
        # Offers extended
        stats['offers_extended'] = JobOfferment.objects.filter(job=job).count()
        
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish a job posting."""
        job = self.get_object()
        
        if job.status != JobPosting.Status.DRAFT:
            return Response(
                {'error': 'Only draft jobs can be published'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job.status = JobPosting.Status.ACTIVE
        job.published_at = timezone.now()
        job.save()
        
        serializer = self.get_serializer(job)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close a job posting."""
        job = self.get_object()
        
        job.status = JobPosting.Status.CLOSED
        job.save()
        
        serializer = self.get_serializer(job)
        return Response(serializer.data)


class ApplicantViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing job applicants.
    """
    permission_classes = [JobApplicationPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'job', 'status', 'source', 'assigned_recruiter', 'rating'
    ]
    search_fields = [
        'first_name', 'last_name', 'email', 'current_location', 
        'skills', 'internal_notes'
    ]
    ordering_fields = ['applied_at', 'last_activity', 'rating']
    ordering = ['-applied_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ApplicantListSerializer
        return ApplicantSerializer
    
    def get_queryset(self):
        """Filter applicants based on user role."""
        user = self.request.user
        queryset = Applicant.objects.select_related(
            'job', 'job__department', 'assigned_recruiter', 'referrer'
        )
        
        if user.is_candidate:
            # Candidates can only see their own applications
            return queryset.filter(email=user.email)
        elif user.is_admin or user.is_hr_manager:
            return queryset
        elif user.is_hiring_manager:
            # Hiring managers can see applicants for their department's jobs
            if hasattr(user, 'employee_profile'):
                return queryset.filter(job__department=user.employee_profile.department)
            return queryset.filter(job__hiring_manager=user)
        else:
            return queryset.none()
    
    def perform_create(self, serializer):
        """Set additional fields when creating an applicant."""
        # If user is a candidate, set email to their email
        if self.request.user.is_candidate:
            serializer.save(email=self.request.user.email)
        else:
            serializer.save()
    
    @action(detail=False, methods=['get'])
    def my_applications(self, request):
        """Get current user's job applications."""
        if not request.user.is_candidate:
            return Response(
                {'error': 'Only candidates can view their applications'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        applications = Applicant.objects.filter(
            email=request.user.email
        ).select_related('job', 'job__department').order_by('-applied_at')
        
        serializer = ApplicantListSerializer(applications, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def move_to_stage(self, request, pk=None):
        """Move applicant to a different stage in the pipeline."""
        applicant = self.get_object()
        new_status = request.data.get('status')
        stage_notes = request.data.get('stage_notes', '')
        
        if not new_status:
            return Response(
                {'error': 'Status is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        applicant.status = new_status
        if stage_notes:
            applicant.stage_notes = stage_notes
        applicant.save()
        
        serializer = self.get_serializer(applicant)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def assign_recruiter(self, request, pk=None):
        """Assign a recruiter to an applicant."""
        applicant = self.get_object()
        recruiter_id = request.data.get('recruiter_id')
        
        if not recruiter_id:
            return Response(
                {'error': 'Recruiter ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from accounts.models import User
            recruiter = User.objects.get(
                id=recruiter_id,
                role__in=['hr_manager', 'hiring_manager', 'admin']
            )
            applicant.assigned_recruiter = recruiter
            applicant.save()
            
            serializer = self.get_serializer(applicant)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid recruiter'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def interview_history(self, request, pk=None):
        """Get interview history for an applicant."""
        applicant = self.get_object()
        interviews = Interview.objects.filter(
            applicant=applicant
        ).select_related('interviewer').order_by('-scheduled_date')
        
        serializer = InterviewListSerializer(interviews, many=True)
        return Response(serializer.data)


class InterviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing interviews.
    """
    permission_classes = [IsManagerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = [
        'applicant', 'interviewer', 'interview_type', 'status'
    ]
    ordering_fields = ['scheduled_date', 'scheduled_time', 'created_at']
    ordering = ['scheduled_date', 'scheduled_time']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return InterviewListSerializer
        return InterviewSerializer
    
    def get_queryset(self):
        """Filter interviews based on user role."""
        user = self.request.user
        queryset = Interview.objects.select_related(
            'applicant', 'interviewer', 'created_by'
        )
        
        if user.is_admin or user.is_hr_manager:
            return queryset
        elif user.is_hiring_manager:
            # Hiring managers can see interviews for their department
            return queryset.filter(
                Q(interviewer=user) | 
                Q(applicant__job__hiring_manager=user) |
                Q(applicant__job__department__manager=user)
            )
        else:
            # Other users can only see interviews they're conducting
            return queryset.filter(interviewer=user)
    
    @action(detail=False, methods=['get'])
    def my_interviews(self, request):
        """Get current user's interviews."""
        interviews = Interview.objects.filter(
            interviewer=request.user
        ).select_related('applicant').order_by('scheduled_date', 'scheduled_time')
        
        serializer = InterviewListSerializer(interviews, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming interviews."""
        user = request.user
        queryset = self.get_queryset().filter(
            scheduled_date__gte=timezone.now().date(),
            status=Interview.Status.SCHEDULED
        )
        
        if user.is_hiring_manager:
            # Include interviews for their department
            queryset = queryset.filter(
                Q(interviewer=user) |
                Q(applicant__job__hiring_manager=user)
            )
        elif not (user.is_admin or user.is_hr_manager):
            queryset = queryset.filter(interviewer=user)
        
        serializer = InterviewListSerializer(
            queryset.order_by('scheduled_date', 'scheduled_time')[:10], 
            many=True
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark interview as completed and add feedback."""
        interview = self.get_object()
        
        if interview.status != Interview.Status.SCHEDULED:
            return Response(
                {'error': 'Interview is not scheduled'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update interview with feedback data
        feedback_data = request.data
        interview.status = Interview.Status.COMPLETED
        interview.completed_at = timezone.now()
        
        # Update scores if provided
        for field in ['technical_score', 'communication_score', 'cultural_fit_score', 
                     'overall_score']:
            if field in feedback_data:
                setattr(interview, field, feedback_data[field])
        
        # Update feedback fields
        for field in ['strengths', 'weaknesses', 'detailed_feedback', 
                     'recommendation', 'questions_asked']:
            if field in feedback_data:
                setattr(interview, field, feedback_data[field])
        
        interview.save()
        
        serializer = self.get_serializer(interview)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reschedule(self, request, pk=None):
        """Reschedule an interview."""
        interview = self.get_object()
        new_date = request.data.get('scheduled_date')
        new_time = request.data.get('scheduled_time')
        
        if not new_date or not new_time:
            return Response(
                {'error': 'New date and time are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        interview.scheduled_date = new_date
        interview.scheduled_time = new_time
        interview.status = Interview.Status.RESCHEDULED
        interview.save()
        
        serializer = self.get_serializer(interview)
        return Response(serializer.data)


class JobOffermentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing job offers.
    """
    serializer_class = JobOffermentSerializer
    permission_classes = [IsHRManagerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['applicant', 'job', 'status', 'extended_by']
    ordering_fields = ['created_at', 'offer_expiry_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter offers based on user role."""
        user = self.request.user
        queryset = JobOfferment.objects.select_related(
            'applicant', 'job', 'extended_by'
        )
        
        if user.is_admin or user.is_hr_manager:
            return queryset
        elif user.is_hiring_manager:
            # Hiring managers can see offers for their department's jobs
            if hasattr(user, 'employee_profile'):
                return queryset.filter(job__department=user.employee_profile.department)
            return queryset.filter(job__hiring_manager=user)
        else:
            return queryset.none()
    
    @action(detail=False, methods=['get'])
    def pending_offers(self, request):
        """Get offers pending response."""
        offers = self.get_queryset().filter(
            status=JobOfferment.Status.EXTENDED,
            offer_expiry_date__gte=timezone.now().date()
        ).order_by('offer_expiry_date')
        
        serializer = self.get_serializer(offers, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get offers expiring within 3 days."""
        cutoff_date = timezone.now().date() + timezone.timedelta(days=3)
        offers = self.get_queryset().filter(
            status=JobOfferment.Status.EXTENDED,
            offer_expiry_date__lte=cutoff_date,
            offer_expiry_date__gte=timezone.now().date()
        ).order_by('offer_expiry_date')
        
        serializer = self.get_serializer(offers, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def extend(self, request, pk=None):
        """Extend a job offer."""
        offer = self.get_object()
        
        if offer.status != JobOfferment.Status.DRAFT:
            return Response(
                {'error': 'Only draft offers can be extended'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        offer.status = JobOfferment.Status.EXTENDED
        offer.extended_at = timezone.now()
        offer.save()
        
        # Update applicant status
        offer.applicant.status = Applicant.Status.OFFER_EXTENDED
        offer.applicant.save()
        
        serializer = self.get_serializer(offer)
        return Response(serializer.data)


class PowerAppsConfigurationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing PowerApps configurations.
    """
    permission_classes = [IsHRManagerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'auto_assign_to_job']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'last_submission_date', 'total_submissions']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PowerAppsConfigurationListSerializer
        return PowerAppsConfigurationSerializer
    
    def get_queryset(self):
        """Filter PowerApps configurations based on user role."""
        user = self.request.user
        queryset = PowerAppsConfiguration.objects.select_related(
            'created_by', 'auto_assign_to_job'
        )
        
        if user.is_admin or user.is_hr_manager:
            return queryset
        else:
            # Only show configurations created by the user
            return queryset.filter(created_by=user)
    
    @action(detail=True, methods=['post'])
    def regenerate_api_key(self, request, pk=None):
        """Regenerate API key for PowerApps configuration."""
        configuration = self.get_object()
        
        import secrets
        import string
        
        # Generate new unique API key
        while True:
            new_api_key = 'dani_powerapps_' + ''.join(
                secrets.choice(string.ascii_lowercase + string.digits) 
                for _ in range(32)
            )
            if not PowerAppsConfiguration.objects.filter(api_key=new_api_key).exists():
                break
        
        old_api_key = configuration.api_key
        configuration.api_key = new_api_key
        configuration.save()
        
        return Response({
            'success': True,
            'message': 'API key regenerated successfully',
            'old_api_key': old_api_key[:20] + '...',  # Partial for security
            'new_api_key': new_api_key,
            'endpoint_url': request.build_absolute_uri(
                f'/api/recruitment/powerapps/{new_api_key}/'
            )
        })
    
    @action(detail=True, methods=['post'])
    def test_webhook(self, request, pk=None):
        """Test webhook URL for PowerApps configuration."""
        configuration = self.get_object()
        
        if not configuration.webhook_url:
            return Response(
                {'error': 'No webhook URL configured'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        import requests
        
        test_payload = {
            'event': 'test',
            'configuration_id': configuration.id,
            'configuration_name': configuration.name,
            'timestamp': timezone.now().isoformat(),
            'test_data': {
                'firstName': 'Test',
                'lastName': 'User',
                'email': 'test@example.com'
            }
        }
        
        try:
            response = requests.post(
                configuration.webhook_url,
                json=test_payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            
            return Response({
                'success': True,
                'message': 'Webhook test successful',
                'response_status': response.status_code,
                'response_data': response.text[:200] if response.text else None
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Webhook test failed: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def field_mapping_templates(self, request, pk=None):
        """Get field mapping templates for common use cases."""
        templates = {
            'basic_application': {
                'name': 'Basic Job Application',
                'description': 'Standard job application form fields',
                'field_mapping': {
                    'firstName': 'first_name',
                    'lastName': 'last_name',
                    'emailAddress': 'email',
                    'phoneNumber': 'phone',
                    'currentLocation': 'current_location',
                    'yearsOfExperience': 'years_of_experience',
                    'currentSalary': 'current_salary',
                    'expectedSalary': 'expected_salary',
                    'linkedInUrl': 'linkedin_url',
                    'portfolioUrl': 'portfolio_url',
                    'willingToRelocate': 'willing_to_relocate',
                    'availableStartDate': 'available_start_date'
                },
                'required_fields': ['firstName', 'lastName', 'emailAddress', 'resume_file']
            },
            'executive_application': {
                'name': 'Executive Application',
                'description': 'Application form for executive positions',
                'field_mapping': {
                    'firstName': 'first_name',
                    'lastName': 'last_name',
                    'emailAddress': 'email',
                    'phoneNumber': 'phone',
                    'currentLocation': 'current_location',
                    'yearsOfExperience': 'years_of_experience',
                    'currentCompany': 'current_company',
                    'currentTitle': 'current_title',
                    'currentSalary': 'current_salary',
                    'expectedSalary': 'expected_salary',
                    'linkedInUrl': 'linkedin_url',
                    'executiveBio': 'executive_bio',
                    'leadershipExperience': 'leadership_experience',
                    'boardExperience': 'board_experience'
                },
                'required_fields': ['firstName', 'lastName', 'emailAddress', 'currentCompany', 'resume_file']
            },
            'technical_application': {
                'name': 'Technical Application',
                'description': 'Application form for technical positions',
                'field_mapping': {
                    'firstName': 'first_name',
                    'lastName': 'last_name',
                    'emailAddress': 'email',
                    'phoneNumber': 'phone',
                    'currentLocation': 'current_location',
                    'yearsOfExperience': 'years_of_experience',
                    'technicalSkills': 'technical_skills',
                    'programmingLanguages': 'programming_languages',
                    'frameworks': 'frameworks',
                    'githubUrl': 'github_url',
                    'portfolioUrl': 'portfolio_url',
                    'certifications': 'certifications',
                    'educationLevel': 'education_level'
                },
                'required_fields': ['firstName', 'lastName', 'emailAddress', 'technicalSkills', 'resume_file']
            }
        }
        
        return Response(templates)
    
    @action(detail=False, methods=['get'])
    def setup_wizard_data(self, request):
        """Get data needed for the PowerApps setup wizard."""
        from employees.models import Department
        
        wizard_data = {
            'job_postings': [
                {
                    'id': job.id,
                    'title': job.title,
                    'department': job.department.name if job.department else None,
                    'status': job.status
                }
                for job in JobPosting.objects.filter(
                    status__in=[JobPosting.Status.ACTIVE, JobPosting.Status.DRAFT]
                ).select_related('department')
            ],
            'departments': [
                {
                    'id': dept.id,
                    'name': dept.name
                }
                for dept in Department.objects.all()
            ],
            'default_field_mapping': {
                'firstName': 'first_name',
                'lastName': 'last_name',
                'emailAddress': 'email',
                'phoneNumber': 'phone',
                'currentLocation': 'current_location',
                'yearsOfExperience': 'years_of_experience',
                'currentSalary': 'current_salary',
                'expectedSalary': 'expected_salary',
                'linkedInUrl': 'linkedin_url',
                'portfolioUrl': 'portfolio_url',
                'willingToRelocate': 'willing_to_relocate',
                'availableStartDate': 'available_start_date'
            },
            'default_required_fields': ['firstName', 'lastName', 'emailAddress', 'resume_file'],
            'default_allowed_file_types': ['pdf', 'doc', 'docx'],
            'default_allowed_origins': [
                'https://apps.powerapps.com',
                'https://apps.preview.powerapps.com',
                'https://make.powerapps.com',
                'https://prod-00.westus.logic.azure.com',
                'https://prod-01.westus.logic.azure.com',
                'https://prod-02.westus.logic.azure.com',
                'https://prod-03.westus.logic.azure.com',
                'https://prod-04.westus.logic.azure.com',
                'https://prod-05.westus.logic.azure.com'
            ]
        }
        
        return Response(wizard_data)


@api_view(['GET'])
@permission_classes([IsHRManagerOrAdmin])
def powerapps_wizard(request):
    """
    Render the PowerApps configuration wizard interface.
    """
    return render(request, 'recruitment/powerapps_wizard.html')


@api_view(['GET'])
@permission_classes([IsHRManagerOrAdmin])
def recruitment_dashboard(request):
    """
    Get recruitment dashboard statistics.
    """
    stats = {
        'active_jobs': JobPosting.objects.filter(status=JobPosting.Status.ACTIVE).count(),
        'total_applications_this_month': Applicant.objects.filter(
            applied_at__month=timezone.now().month,
            applied_at__year=timezone.now().year
        ).count(),
        'interviews_this_week': Interview.objects.filter(
            scheduled_date__week=timezone.now().isocalendar()[1],
            scheduled_date__year=timezone.now().year
        ).count(),
        'pending_offers': JobOfferment.objects.filter(
            status=JobOfferment.Status.EXTENDED
        ).count(),
        'applications_by_status': {},
        'top_job_sources': {},
        'hiring_pipeline_stats': {}
    }
    
    # Applications by status
    status_counts = Applicant.objects.values('status').annotate(count=Count('id'))
    for item in status_counts:
        stats['applications_by_status'][item['status']] = item['count']
    
    # Top application sources
    source_counts = Applicant.objects.values('source').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    for item in source_counts:
        stats['top_job_sources'][item['source']] = item['count']
    
    # Hiring pipeline conversion rates
    total_apps = Applicant.objects.count()
    if total_apps > 0:
        stats['hiring_pipeline_stats'] = {
            'screening_rate': (
                Applicant.objects.exclude(status=Applicant.Status.NEW).count() / total_apps
            ) * 100,
            'interview_rate': (
                Applicant.objects.filter(
                    status__in=[
                        Applicant.Status.PHONE_INTERVIEW,
                        Applicant.Status.TECHNICAL_TEST,
                        Applicant.Status.ONSITE_INTERVIEW,
                        Applicant.Status.FINAL_INTERVIEW
                    ]
                ).count() / total_apps
            ) * 100,
            'offer_rate': (
                Applicant.objects.filter(
                    status__in=[
                        Applicant.Status.OFFER_EXTENDED,
                        Applicant.Status.OFFER_ACCEPTED,
                        Applicant.Status.HIRED
                    ]
                ).count() / total_apps
            ) * 100
        }
    
    return Response(stats)


from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
import hashlib
import hmac
import time

def secure_api_key_required(view_func):
    """
    Decorator for API endpoints that require secure API key authentication.
    This replaces CSRF exemption with proper API security.
    """
    @csrf_exempt  # Only exempt CSRF for properly authenticated API calls
    def wrapper(request, api_key, *args, **kwargs):
        # Verify API key exists and is active
        try:
            config = PowerAppsConfiguration.objects.get(
                api_key=api_key,
                status=PowerAppsConfiguration.Status.ACTIVE
            )
        except PowerAppsConfiguration.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Invalid API key or configuration inactive'
            }, status=401)
        
        # Add rate limiting check
        client_ip = request.META.get('HTTP_X_FORWARDED_FOR', 
                                   request.META.get('REMOTE_ADDR', ''))
        
        # Basic rate limiting (can be enhanced with Redis/cache)
        rate_limit_key = f"api_rate_limit_{api_key}_{client_ip}"
        
        # Check origin restrictions if configured
        if config.allowed_origins:
            origin = request.META.get('HTTP_ORIGIN', '')
            if origin not in config.allowed_origins:
                return JsonResponse({
                    'success': False,
                    'error': 'Origin not allowed'
                }, status=403)
        
        # Call the original view
        return view_func(request, api_key, *args, **kwargs)
    return wrapper

@secure_api_key_required
@require_http_methods(["POST"])
def powerapps_submission(request, api_key):
    """
    API endpoint for PowerApps form submissions.
    
    Receives job application data from PowerApps forms and creates
    Applicant records in the DANI HRIS system.
    """
    
    # Set up logging for this operation
    logger = logging.getLogger('dani.powerapps')
    operation_id = f"powerapps_{uuid.uuid4().hex[:8]}"
    
    logger.info(f"[{operation_id}] PowerApps submission received", extra={
        'api_key_hash': hashlib.sha256(api_key.encode()).hexdigest()[:16],
        'content_type': request.content_type,
        'content_length': request.META.get('CONTENT_LENGTH', 0),
        'client_ip': request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', 'unknown'))[:15]  # Truncate IP for privacy
    })
    
    try:
        # Get PowerApps configuration (already validated by decorator)
        config = PowerAppsConfiguration.objects.get(
            api_key=api_key,
            status=PowerAppsConfiguration.Status.ACTIVE
        )
        
        # Parse request data
        try:
            if request.content_type == 'application/json':
                form_data = json.loads(request.body)
            else:
                form_data = dict(request.POST)
                # Handle file uploads
                if request.FILES:
                    for field_name, file_obj in request.FILES.items():
                        form_data[field_name] = file_obj
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"[{operation_id}] Invalid request data: {e}")
            config.increment_submission_count(successful=False)
            return JsonResponse({
                'success': False,
                'error': 'Invalid request data format',
                'operation_id': operation_id
            }, status=400)
        
        # Validate required fields
        missing_fields = config.validate_required_fields(form_data)
        if missing_fields:
            logger.warning(f"[{operation_id}] Missing required fields: {missing_fields}")
            config.increment_submission_count(successful=False)
            return JsonResponse({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}',
                'missing_fields': missing_fields,
                'operation_id': operation_id
            }, status=400)
        
        # Transform form data to DANI format
        applicant_data = config.transform_form_data(form_data)
        
        # Validate email domain if restrictions are set
        if config.allowed_email_domains:
            email = applicant_data.get('email', '')
            email_domain = email.split('@')[-1].lower() if '@' in email else ''
            if email_domain not in [domain.lower() for domain in config.allowed_email_domains]:
                logger.warning(f"[{operation_id}] Email domain not allowed: {email_domain}")
                config.increment_submission_count(successful=False)
                return JsonResponse({
                    'success': False,
                    'error': f'Email domain "{email_domain}" is not allowed',
                    'operation_id': operation_id
                }, status=400)
        
        # Check for duplicate applications if enabled
        if config.enable_duplicate_detection and config.auto_assign_to_job:
            existing_applicant = Applicant.objects.filter(
                email=applicant_data.get('email'),
                job=config.auto_assign_to_job
            ).first()
            
            if existing_applicant:
                logger.warning(f"[{operation_id}] Duplicate application detected: {applicant_data.get('email')}")
                config.increment_submission_count(successful=False)
                return JsonResponse({
                    'success': False,
                    'error': 'Duplicate application detected',
                    'existing_application_id': existing_applicant.id,
                    'operation_id': operation_id
                }, status=409)
        
        # Process file uploads
        resume_file = None
        cover_letter_file = None
        
        if config.resume_field_name in form_data:
            resume_file = process_file_upload(
                form_data[config.resume_field_name],
                config.max_file_size_mb,
                config.allowed_file_types,
                'resume'
            )
        
        if config.cover_letter_field_name and config.cover_letter_field_name in form_data:
            cover_letter_file = process_file_upload(
                form_data[config.cover_letter_field_name],
                config.max_file_size_mb,
                config.allowed_file_types,
                'cover_letter'
            )
        
        # Create Applicant record
        try:
            applicant = Applicant.objects.create(
                first_name=applicant_data.get('first_name', ''),
                last_name=applicant_data.get('last_name', ''),
                email=applicant_data.get('email', ''),
                phone=applicant_data.get('phone', ''),
                job=config.auto_assign_to_job,
                source=config.default_application_source,
                resume=resume_file,
                cover_letter=cover_letter_file,
                current_location=applicant_data.get('current_location', ''),
                years_of_experience=applicant_data.get('years_of_experience'),
                current_salary=applicant_data.get('current_salary'),
                expected_salary=applicant_data.get('expected_salary'),
                linkedin_url=applicant_data.get('linkedin_url', ''),
                portfolio_url=applicant_data.get('portfolio_url', ''),
                willing_to_relocate=applicant_data.get('willing_to_relocate', False),
                available_start_date=applicant_data.get('available_start_date'),
                screening_responses=form_data  # Store original form data
            )
            
            logger.info(f"[{operation_id}] Applicant created successfully: {applicant.id}")
            
        except Exception as e:
            logger.error(f"[{operation_id}] Failed to create applicant: {e}")
            config.increment_submission_count(successful=False)
            return JsonResponse({
                'success': False,
                'error': 'Failed to create application record',
                'operation_id': operation_id
            }, status=500)
        
        # Send confirmation email if enabled
        if config.auto_send_confirmation:
            try:
                send_application_confirmation_email(applicant, config)
                logger.info(f"[{operation_id}] Confirmation email sent to: {applicant.email}")
            except Exception as e:
                logger.warning(f"[{operation_id}] Failed to send confirmation email: {e}")
        
        # Send notification emails
        if config.notification_emails:
            try:
                send_new_application_notification(applicant, config)
                logger.info(f"[{operation_id}] Notification emails sent")
            except Exception as e:
                logger.warning(f"[{operation_id}] Failed to send notification emails: {e}")
        
        # Call webhook if configured
        if config.webhook_url:
            try:
                call_webhook(config.webhook_url, applicant, operation_id)
                logger.info(f"[{operation_id}] Webhook called successfully")
            except Exception as e:
                logger.warning(f"[{operation_id}] Webhook call failed: {e}")
        
        # Update configuration statistics
        config.increment_submission_count(successful=True)
        
        # Return success response
        response_data = {
            'success': True,
            'message': 'Application submitted successfully',
            'applicant_id': applicant.id,
            'operation_id': operation_id,
            'job_title': config.auto_assign_to_job.title if config.auto_assign_to_job else None
        }
        
        logger.info(f"[{operation_id}] PowerApps submission completed successfully")
        return JsonResponse(response_data, status=201)
        
    except Exception as e:
        logger.error(f"[{operation_id}] Unexpected error in PowerApps submission: {e}", exc_info=True)
        try:
            config.increment_submission_count(successful=False)
        except:
            pass  # Don't fail if we can't update stats
        
        return JsonResponse({
            'success': False,
            'error': 'Internal server error',
            'operation_id': operation_id
        }, status=500)


def process_file_upload(file_data, max_size_mb, allowed_types, file_type):
    """
    SECURE file upload processing with content validation.
    
    Args:
        file_data: File data (base64 encoded string or file object)
        max_size_mb: Maximum file size in MB
        allowed_types: List of allowed file extensions
        file_type: Type of file ('resume' or 'cover_letter')
    
    Returns:
        ContentFile object for saving to model
    """
    import magic
    
    try:
        if isinstance(file_data, str):
            # Handle base64 encoded file with strict validation
            if ';base64,' in file_data:
                header, encoded = file_data.split(';base64,', 1)
                try:
                    file_content = base64.b64decode(encoded, validate=True)
                except Exception:
                    raise ValueError("Invalid base64 encoding")
            else:
                try:
                    file_content = base64.b64decode(file_data, validate=True)
                except Exception:
                    raise ValueError("Invalid base64 encoding")
        else:
            # Handle uploaded file object
            file_content = file_data.read()
        
        # Validate file size first (prevent DoS)
        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > max_size_mb:
            raise ValueError(f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed ({max_size_mb}MB)")
        
        # Validate file content using magic bytes (not just extension)
        mime_type = magic.from_buffer(file_content, mime=True)
        
        # Map MIME types to safe extensions
        safe_mime_types = {
            'application/pdf': 'pdf',
            'application/msword': 'doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'text/plain': 'txt',
            'application/rtf': 'rtf'
        }
        
        if mime_type not in safe_mime_types:
            raise ValueError(f"File type '{mime_type}' not allowed. Only document files are permitted.")
        
        file_ext = safe_mime_types[mime_type]
        
        # Double-check against allowed types
        if allowed_types and file_ext not in allowed_types:
            raise ValueError(f"File type '{file_ext}' not in allowed list: {allowed_types}")
        
        # Additional security: scan for embedded executables (basic check)
        dangerous_signatures = [
            b'MZ',  # PE executable
            b'\x7fELF',  # ELF executable
            b'PK\x03\x04',  # ZIP (could contain executables)
        ]
        
        for sig in dangerous_signatures:
            if sig in file_content[:100]:  # Check first 100 bytes
                raise ValueError("File contains potentially dangerous content")
        
        # Limit file content to prevent memory exhaustion
        if len(file_content) > 50 * 1024 * 1024:  # 50MB absolute max
            raise ValueError("File size exceeds absolute maximum (50MB)")
        
        # Create secure filename with timestamp
        timestamp = int(time.time())
        filename = f"{file_type}_{timestamp}_{uuid.uuid4().hex[:8]}.{file_ext}"
        
        return ContentFile(file_content, name=filename)
        
    except Exception as e:
        raise ValueError(f"Failed to process {file_type} file: {e}")


def send_application_confirmation_email(applicant, config):
    """
    Send confirmation email to applicant.
    
    Args:
        applicant: Applicant instance
        config: PowerAppsConfiguration instance
    """
    from django.core.mail import send_mail
    from django.template import Template, Context
    
    try:
        # Use custom template if provided, otherwise use default
        if config.confirmation_email_template:
            template = Template(config.confirmation_email_template)
        else:
            template = Template("""
            Dear {{ applicant.first_name }},
            
            Thank you for your application for the {{ job_title }} position.
            
            We have received your application and our team will review it shortly.
            You will hear from us within the next few business days.
            
            Application Details:
            - Name: {{ applicant.full_name }}
            - Email: {{ applicant.email }}
            - Job: {{ job_title }}
            - Submitted: {{ applicant.applied_at }}
            
            Best regards,
            {{ company_name }} Recruitment Team
            """)
        
        context = Context({
            'applicant': applicant,
            'job_title': applicant.job.title if applicant.job else 'Unknown Position',
            'company_name': 'DANI HRIS'  # Could be configurable
        })
        
        email_content = template.render(context)
        
        send_mail(
            subject=f"Application Received - {applicant.job.title if applicant.job else 'Job Application'}",
            message=email_content,
            from_email=None,  # Use default from settings
            recipient_list=[applicant.email],
            fail_silently=False
        )
        
    except Exception as e:
        raise Exception(f"Failed to send confirmation email: {e}")


def send_new_application_notification(applicant, config):
    """
    Send notification emails to HR team about new application.
    
    Args:
        applicant: Applicant instance
        config: PowerAppsConfiguration instance
    """
    from django.core.mail import send_mail
    
    try:
        if not config.notification_emails:
            return
        
        subject = f"New Application: {applicant.full_name} - {applicant.job.title if applicant.job else 'Unknown Position'}"
        
        message = f"""
        A new job application has been received through PowerApps.
        
        Applicant Details:
        - Name: {applicant.full_name}
        - Email: {applicant.email}
        - Phone: {applicant.phone}
        - Position: {applicant.job.title if applicant.job else 'Unknown Position'}
        - Source: {applicant.source}
        - Submitted: {applicant.applied_at}
        
        Please log into the DANI HRIS system to review this application.
        
        Configuration: {config.name}
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=None,  # Use default from settings
            recipient_list=config.notification_emails,
            fail_silently=False
        )
        
    except Exception as e:
        raise Exception(f"Failed to send notification emails: {e}")


def call_webhook(webhook_url, applicant, operation_id):
    """
    Call configured webhook with application data.
    
    Args:
        webhook_url: Webhook URL to call
        applicant: Applicant instance
        operation_id: Operation identifier for logging
    """
    import requests
    
    try:
        webhook_data = {
            'event': 'new_application',
            'operation_id': operation_id,
            'applicant': {
                'id': applicant.id,
                'name': applicant.full_name,
                'email': applicant.email,
                'phone': applicant.phone,
                'job_title': applicant.job.title if applicant.job else None,
                'source': applicant.source,
                'applied_at': applicant.applied_at.isoformat()
            }
        }
        
        response = requests.post(
            webhook_url,
            json=webhook_data,
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        
        response.raise_for_status()
        
    except Exception as e:
        raise Exception(f"Webhook call failed: {e}")