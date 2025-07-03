"""
URL configuration for employees app.

This module defines the URL patterns for employee management endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'employees'

# Create router for ViewSets
router = DefaultRouter()
router.register(r'departments', views.DepartmentViewSet)
router.register(r'profiles', views.EmployeeProfileViewSet, basename='employeeprofile')
router.register(r'performance-reviews', views.PerformanceReviewViewSet, basename='performancereview')
router.register(r'time-off-requests', views.TimeOffRequestViewSet, basename='timeoffrequest')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
]