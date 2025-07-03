"""
URL configuration for accounts app.

This module defines the URL patterns for user authentication and management endpoints.
"""

from django.urls import path
from . import views
from . import azure_ad_views

app_name = 'accounts'

urlpatterns = [
    # Authentication endpoints
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Profile management
    path('profile/<str:pk>/', views.UserProfileView.as_view(), name='user-profile'),
    path('profile/me/', views.UserProfileView.as_view(), {'pk': 'me'}, name='my-profile'),
    path('password/change/', views.PasswordChangeView.as_view(), name='password-change'),
    
    # User management (admin/HR only)
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/deactivate/', views.UserDeactivateView.as_view(), name='user-deactivate'),
    path('users/<int:pk>/reactivate/', views.UserReactivateView.as_view(), name='user-reactivate'),
    
    # Session management
    path('sessions/', views.UserSessionListView.as_view(), name='session-list'),
    path('sessions/my/', views.MySessionsView.as_view(), name='my-sessions'),
    
    # Statistics and reporting
    path('stats/', views.user_stats_view, name='user-stats'),
    
    # Azure AD synchronization endpoints
    path('azure-ad/sync/user/<int:user_id>/', azure_ad_views.sync_user_to_azure, name='azure-ad-sync-user'),
    path('azure-ad/sync/bulk/', azure_ad_views.bulk_sync_users, name='azure-ad-bulk-sync'),
    path('azure-ad/sync/retry-failed/', azure_ad_views.retry_failed_syncs, name='azure-ad-retry-failed'),
    path('azure-ad/test/', azure_ad_views.test_connection, name='azure-ad-test'),
    path('azure-ad/dashboard/', azure_ad_views.sync_dashboard, name='azure-ad-dashboard'),
    path('azure-ad/user/<int:user_id>/status/', azure_ad_views.user_sync_status, name='azure-ad-user-status'),
    path('azure-ad/user/<int:user_id>/toggle/', azure_ad_views.toggle_user_sync, name='azure-ad-toggle-sync'),
]