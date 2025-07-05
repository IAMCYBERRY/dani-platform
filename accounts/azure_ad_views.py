"""
API views for Azure AD synchronization management.

These views provide endpoints for managing Azure AD sync operations
through the REST API.
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.conf import settings

from .models import User
from .azure_ad_service import azure_ad_service
from .tasks import (
    sync_user_to_azure_ad,
    bulk_sync_users_to_azure_ad,
    sync_failed_users_retry,
    test_azure_ad_connection
)

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_user_to_azure(request, user_id):
    """
    Sync a specific user to Azure AD.
    
    Body parameters:
    - action: 'create', 'update', 'disable', or 'delete' (default: 'create')
    - force: boolean to force sync even if disabled for user (default: false)
    """
    # Check permissions
    if not request.user.is_admin and not request.user.is_hr_manager:
        return Response(
            {'error': 'Permission denied. Admin or HR Manager role required.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if Azure AD is enabled
    if not settings.AZURE_AD_ENABLED:
        return Response(
            {'error': 'Azure AD integration is disabled'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = get_object_or_404(User, id=user_id)
    action = request.data.get('action', 'sync')  # Default to intelligent sync
    force = request.data.get('force', False)
    
    # Validate action
    valid_actions = ['create', 'update', 'disable', 'delete', 'sync']
    if action not in valid_actions:
        return Response(
            {'error': f'Invalid action. Must be one of: {", ".join(valid_actions)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if sync is enabled for user
    if not user.azure_ad_sync_enabled and not force:
        return Response(
            {'error': 'Azure AD sync is disabled for this user. Use force=true to override.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Queue the sync task
        task = sync_user_to_azure_ad.delay(user_id, action)
        
        # Update user sync status
        user.azure_ad_sync_status = 'pending'
        user.save()
        
        logger.info(f"Queued Azure AD sync for user {user.email} (action: {action})")
        
        return Response({
            'message': f'User sync queued successfully',
            'task_id': task.id,
            'user': {
                'id': user.id,
                'email': user.email,
                'azure_ad_object_id': user.azure_ad_object_id,
                'sync_status': user.azure_ad_sync_status,
            },
            'action': action
        }, status=status.HTTP_202_ACCEPTED)
    
    except Exception as e:
        logger.error(f"Failed to queue Azure AD sync for user {user.email}: {str(e)}")
        return Response(
            {'error': f'Failed to queue sync task: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_sync_users(request):
    """
    Bulk sync multiple users to Azure AD.
    
    Body parameters:
    - user_ids: List of user IDs to sync (optional, if not provided syncs all pending)
    - action: Action to perform for all users (default: 'create')
    """
    # Check permissions
    if not request.user.is_admin and not request.user.is_hr_manager:
        return Response(
            {'error': 'Permission denied. Admin or HR Manager role required.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if Azure AD is enabled
    if not settings.AZURE_AD_ENABLED:
        return Response(
            {'error': 'Azure AD integration is disabled'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user_ids = request.data.get('user_ids')
    action = request.data.get('action', 'sync')  # Default to intelligent sync
    
    # Validate action
    valid_actions = ['create', 'update', 'disable', 'delete', 'sync']
    if action not in valid_actions:
        return Response(
            {'error': f'Invalid action. Must be one of: {", ".join(valid_actions)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Queue the bulk sync task
        task = bulk_sync_users_to_azure_ad.delay(user_ids, action)
        
        logger.info(f"Queued bulk Azure AD sync (action: {action}, user_ids: {user_ids})")
        
        return Response({
            'message': 'Bulk user sync queued successfully',
            'task_id': task.id,
            'user_ids': user_ids,
            'action': action
        }, status=status.HTTP_202_ACCEPTED)
    
    except Exception as e:
        logger.error(f"Failed to queue bulk Azure AD sync: {str(e)}")
        return Response(
            {'error': f'Failed to queue bulk sync task: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_sync_status(request, user_id):
    """
    Get Azure AD sync status for a specific user.
    """
    # Check permissions
    if not (request.user.is_admin or request.user.is_hr_manager or request.user.id == user_id):
        return Response(
            {'error': 'Permission denied. You can only view your own sync status.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    user = get_object_or_404(User, id=user_id)
    
    return Response({
        'user': {
            'id': user.id,
            'email': user.email,
            'full_name': user.get_full_name(),
        },
        'azure_ad': {
            'object_id': user.azure_ad_object_id,
            'sync_enabled': user.azure_ad_sync_enabled,
            'sync_status': user.azure_ad_sync_status,
            'last_sync': user.azure_ad_last_sync.isoformat() if user.azure_ad_last_sync else None,
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def retry_failed_syncs(request):
    """
    Retry synchronization for all users with failed sync status.
    """
    # Check permissions
    if not request.user.is_admin and not request.user.is_hr_manager:
        return Response(
            {'error': 'Permission denied. Admin or HR Manager role required.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if Azure AD is enabled
    if not settings.AZURE_AD_ENABLED:
        return Response(
            {'error': 'Azure AD integration is disabled'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        task = sync_failed_users_retry.delay()
        
        logger.info("Queued retry for failed Azure AD syncs")
        
        return Response({
            'message': 'Failed sync retry queued successfully',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)
    
    except Exception as e:
        logger.error(f"Failed to queue retry task: {str(e)}")
        return Response(
            {'error': f'Failed to queue retry task: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_connection(request):
    """
    Test the connection to Azure AD/Microsoft Graph API.
    """
    # Check permissions
    if not request.user.is_admin:
        return Response(
            {'error': 'Permission denied. Admin role required.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if Azure AD is enabled
    if not settings.AZURE_AD_ENABLED:
        return Response(
            {'error': 'Azure AD integration is disabled'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        task = test_azure_ad_connection.delay()
        
        return Response({
            'message': 'Connection test queued successfully',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)
    
    except Exception as e:
        logger.error(f"Failed to queue connection test: {str(e)}")
        return Response(
            {'error': f'Failed to queue connection test: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sync_dashboard(request):
    """
    Get Azure AD sync dashboard data with statistics.
    """
    # Check permissions
    if not request.user.is_admin and not request.user.is_hr_manager:
        return Response(
            {'error': 'Permission denied. Admin or HR Manager role required.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get sync statistics
    total_users = User.objects.count()
    synced_users = User.objects.filter(azure_ad_sync_status='synced').count()
    pending_users = User.objects.filter(azure_ad_sync_status='pending').count()
    failed_users = User.objects.filter(azure_ad_sync_status='failed').count()
    disabled_users = User.objects.filter(azure_ad_sync_status='disabled').count()
    
    # Get users with Azure AD accounts
    azure_ad_users = User.objects.exclude(azure_ad_object_id__isnull=True).exclude(azure_ad_object_id='').count()
    
    # Get recent sync activities (last 10)
    recent_syncs = User.objects.exclude(azure_ad_last_sync__isnull=True).order_by('-azure_ad_last_sync')[:10]
    
    recent_sync_data = []
    for user in recent_syncs:
        recent_sync_data.append({
            'user_id': user.id,
            'email': user.email,
            'full_name': user.get_full_name(),
            'sync_status': user.azure_ad_sync_status,
            'last_sync': user.azure_ad_last_sync.isoformat() if user.azure_ad_last_sync else None,
            'azure_ad_object_id': user.azure_ad_object_id,
        })
    
    return Response({
        'statistics': {
            'total_users': total_users,
            'azure_ad_users': azure_ad_users,
            'sync_status_breakdown': {
                'synced': synced_users,
                'pending': pending_users,
                'failed': failed_users,
                'disabled': disabled_users,
            },
            'sync_coverage': round((azure_ad_users / total_users * 100) if total_users > 0 else 0, 2),
        },
        'recent_syncs': recent_sync_data,
        'configuration': {
            'azure_ad_enabled': settings.AZURE_AD_ENABLED,
            'sync_enabled': settings.AZURE_AD_SYNC_ENABLED,
            'tenant_id': settings.AZURE_AD_TENANT_ID,
            'sync_on_create': settings.AZURE_AD_SYNC_ON_USER_CREATE,
            'sync_on_update': settings.AZURE_AD_SYNC_ON_USER_UPDATE,
            'sync_on_disable': settings.AZURE_AD_SYNC_ON_USER_DISABLE,
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_user_sync(request, user_id):
    """
    Enable or disable Azure AD sync for a specific user.
    
    Body parameters:
    - enabled: boolean to enable/disable sync
    """
    # Check permissions
    if not request.user.is_admin and not request.user.is_hr_manager:
        return Response(
            {'error': 'Permission denied. Admin or HR Manager role required.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    user = get_object_or_404(User, id=user_id)
    enabled = request.data.get('enabled', True)
    
    if not isinstance(enabled, bool):
        return Response(
            {'error': 'enabled parameter must be a boolean'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user.azure_ad_sync_enabled = enabled
    if not enabled:
        user.azure_ad_sync_status = 'disabled'
    else:
        # Reset to pending if re-enabling
        user.azure_ad_sync_status = 'pending'
    
    user.save()
    
    logger.info(f"Azure AD sync {'enabled' if enabled else 'disabled'} for user {user.email}")
    
    return Response({
        'message': f'Azure AD sync {"enabled" if enabled else "disabled"} for user',
        'user': {
            'id': user.id,
            'email': user.email,
            'azure_ad_sync_enabled': user.azure_ad_sync_enabled,
            'azure_ad_sync_status': user.azure_ad_sync_status,
        }
    })