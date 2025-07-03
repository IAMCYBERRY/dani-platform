"""
Custom permissions for role-based access control.

This module defines permission classes that work with the User model's role system
to provide fine-grained access control throughout the HRIS platform.
"""

from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Permission class that allows access only to admin users.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_admin
        )


class IsHRManagerOrAdmin(permissions.BasePermission):
    """
    Permission class that allows access to HR managers and admin users.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_hr_manager or request.user.is_admin)
        )


class IsManagerOrAdmin(permissions.BasePermission):
    """
    Permission class that allows access to any manager role or admin.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_hiring_manager or 
             request.user.is_hr_manager or 
             request.user.is_admin)
        )


class IsOwnerOrManagerOrAdmin(permissions.BasePermission):
    """
    Permission class that allows users to access their own data,
    or managers/admins to access any data.
    """
    
    def has_object_permission(self, request, view, obj):
        # Check if the object has a user field (for user-owned resources)
        if hasattr(obj, 'user'):
            return (
                obj.user == request.user or
                request.user.is_hr_manager or
                request.user.is_admin
            )
        
        # Check if the object is a User instance
        if hasattr(obj, 'email'):  # User model check
            return (
                obj == request.user or
                request.user.is_hr_manager or
                request.user.is_admin
            )
        
        # Default to admin-only access for other objects
        return request.user.is_admin


class IsCandidateOrAdmin(permissions.BasePermission):
    """
    Permission class for candidate-specific access.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_candidate or 
             request.user.is_hr_manager or 
             request.user.is_admin)
        )


class DepartmentBasedPermission(permissions.BasePermission):
    """
    Permission class that allows hiring managers to access only their department's data.
    HR managers and admins have access to all departments.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            not request.user.is_candidate
        )
    
    def has_object_permission(self, request, view, obj):
        # Admin and HR managers have access to everything
        if request.user.is_admin or request.user.is_hr_manager:
            return True
        
        # Hiring managers can only access their department's data
        if request.user.is_hiring_manager:
            # Check if object has a department field
            if hasattr(obj, 'department'):
                return obj.department == request.user.department
            
            # Check if object is related to a user with department
            if hasattr(obj, 'user') and hasattr(obj.user, 'department'):
                return obj.user.department == request.user.department
            
            # Check if object has an employee field with department
            if hasattr(obj, 'employee') and hasattr(obj.employee, 'department'):
                return obj.employee.department == request.user.department
        
        # Employees can only access their own data
        if request.user.is_employee:
            if hasattr(obj, 'user'):
                return obj.user == request.user
            if hasattr(obj, 'email'):  # User model
                return obj == request.user
        
        return False


class ReadOnlyOrManagerPermission(permissions.BasePermission):
    """
    Permission class that allows read-only access to all authenticated users,
    but write access only to managers and admins.
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Read permissions for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for managers and admins
        return (
            request.user.is_hiring_manager or 
            request.user.is_hr_manager or 
            request.user.is_admin
        )


class JobApplicationPermission(permissions.BasePermission):
    """
    Custom permission for job applications.
    - Candidates can create and view their own applications
    - Managers can view applications for their department's jobs
    - HR managers and admins can view all applications
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admin and HR managers have full access
        if request.user.is_admin or request.user.is_hr_manager:
            return True
        
        # Candidates can only access their own applications
        if request.user.is_candidate:
            return hasattr(obj, 'candidate') and obj.candidate == request.user
        
        # Hiring managers can access applications for their department's jobs
        if request.user.is_hiring_manager:
            if hasattr(obj, 'job') and hasattr(obj.job, 'department'):
                return obj.job.department == request.user.department
        
        return False