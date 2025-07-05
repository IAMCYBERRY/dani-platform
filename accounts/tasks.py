"""
Celery tasks for Azure AD synchronization.

These tasks handle background synchronization between the HRIS platform
and Azure AD to ensure data consistency and reliability.
"""

import logging
from typing import Dict, Any

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .models import User
from .azure_ad_service import azure_ad_service

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def sync_user_to_azure_ad(self, user_id: int, action: str = 'create') -> Dict[str, Any]:
    """
    Sync a user to Azure AD.
    
    Args:
        user_id: The ID of the user to sync
        action: The action to perform ('create', 'update', 'disable', 'delete')
    
    Returns:
        Dict containing sync result information
    """
    if not settings.AZURE_AD_ENABLED or not settings.AZURE_AD_SYNC_ENABLED:
        return {
            'success': False,
            'error': 'Azure AD sync is disabled',
            'user_id': user_id,
            'action': action
        }
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return {
            'success': False,
            'error': f'User with ID {user_id} not found',
            'user_id': user_id,
            'action': action
        }
    
    # Update sync status to pending
    user.azure_ad_sync_status = 'pending'
    user.save()
    
    try:
        if action == 'create':
            # Use intelligent sync that automatically chooses create or update
            success, result = azure_ad_service.sync_user_from_hris(user, force_create=True)
        elif action == 'update':
            success, result = azure_ad_service.update_user(user)
        elif action == 'disable':
            success, result = azure_ad_service.disable_user(user)
        elif action == 'delete':
            success, result = azure_ad_service.delete_user(user)
        elif action == 'sync':
            # New action: intelligent sync (create or update as needed)
            success, result = azure_ad_service.sync_user_from_hris(user, force_create=True)
        else:
            logger.error(f"Invalid action: {action}")
            return {
                'success': False,
                'error': f'Invalid action: {action}',
                'user_id': user_id,
                'action': action
            }
        
        if success:
            logger.info(f"Successfully {action}d user {user.email} in Azure AD")
            return {
                'success': True,
                'message': f'User {action}d successfully in Azure AD',
                'user_id': user_id,
                'action': action,
                'result': result
            }
        else:
            # Retry on failure
            if self.request.retries < self.max_retries:
                logger.warning(f"Retrying Azure AD sync for user {user.email} (attempt {self.request.retries + 1})")
                raise self.retry(countdown=self.default_retry_delay * (2 ** self.request.retries))
            else:
                logger.error(f"Failed to {action} user {user.email} in Azure AD after {self.max_retries} retries: {result}")
                return {
                    'success': False,
                    'error': f'Failed to {action} user in Azure AD',
                    'user_id': user_id,
                    'action': action,
                    'details': result
                }
    
    except Exception as e:
        logger.error(f"Exception during Azure AD sync for user {user.email}: {str(e)}")
        
        # Update sync status to failed
        user.azure_ad_sync_status = 'failed'
        user.save()
        
        # Retry on exception
        if self.request.retries < self.max_retries:
            logger.warning(f"Retrying Azure AD sync for user {user.email} due to exception (attempt {self.request.retries + 1})")
            raise self.retry(countdown=self.default_retry_delay * (2 ** self.request.retries))
        else:
            return {
                'success': False,
                'error': f'Exception during Azure AD sync: {str(e)}',
                'user_id': user_id,
                'action': action
            }


