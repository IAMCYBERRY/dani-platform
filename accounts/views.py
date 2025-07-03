"""
Authentication and user management API views.

This module contains Django REST Framework views for handling user authentication,
registration, profile management, and role-based operations.
"""

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import User, UserSession
from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    UserListSerializer,
    PasswordChangeSerializer,
    UserSessionSerializer,
    LoginSerializer
)
from .permissions import (
    IsAdminUser,
    IsHRManagerOrAdmin,
    IsOwnerOrManagerOrAdmin
)


class UserRegistrationView(generics.CreateAPIView):
    """
    API view for user registration.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]  # Allow public registration
    
    def create(self, request, *args, **kwargs):
        """
        Create a new user account.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save()
        
        # Generate JWT tokens for the new user
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    Custom login view with session tracking.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        Authenticate user and return JWT tokens.
        """
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Create user session record
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        ip_address = self.get_client_ip(request)
        
        UserSession.objects.create(
            user=user,
            session_key=request.session.session_key or '',
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Login successful'
        })
    
    def get_client_ip(self, request):
        """
        Get the client's IP address from the request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API view for retrieving and updating user profiles.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManagerOrAdmin]
    
    def get_object(self):
        """
        Return the user object. If 'me' is used, return current user.
        """
        pk = self.kwargs.get('pk')
        if pk == 'me':
            return self.request.user
        return generics.get_object_or_404(User, pk=pk)


class UserListView(generics.ListAPIView):
    """
    API view for listing users with filtering and search.
    """
    serializer_class = UserListSerializer
    permission_classes = [IsHRManagerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'department', 'is_active']
    search_fields = ['first_name', 'last_name', 'email', 'department']
    ordering_fields = ['first_name', 'last_name', 'email', 'date_joined']
    ordering = ['first_name', 'last_name']
    
    def get_queryset(self):
        """
        Return queryset based on user role.
        """
        user = self.request.user
        
        if user.is_admin or user.is_hr_manager:
            # Admin and HR managers can see all users
            return User.objects.all()
        elif user.is_hiring_manager:
            # Hiring managers can see users in their department
            return User.objects.filter(department=user.department)
        else:
            # Regular employees can only see basic info of colleagues
            return User.objects.filter(is_active=True).exclude(role='candidate')


class PasswordChangeView(APIView):
    """
    API view for changing user password.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Change user password.
        """
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Password changed successfully'
        })


class UserDeactivateView(APIView):
    """
    API view for deactivating user accounts.
    """
    permission_classes = [IsAdminUser]
    
    def post(self, request, pk):
        """
        Deactivate a user account.
        """
        user = generics.get_object_or_404(User, pk=pk)
        
        if user.is_admin and User.objects.filter(role=User.Role.ADMIN, is_active=True).count() <= 1:
            return Response({
                'error': 'Cannot deactivate the last admin user'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.is_active = False
        user.save()
        
        return Response({
            'message': f'User {user.email} has been deactivated'
        })


class UserReactivateView(APIView):
    """
    API view for reactivating user accounts.
    """
    permission_classes = [IsAdminUser]
    
    def post(self, request, pk):
        """
        Reactivate a user account.
        """
        user = generics.get_object_or_404(User, pk=pk)
        user.is_active = True
        user.save()
        
        return Response({
            'message': f'User {user.email} has been reactivated'
        })


class UserSessionListView(generics.ListAPIView):
    """
    API view for listing user sessions.
    """
    serializer_class = UserSessionSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user', 'is_active']
    ordering = ['-last_activity']
    
    def get_queryset(self):
        """
        Return sessions, optionally filtered by user.
        """
        queryset = UserSession.objects.select_related('user')
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset


class MySessionsView(generics.ListAPIView):
    """
    API view for users to see their own sessions.
    """
    serializer_class = UserSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Return current user's sessions.
        """
        return UserSession.objects.filter(
            user=self.request.user,
            is_active=True
        ).order_by('-last_activity')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """
    Logout view that invalidates the current session.
    """
    # Mark session as inactive
    session_key = request.session.session_key
    if session_key:
        UserSession.objects.filter(
            user=request.user,
            session_key=session_key
        ).update(is_active=False)
    
    return Response({
        'message': 'Logout successful'
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_stats_view(request):
    """
    Get user statistics for dashboard.
    """
    if not (request.user.is_admin or request.user.is_hr_manager):
        return Response({
            'error': 'Permission denied'
        }, status=status.HTTP_403_FORBIDDEN)
    
    stats = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'users_by_role': {
            role[0]: User.objects.filter(role=role[0]).count()
            for role in User.Role.choices
        },
        'new_users_this_month': User.objects.filter(
            date_joined__month=timezone.now().month,
            date_joined__year=timezone.now().year
        ).count()
    }
    
    return Response(stats)