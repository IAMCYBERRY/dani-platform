"""
Custom user manager for the HRIS platform.

This module provides a custom user manager that works with email-based authentication
instead of username-based authentication.
"""

from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import validate_email


class UserManager(BaseUserManager):
    """
    Custom user manager for User model with email as the unique identifier.
    """
    
    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given email and password.
        """
        if not email:
            raise ValueError('The Email field must be set')
        
        try:
            validate_email(email)
        except ValidationError:
            raise ValueError('Invalid email address')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a regular user with the given email and password.
        """
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('role', 'employee')
        
        return self._create_user(email, password, **extra_fields)
    
    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a superuser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self._create_user(email, password, **extra_fields)
    
    def create_hr_manager(self, email, password=None, **extra_fields):
        """
        Create and save an HR manager user.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('role', 'hr_manager')
        
        return self._create_user(email, password, **extra_fields)
    
    def create_hiring_manager(self, email, password=None, **extra_fields):
        """
        Create and save a hiring manager user.
        """
        extra_fields.setdefault('role', 'hiring_manager')
        
        return self._create_user(email, password, **extra_fields)
    
    def create_candidate(self, email, password=None, **extra_fields):
        """
        Create and save a candidate user.
        """
        extra_fields.setdefault('role', 'candidate')
        
        return self._create_user(email, password, **extra_fields)
    
    def get_by_natural_key(self, email):
        """
        Retrieve user by email (natural key).
        """
        return self.get(email__iexact=email)
    
    def active_users(self):
        """
        Return queryset of active users.
        """
        return self.filter(is_active=True)
    
    def by_role(self, role):
        """
        Return queryset of users by role.
        """
        return self.filter(role=role)
    
    def staff_users(self):
        """
        Return queryset of staff users (admins and HR managers).
        """
        return self.filter(role__in=['admin', 'hr_manager'])
    
    def managers(self):
        """
        Return queryset of all managers (HR and hiring managers).
        """
        return self.filter(role__in=['hr_manager', 'hiring_manager'])