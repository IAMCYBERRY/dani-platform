"""
Middleware for PowerApps integration.

This module provides middleware for handling PowerApps-specific requirements
like CORS headers and API authentication.
"""

from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from .models import PowerAppsConfiguration


class PowerAppsCorsMiddleware(MiddlewareMixin):
    """
    Middleware to handle CORS for PowerApps endpoints.
    
    This middleware checks if a request is for a PowerApps endpoint
    and applies appropriate CORS headers based on the configuration.
    """
    
    def process_request(self, request):
        """Process incoming request for PowerApps CORS."""
        
        # Check if this is a PowerApps endpoint
        if '/api/recruitment/powerapps/' in request.path:
            # Handle preflight OPTIONS request
            if request.method == 'OPTIONS':
                response = HttpResponse()
                self._add_cors_headers(response, request)
                return response
        
        return None
    
    def process_response(self, request, response):
        """Process response to add CORS headers for PowerApps endpoints."""
        
        # Check if this is a PowerApps endpoint
        if '/api/recruitment/powerapps/' in request.path:
            self._add_cors_headers(response, request)
        
        return response
    
    def _add_cors_headers(self, response, request):
        """Add CORS headers to response."""
        
        # Get the API key from the URL
        try:
            path_parts = request.path.split('/')
            if 'powerapps' in path_parts:
                api_key_index = path_parts.index('powerapps') + 1
                if api_key_index < len(path_parts):
                    api_key = path_parts[api_key_index]
                    
                    # Get the configuration for this API key
                    try:
                        config = PowerAppsConfiguration.objects.get(
                            api_key=api_key,
                            status=PowerAppsConfiguration.Status.ACTIVE
                        )
                        
                        # Get allowed origins from configuration
                        allowed_origins = config.allowed_origins or []
                        
                        # Check if origin is allowed
                        origin = request.META.get('HTTP_ORIGIN')
                        if origin and origin in allowed_origins:
                            response['Access-Control-Allow-Origin'] = origin
                        elif not allowed_origins:  # If no restrictions, allow all
                            response['Access-Control-Allow-Origin'] = '*'
                        
                    except PowerAppsConfiguration.DoesNotExist:
                        # If configuration doesn't exist, don't add CORS headers
                        pass
        except (IndexError, ValueError):
            # If we can't parse the API key, don't add CORS headers
            pass
        
        # Add other CORS headers
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response['Access-Control-Max-Age'] = '86400'