@shared_task
def bulk_sync_users_to_azure_ad(user_ids: list = None, action: str = 'create') -> Dict[str, Any]:
    """
    Bulk sync multiple users to Azure AD.
    
    Args:
        user_ids: List of user IDs to sync. If None, sync all pending users.
        action: The action to perform for all users
    
    Returns:
        Dict containing bulk sync results
    """
    if not settings.AZURE_AD_ENABLED or not settings.AZURE_AD_SYNC_ENABLED:
        return {
            'success': False,
            'error': 'Azure AD sync is disabled',
            'total_users': 0,
            'successful': 0,
            'failed': 0
        }
    
    # Get users to sync
    if user_ids:
        users = User.objects.filter(id__in=user_ids, azure_ad_sync_enabled=True)
    else:
        # Sync all users with pending status
        users = User.objects.filter(
            azure_ad_sync_status='pending',
            azure_ad_sync_enabled=True
        )
    
    total_users = users.count()
    successful = 0
    failed = 0
    results = []
    
    logger.info(f"Starting bulk Azure AD sync for {total_users} users")
    
    for user in users:
        try:
            # Queue individual sync task
            result = sync_user_to_azure_ad.delay(user.id, action)
            results.append({
                'user_id': user.id,
                'email': user.email,
                'task_id': result.id,
                'status': 'queued'
            })
        except Exception as e:
            logger.error(f"Failed to queue sync task for user {user.email}: {str(e)}")
            failed += 1
            results.append({
                'user_id': user.id,
                'email': user.email,
                'status': 'failed_to_queue',
                'error': str(e)
            })
    
    successful = len([r for r in results if r['status'] == 'queued'])
    
    logger.info(f"Bulk Azure AD sync completed: {successful} queued, {failed} failed to queue")
    
    return {
        'success': True,
        'total_users': total_users,
        'successful': successful,
        'failed': failed,
        'results': results
    }


@shared_task
def sync_failed_users_retry() -> Dict[str, Any]:
    """
    Retry synchronization for users with failed sync status.
    This task should be run periodically to handle temporary failures.
    
    Returns:
        Dict containing retry results
    """
    if not settings.AZURE_AD_ENABLED or not settings.AZURE_AD_SYNC_ENABLED:
        return {
            'success': False,
            'error': 'Azure AD sync is disabled',
            'retried_users': 0
        }
    
    # Get users with failed sync status
    failed_users = User.objects.filter(
        azure_ad_sync_status='failed',
        azure_ad_sync_enabled=True
    )
    
    retried_count = 0
    
    for user in failed_users:
        try:
            # Use intelligent sync action that handles both create and update
            action = 'sync'
            
            # Queue retry task
            sync_user_to_azure_ad.delay(user.id, action)
            retried_count += 1
            
            logger.info(f"Queued retry for user {user.email}")
            
        except Exception as e:
            logger.error(f"Failed to queue retry for user {user.email}: {str(e)}")
    
    logger.info(f"Queued {retried_count} users for Azure AD sync retry")
    
    return {
        'success': True,
        'retried_users': retried_count,
        'message': f'Queued {retried_count} users for retry'
    }


@shared_task
def test_azure_ad_connection() -> Dict[str, Any]:
    """
    Test the connection to Azure AD/Microsoft Graph API.
    
    Returns:
        Dict containing connection test results
    """
    if not settings.AZURE_AD_ENABLED:
        return {
            'success': False,
            'error': 'Azure AD is disabled',
            'timestamp': timezone.now().isoformat()
        }
    
    try:
        success, result = azure_ad_service.test_connection()
        
        return {
            'success': success,
            'timestamp': timezone.now().isoformat(),
            'result': result
        }
    
    except Exception as e:
        logger.error(f"Exception during Azure AD connection test: {str(e)}")
        return {
            'success': False,
            'error': f'Exception during connection test: {str(e)}',
            'timestamp': timezone.now().isoformat()
        }


@shared_task
def cleanup_sync_status() -> Dict[str, Any]:
    """
    Clean up old sync statuses and update pending users that have been
    stuck in pending state for too long.
    
    Returns:
        Dict containing cleanup results
    """
    from datetime import timedelta
    
    # Reset pending status for users stuck for more than 1 hour
    stuck_threshold = timezone.now() - timedelta(hours=1)
    
    stuck_users = User.objects.filter(
        azure_ad_sync_status='pending',
        updated_at__lt=stuck_threshold
    )
    
    updated_count = stuck_users.update(azure_ad_sync_status='failed')
    
    logger.info(f"Reset {updated_count} stuck pending users to failed status")
    
    return {
        'success': True,
        'updated_users': updated_count,
        'message': f'Reset {updated_count} stuck pending users'
    }