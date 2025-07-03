"""
Serializers for user authentication and profile management.

This module contains Django REST Framework serializers for handling user-related
API operations including registration, authentication, and profile management.
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, UserSession


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'password', 'password_confirm',
            'phone_number', 'department', 'job_title', 'role'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, attrs):
        """
        Validate password confirmation and role permissions.
        """
        password = attrs.get('password')
        password_confirm = attrs.pop('password_confirm', None)
        
        if password != password_confirm:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        
        # Only admin users can create admin or HR manager accounts
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user_role = attrs.get('role', User.Role.EMPLOYEE)
            if user_role in [User.Role.ADMIN, User.Role.HR_MANAGER]:
                if not (request.user.is_authenticated and request.user.is_admin):
                    raise serializers.ValidationError({
                        'role': 'Only admin users can create admin or HR manager accounts.'
                    })
        
        return attrs
    
    def create(self, validated_data):
        """
        Create a new user with encrypted password.
        """
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information.
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'role_display', 'phone_number', 'profile_picture',
            'department', 'job_title', 'date_joined', 'last_login', 'is_active'
        ]
        read_only_fields = ['id', 'email', 'date_joined', 'last_login']
    
    def update(self, instance, validated_data):
        """
        Update user profile with role change restrictions.
        """
        request = self.context.get('request')
        
        # Only admin users can change roles
        if 'role' in validated_data:
            if not (request and request.user.is_authenticated and request.user.is_admin):
                validated_data.pop('role')
        
        # Users can only update their own profile unless they're admin/HR
        if request and request.user.is_authenticated:
            if instance != request.user and not request.user.has_permission('manage_employees'):
                raise serializers.ValidationError(
                    'You can only update your own profile.'
                )
        
        return super().update(instance, validated_data)


class UserListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for user listings.
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'role', 'role_display',
            'department', 'job_title', 'is_active'
        ]


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for password change.
    """
    old_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate_old_password(self, value):
        """
        Validate the old password.
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Invalid old password.')
        return value
    
    def validate(self, attrs):
        """
        Validate password confirmation.
        """
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')
        
        if new_password != new_password_confirm:
            raise serializers.ValidationError({
                'new_password_confirm': 'New passwords do not match.'
            })
        
        return attrs
    
    def save(self):
        """
        Save the new password.
        """
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        return user


class UserSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for user session tracking.
    """
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = UserSession
        fields = [
            'id', 'user_email', 'user_name', 'ip_address', 'user_agent',
            'created_at', 'last_activity', 'is_active'
        ]
        read_only_fields = ['id', 'created_at']


class LoginSerializer(serializers.Serializer):
    """
    Custom login serializer with email and password.
    """
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )
    
    def validate(self, attrs):
        """
        Validate login credentials.
        """
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    'Invalid email or password.',
                    code='authorization'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    'User account is disabled.',
                    code='authorization'
                )
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                'Must include email and password.',
                code='authorization'
            )