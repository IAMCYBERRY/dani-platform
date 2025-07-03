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

from accounts.permissions import (
    IsHRManagerOrAdmin,
    IsManagerOrAdmin,
    DepartmentBasedPermission,
    JobApplicationPermission,
    IsCandidateOrAdmin
)
from .models import JobPosting, Applicant, Interview, JobOfferment
from .serializers import (
    JobPostingSerializer,
    JobPostingListSerializer,
    ApplicantSerializer,
    ApplicantListSerializer,
    InterviewSerializer,
    InterviewListSerializer,
    JobOffermentSerializer
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