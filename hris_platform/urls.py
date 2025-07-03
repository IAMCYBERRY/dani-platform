"""
D.A.N.I Platform URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# Customize admin site branding
admin.site.site_header = 'D.A.N.I Administration'
admin.site.site_title = 'D.A.N.I Admin Portal'
admin.site.index_title = 'Welcome to D.A.N.I - Domain Access & Navigation Interface'

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API Authentication
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API endpoints
    path('api/accounts/', include('accounts.urls')),
    path('api/employees/', include('employees.urls')),
    path('api/recruitment/', include('recruitment.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)