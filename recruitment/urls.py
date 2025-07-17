"""
URL configuration for recruitment app.

This module defines the URL patterns for recruitment and ATS endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'recruitment'

# Create router for ViewSets
router = DefaultRouter()
router.register(r'jobs', views.JobPostingViewSet, basename='jobposting')
router.register(r'applicants', views.ApplicantViewSet, basename='applicant')
router.register(r'interviews', views.InterviewViewSet, basename='interview')
router.register(r'offers', views.JobOffermentViewSet, basename='jobofferment')
router.register(r'powerapps-configs', views.PowerAppsConfigurationViewSet, basename='powerappsconfig')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Additional endpoints
    path('dashboard/', views.recruitment_dashboard, name='dashboard'),
    
    # PowerApps integration
    path('powerapps/<str:api_key>/', views.powerapps_submission, name='powerapps_submission'),
    path('powerapps-wizard/', views.powerapps_wizard, name='powerapps_wizard'),
]