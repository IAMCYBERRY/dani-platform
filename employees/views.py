"""
API views for employee management functionality.

This module contains Django REST Framework views for handling employee-related
operations including profiles, departments, performance reviews, and time-off requests.
"""

from rest_framework import viewsets, generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from accounts.permissions import (
    IsHRManagerOrAdmin,
    IsManagerOrAdmin,
    IsOwnerOrManagerOrAdmin,
    DepartmentBasedPermission
)
from .models import Department, EmployeeProfile, PerformanceReview, TimeOffRequest
from .serializers import (
    DepartmentSerializer,
    DepartmentListSerializer,
    EmployeeProfileSerializer,
    EmployeeListSerializer,
    PerformanceReviewSerializer,
    TimeOffRequestSerializer,
    TimeOffRequestListSerializer
)


class DepartmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing departments.
    """
    queryset = Department.objects.all()
    permission_classes = [IsHRManagerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'manager', 'parent_department']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return DepartmentListSerializer
        return DepartmentSerializer
    
    def get_queryset(self):
        """Filter departments based on user role."""
        user = self.request.user
        queryset = Department.objects.select_related('manager', 'parent_department')
        
        if user.is_admin or user.is_hr_manager:
            return queryset
        elif user.is_hiring_manager:
            # Hiring managers can see their own department and sub-departments
            return queryset.filter(
                Q(manager=user) | 
                Q(parent_department__manager=user)
            )
        else:
            # Employees can only see their own department
            if hasattr(user, 'employee_profile'):
                return queryset.filter(id=user.employee_profile.department.id)
            return queryset.none()
    
    @action(detail=True, methods=['get'])
    def employees(self, request, pk=None):
        """Get employees in a specific department."""
        department = self.get_object()
        employees = EmployeeProfile.objects.filter(
            department=department,
            is_active=True
        ).select_related('user', 'manager')
        
        serializer = EmployeeListSerializer(employees, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get department statistics."""
        department = self.get_object()
        
        stats = {
            'total_employees': department.employees.filter(is_active=True).count(),
            'employment_status_breakdown': {},
            'average_tenure_days': 0,
            'pending_time_off_requests': 0
        }
        
        # Employment status breakdown
        status_counts = department.employees.values('employment_status').annotate(
            count=Count('id')
        )
        for item in status_counts:
            stats['employment_status_breakdown'][item['employment_status']] = item['count']
        
        # Average tenure
        avg_tenure = department.employees.filter(is_active=True).aggregate(
            avg_tenure=Avg('tenure_days')
        )
        stats['average_tenure_days'] = avg_tenure['avg_tenure'] or 0
        
        # Pending time-off requests
        stats['pending_time_off_requests'] = TimeOffRequest.objects.filter(
            employee__department=department,
            status=TimeOffRequest.Status.PENDING
        ).count()
        
        return Response(stats)


class EmployeeProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing employee profiles.
    """
    permission_classes = [permissions.IsAuthenticated, DepartmentBasedPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'department', 'employment_status', 'employment_type', 
        'manager', 'is_active'
    ]
    search_fields = [
        'user__first_name', 'user__last_name', 'user__email',
        'employee_id', 'job_title', 'skills'
    ]
    ordering_fields = [
        'user__first_name', 'user__last_name', 'hire_date', 
        'employee_id', 'job_title'
    ]
    ordering = ['user__first_name', 'user__last_name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return EmployeeListSerializer
        return EmployeeProfileSerializer
    
    def get_queryset(self):
        """Filter employees based on user role and department."""
        user = self.request.user
        queryset = EmployeeProfile.objects.select_related(
            'user', 'department', 'manager'
        )
        
        if user.is_admin or user.is_hr_manager:
            return queryset
        elif user.is_hiring_manager:
            # Hiring managers can see employees in their department
            if hasattr(user, 'employee_profile'):
                return queryset.filter(department=user.employee_profile.department)
            return queryset.none()
        else:
            # Employees can only see their own profile
            if hasattr(user, 'employee_profile'):
                return queryset.filter(id=user.employee_profile.id)
            return queryset.none()
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's employee profile."""
        if hasattr(request.user, 'employee_profile'):
            serializer = self.get_serializer(request.user.employee_profile)
            return Response(serializer.data)
        return Response(
            {'error': 'No employee profile found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    @action(detail=True, methods=['get'])
    def direct_reports(self, request, pk=None):
        """Get direct reports for a manager."""
        employee = self.get_object()
        if not (employee.user.is_hiring_manager or employee.user.is_hr_manager):
            return Response(
                {'error': 'Employee is not a manager'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reports = EmployeeProfile.objects.filter(
            manager=employee.user,
            is_active=True
        ).select_related('user', 'department')
        
        serializer = EmployeeListSerializer(reports, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def performance_history(self, request, pk=None):
        """Get performance review history for an employee."""
        employee = self.get_object()
        reviews = PerformanceReview.objects.filter(
            employee=employee
        ).select_related('reviewer').order_by('-review_period_end')
        
        serializer = PerformanceReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def time_off_summary(self, request, pk=None):
        """Get time-off summary for an employee."""
        employee = self.get_object()
        current_year = timezone.now().year
        
        time_off_data = {
            'current_year_requests': TimeOffRequest.objects.filter(
                employee=employee,
                start_date__year=current_year
            ).count(),
            'approved_days_current_year': sum([
                req.total_days for req in TimeOffRequest.objects.filter(
                    employee=employee,
                    start_date__year=current_year,
                    status=TimeOffRequest.Status.APPROVED
                )
            ]),
            'pending_requests': TimeOffRequest.objects.filter(
                employee=employee,
                status=TimeOffRequest.Status.PENDING
            ).count(),
            'upcoming_time_off': TimeOffRequest.objects.filter(
                employee=employee,
                status=TimeOffRequest.Status.APPROVED,
                start_date__gte=timezone.now().date()
            ).order_by('start_date')[:5]
        }
        
        return Response(time_off_data)


class PerformanceReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing performance reviews.
    """
    serializer_class = PerformanceReviewSerializer
    permission_classes = [IsManagerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['employee', 'reviewer', 'review_type', 'is_final']
    ordering_fields = ['review_period_end', 'created_at']
    ordering = ['-review_period_end']
    
    def get_queryset(self):
        """Filter reviews based on user role."""
        user = self.request.user
        queryset = PerformanceReview.objects.select_related(
            'employee__user', 'reviewer'
        )
        
        if user.is_admin or user.is_hr_manager:
            return queryset
        elif user.is_hiring_manager:
            # Hiring managers can see reviews for their direct reports
            return queryset.filter(
                Q(employee__manager=user) | Q(reviewer=user)
            )
        else:
            # Employees can see their own reviews
            if hasattr(user, 'employee_profile'):
                return queryset.filter(employee=user.employee_profile)
            return queryset.none()
    
    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        """Get current user's performance reviews."""
        if hasattr(request.user, 'employee_profile'):
            reviews = PerformanceReview.objects.filter(
                employee=request.user.employee_profile
            ).select_related('reviewer').order_by('-review_period_end')
            
            serializer = self.get_serializer(reviews, many=True)
            return Response(serializer.data)
        
        return Response(
            {'error': 'No employee profile found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    @action(detail=False, methods=['get'])
    def pending_reviews(self, request):
        """Get pending reviews that need to be completed."""
        user = request.user
        if not (user.is_hiring_manager or user.is_hr_manager or user.is_admin):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Find employees who need reviews (hired > 90 days ago, no recent review)
        cutoff_date = timezone.now().date() - timezone.timedelta(days=90)
        recent_review_cutoff = timezone.now().date() - timezone.timedelta(days=365)
        
        employees_needing_review = EmployeeProfile.objects.filter(
            hire_date__lte=cutoff_date,
            is_active=True
        ).exclude(
            performance_reviews__review_period_end__gte=recent_review_cutoff
        )
        
        if user.is_hiring_manager:
            employees_needing_review = employees_needing_review.filter(
                manager=user
            )
        
        data = []
        for employee in employees_needing_review:
            data.append({
                'employee_id': employee.id,
                'employee_name': employee.user.get_full_name(),
                'department': employee.department.name,
                'hire_date': employee.hire_date,
                'days_since_last_review': (
                    timezone.now().date() - 
                    (employee.performance_reviews.order_by('-review_period_end').first().review_period_end
                     if employee.performance_reviews.exists() else employee.hire_date)
                ).days
            })
        
        return Response(data)


class TimeOffRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing time-off requests.
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['employee', 'request_type', 'status']
    ordering_fields = ['start_date', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TimeOffRequestListSerializer
        return TimeOffRequestSerializer
    
    def get_queryset(self):
        """Filter time-off requests based on user role."""
        user = self.request.user
        queryset = TimeOffRequest.objects.select_related(
            'employee__user', 'approved_by'
        )
        
        if user.is_admin or user.is_hr_manager:
            return queryset
        elif user.is_hiring_manager:
            # Hiring managers can see requests from their direct reports
            return queryset.filter(employee__manager=user)
        else:
            # Employees can see only their own requests
            if hasattr(user, 'employee_profile'):
                return queryset.filter(employee=user.employee_profile)
            return queryset.none()
    
    def perform_create(self, serializer):
        """Set employee to current user's profile when creating."""
        if hasattr(self.request.user, 'employee_profile'):
            serializer.save(employee=self.request.user.employee_profile)
        else:
            raise serializers.ValidationError(
                'Only employees can create time-off requests'
            )
    
    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        """Get current user's time-off requests."""
        if hasattr(request.user, 'employee_profile'):
            requests = TimeOffRequest.objects.filter(
                employee=request.user.employee_profile
            ).order_by('-created_at')
            
            serializer = self.get_serializer(requests, many=True)
            return Response(serializer.data)
        
        return Response(
            {'error': 'No employee profile found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    @action(detail=False, methods=['get'])
    def pending_approvals(self, request):
        """Get time-off requests pending approval."""
        user = request.user
        if not (user.is_hiring_manager or user.is_hr_manager or user.is_admin):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = TimeOffRequest.objects.filter(
            status=TimeOffRequest.Status.PENDING
        ).select_related('employee__user')
        
        if user.is_hiring_manager:
            queryset = queryset.filter(employee__manager=user)
        
        serializer = TimeOffRequestListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a time-off request."""
        time_off_request = self.get_object()
        
        if not (request.user.is_hr_manager or request.user.is_admin or
                time_off_request.employee.manager == request.user):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if time_off_request.status != TimeOffRequest.Status.PENDING:
            return Response(
                {'error': 'Request is not pending approval'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        time_off_request.status = TimeOffRequest.Status.APPROVED
        time_off_request.approved_by = request.user
        time_off_request.approval_date = timezone.now()
        time_off_request.save()
        
        serializer = self.get_serializer(time_off_request)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def deny(self, request, pk=None):
        """Deny a time-off request."""
        time_off_request = self.get_object()
        
        if not (request.user.is_hr_manager or request.user.is_admin or
                time_off_request.employee.manager == request.user):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if time_off_request.status != TimeOffRequest.Status.PENDING:
            return Response(
                {'error': 'Request is not pending approval'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        denial_reason = request.data.get('denial_reason', '')
        
        time_off_request.status = TimeOffRequest.Status.DENIED
        time_off_request.approved_by = request.user
        time_off_request.approval_date = timezone.now()
        time_off_request.denial_reason = denial_reason
        time_off_request.save()
        
        serializer = self.get_serializer(time_off_request)
        return Response(serializer.data)