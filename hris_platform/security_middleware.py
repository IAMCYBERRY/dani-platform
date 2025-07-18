"""
Security middleware for enhanced security headers and protections.
"""

from django.conf import settings
from django.http import HttpResponse
import time
from collections import defaultdict


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to all responses.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Add CSP header
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline'",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data:",
            "font-src 'self'",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        response['Content-Security-Policy'] = '; '.join(csp_directives)
        
        # Add HSTS in production
        if not settings.DEBUG and request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        return response


class RateLimitMiddleware:
    """
    Simple rate limiting middleware for API endpoints.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.requests = defaultdict(list)
        self.max_requests = 100  # requests per window
        self.window_size = 3600  # 1 hour in seconds

    def __call__(self, request):
        # Only apply rate limiting to API endpoints
        if request.path.startswith('/api/') or 'powerapps' in request.path:
            client_ip = self.get_client_ip(request)
            current_time = time.time()
            
            # Clean old requests
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if current_time - req_time < self.window_size
            ]
            
            # Check rate limit
            if len(self.requests[client_ip]) >= self.max_requests:
                return HttpResponse(
                    'Rate limit exceeded. Try again later.',
                    status=429,
                    content_type='text/plain'
                )
            
            # Record this request
            self.requests[client_ip].append(current_time)
        
        return self.get_response(request)
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityAuditMiddleware:
    """
    Middleware to log security events for monitoring.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log suspicious activity
        if self.is_suspicious_request(request):
            import logging
            logger = logging.getLogger('security')
            logger.warning(f"Suspicious request detected: {request.path}", extra={
                'client_ip': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:100],
                'method': request.method,
                'path': request.path
            })
        
        return self.get_response(request)
    
    def is_suspicious_request(self, request):
        """Check for common attack patterns."""
        suspicious_patterns = [
            'script>',
            'javascript:',
            'eval(',
            'union select',
            '../',
            '..\\',
            'cmd.exe',
            '/etc/passwd',
            'base64_decode'
        ]
        
        # Check URL path
        path_lower = request.path.lower()
        for pattern in suspicious_patterns:
            if pattern in path_lower:
                return True
        
        # Check query parameters
        for value in request.GET.values():
            value_lower = value.lower()
            for pattern in suspicious_patterns:
                if pattern in value_lower:
                    return True
        
        return False
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip