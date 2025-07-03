"""
Django REST Framework serializers for employee management.

This module contains serializers for handling employee-related API operations
including profiles, departments, performance reviews, and time-off requests.
"""

from rest_framework import serializers
from django.utils import timezone
from accounts.serializers import UserListSerializer
from .models import Department, EmployeeProfile, PerformanceReview, TimeOffRequest


class DepartmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Department model.
    """
    manager_name = serializers.CharField(source='manager.get_full_name', read_only=True)
    employee_count = serializers.ReadOnlyField()
    parent_department_name = serializers.CharField(
        source='parent_department.name', 
        read_only=True
    )
    
    class Meta:
        model = Department
        fields = [
            'id', 'name', 'code', 'description', 'manager', 'manager_name',
            'parent_department', 'parent_department_name', 'budget',
            'employee_count', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'employee_count']
    
    def validate_code(self, value):
        """Validate department code format."""
        if not value.isupper():
            raise serializers.ValidationError(
                'Department code must be uppercase.'
            )
        return value


class DepartmentListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for department listings.
    """
    manager_name = serializers.CharField(source='manager.get_full_name', read_only=True)
    employee_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Department
        fields = [
            'id', 'name', 'code', 'manager_name', 'employee_count', 'is_active'
        ]


class EmployeeProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for EmployeeProfile model.
    """
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    manager_name = serializers.CharField(source='manager.get_full_name', read_only=True)
    tenure_days = serializers.ReadOnlyField()
    is_on_probation = serializers.ReadOnlyField()
    
    class Meta:
        model = EmployeeProfile
        fields = [
            'id', 'user', 'user_email', 'user_name', 'employee_id',
            'department', 'department_name', 'job_title', 'manager', 'manager_name',
            'employment_status', 'employment_type', 'hire_date', 'termination_date',
            'probation_end_date', 'salary', 'hourly_rate', 'work_phone',
            'work_location', 'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relationship', 'skills', 'certifications',
            'education', 'notes', 'tenure_days', 'is_on_probation',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'employee_id', 'tenure_days', 'is_on_probation',
            'created_at', 'updated_at'
        ]
    
    def validate(self, attrs):
        """Validate employment dates and manager assignment."""
        hire_date = attrs.get('hire_date')
        termination_date = attrs.get('termination_date')
        probation_end_date = attrs.get('probation_end_date')
        
        # Validate date logic
        if termination_date and hire_date and termination_date <= hire_date:
            raise serializers.ValidationError({
                'termination_date': 'Termination date must be after hire date.'
            })
        
        if probation_end_date and hire_date and probation_end_date <= hire_date:
            raise serializers.ValidationError({
                'probation_end_date': 'Probation end date must be after hire date.'
            })
        
        # Validate manager assignment (manager should be in same or parent department)
        manager = attrs.get('manager')
        department = attrs.get('department')
        if manager and department:
            if not (manager.is_hr_manager or manager.is_admin or 
                   manager.employee_profile.department == department or
                   manager.employee_profile.department == department.parent_department):
                raise serializers.ValidationError({
                    'manager': 'Manager must be in the same department, parent department, or be an HR manager/admin.'
                })
        
        return attrs


class EmployeeListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for employee listings.
    """
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    employment_status_display = serializers.CharField(
        source='get_employment_status_display', 
        read_only=True
    )
    
    class Meta:
        model = EmployeeProfile
        fields = [
            'id', 'employee_id', 'user_name', 'user_email', 'job_title',
            'department_name', 'employment_status', 'employment_status_display',
            'hire_date', 'is_active'
        ]


class PerformanceReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for PerformanceReview model.
    """
    employee_name = serializers.CharField(
        source='employee.user.get_full_name', 
        read_only=True
    )
    reviewer_name = serializers.CharField(
        source='reviewer.get_full_name', 
        read_only=True
    )
    review_type_display = serializers.CharField(
        source='get_review_type_display', 
        read_only=True
    )
    overall_rating_display = serializers.CharField(
        source='get_overall_rating_display', 
        read_only=True
    )
    
    class Meta:
        model = PerformanceReview
        fields = [
            'id', 'employee', 'employee_name', 'reviewer', 'reviewer_name',
            'review_period_start', 'review_period_end', 'review_type',
            'review_type_display', 'overall_rating', 'overall_rating_display',
            'goals_achieved', 'areas_of_improvement', 'goals_next_period',
            'additional_comments', 'employee_comments', 'is_final',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        """Validate review period dates."""
        start_date = attrs.get('review_period_start')
        end_date = attrs.get('review_period_end')
        
        if start_date and end_date and end_date <= start_date:
            raise serializers.ValidationError({
                'review_period_end': 'Review period end date must be after start date.'
            })
        
        # Validate reviewer has permission to review this employee
        employee = attrs.get('employee')
        reviewer = attrs.get('reviewer')
        request = self.context.get('request')
        
        if request and reviewer and employee:
            if not (reviewer.is_admin or reviewer.is_hr_manager or
                   employee.manager == reviewer):
                raise serializers.ValidationError({
                    'reviewer': 'Reviewer must be the employee\'s manager, HR manager, or admin.'
                })
        
        return attrs


class TimeOffRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for TimeOffRequest model.
    """
    employee_name = serializers.CharField(
        source='employee.user.get_full_name', 
        read_only=True
    )
    request_type_display = serializers.CharField(
        source='get_request_type_display', 
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', 
        read_only=True
    )
    approved_by_name = serializers.CharField(
        source='approved_by.get_full_name', 
        read_only=True
    )
    
    class Meta:
        model = TimeOffRequest
        fields = [
            'id', 'employee', 'employee_name', 'request_type',
            'request_type_display', 'start_date', 'end_date', 'total_days',
            'reason', 'status', 'status_display', 'approved_by',
            'approved_by_name', 'approval_date', 'denial_reason',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'total_days', 'approved_by', 'approval_date',
            'created_at', 'updated_at'
        ]
    
    def validate(self, attrs):
        """Validate time-off request dates."""
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        if start_date and end_date:
            if end_date < start_date:
                raise serializers.ValidationError({
                    'end_date': 'End date must be after or equal to start date.'
                })
            
            # Validate start date is not in the past (except for sick leave)
            request_type = attrs.get('request_type')
            if (request_type != TimeOffRequest.RequestType.SICK and 
                start_date < timezone.now().date()):
                raise serializers.ValidationError({
                    'start_date': 'Start date cannot be in the past except for sick leave.'
                })
        
        return attrs
    
    def update(self, instance, validated_data):
        """Handle status updates with approval tracking."""
        new_status = validated_data.get('status')
        request = self.context.get('request')
        
        if new_status and new_status != instance.status:
            if new_status == TimeOffRequest.Status.APPROVED:
                instance.approved_by = request.user
                instance.approval_date = timezone.now()
            elif new_status == TimeOffRequest.Status.DENIED:
                instance.approved_by = request.user
                instance.approval_date = timezone.now()
        
        return super().update(instance, validated_data)


class TimeOffRequestListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for time-off request listings.
    """
    employee_name = serializers.CharField(
        source='employee.user.get_full_name', 
        read_only=True
    )
    request_type_display = serializers.CharField(
        source='get_request_type_display', 
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', 
        read_only=True
    )
    
    class Meta:
        model = TimeOffRequest
        fields = [
            'id', 'employee_name', 'request_type_display', 'start_date',
            'end_date', 'total_days', 'status', 'status_display', 'created_at'
        ]