"""
Celery configuration for HRIS Platform.

This module configures Celery for background task processing,
including Azure AD synchronization tasks.
"""

import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hris_platform.settings')

app = Celery('hris_platform')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery functionality."""
    print(f'Request: {self.request!r}')