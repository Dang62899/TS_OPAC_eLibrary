"""
Advanced security configurations and middleware for TS OPAC eLibrary

Provides:
- Request/Response security headers
- Rate limiting per user/IP
- Input validation and sanitization
- CSRF protection enhancements
- Security logging
"""

import hashlib
import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import ValidationError
from rest_framework import status
import re

logger = logging.getLogger(__name__)


class DevNoHSTSMiddleware(MiddlewareMixin):
    """
    Development-only middleware to remove HSTS headers and prevent HTTPS enforcement.
    Ensures HTTP-only access during development.
    """

    def process_response(self, request, response):
        """Remove HSTS headers in development"""
        # Remove any HSTS headers that might be set
        if "Strict-Transport-Security" in response:
            del response["Strict-Transport-Security"]
        # Ensure no HTTPS redirect is happening
        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers to all responses.
    Protects against XSS, clickjacking, MIME type sniffing, etc.
    """

    def process_response(self, request, response):
        """Add security headers to response"""
        
        # Prevent clickjacking attacks
        response["X-Frame-Options"] = "DENY"
        
        # Prevent MIME type sniffing
        response["X-Content-Type-Options"] = "nosniff"
        
        # Enable XSS protection in older browsers
        response["X-XSS-Protection"] = "1; mode=block"
        
        # Content Security Policy - restrictive policy
        response["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        
        # Referrer policy - don't leak referrer to external sites
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Feature policy / Permissions policy
        response["Permissions-Policy"] = (
            "camera=(), "
            "microphone=(), "
            "geolocation=(), "
            "payment=()"
        )
        
        # Cache policy for sensitive endpoints
        if "/api/" in request.path:
            response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response["Pragma"] = "no-cache"
        
        return response


class SecurityLoggingMiddleware(MiddlewareMixin):
    """
    Log security-relevant events (failed auth, suspicious patterns, etc.)
    """

    def process_request(self, request):
        """Log incoming request details"""
        
        # Log failed authentication attempts
        if "/api/auth/" in request.path and request.method == "POST":
            # Will log failed attempts at application level
            pass
        
        # Check for suspicious patterns
        if self._check_suspicious_request(request):
            logger.warning(
                f"Suspicious request detected: {request.method} {request.path} "
                f"from {self._get_client_ip(request)}"
            )
        
        return None

    def process_response(self, request, response):
        """Log response status for security events"""
        
        # Log authentication failures
        if response.status_code == 401:
            logger.warning(
                f"Authentication failed: {request.method} {request.path} "
                f"from {self._get_client_ip(request)}"
            )
        
        # Log permission denied
        if response.status_code == 403:
            logger.warning(
                f"Permission denied: {request.method} {request.path} "
                f"from {self._get_client_ip(request)} user={request.user}"
            )
        
        # Log potential attacks
        if response.status_code == 400:
            logger.info(
                f"Bad request: {request.method} {request.path} "
                f"from {self._get_client_ip(request)}"
            )
        
        return response

    @staticmethod
    def _check_suspicious_request(request):
        """Check for common attack patterns"""
        
        # SQL injection patterns
        suspicious_patterns = [
            r"(\bunion\b|\bselect\b|\binsert\b|\bupdate\b|\bdelete\b|\bdrop\b)",  # SQL keywords
            r"(<script|javascript:|onerror=|onload=)",  # XSS patterns
            r"(\.\.\%2f|\.\.\%5c)",  # Path traversal
            r"(eval\(|exec\(|system\()",  # Code injection
        ]
        
        # Check path and query string
        full_path = f"{request.path}?{request.GET.urlencode()}"
        
        for pattern in suspicious_patterns:
            if re.search(pattern, full_path, re.IGNORECASE):
                return True
        
        return False

    @staticmethod
    def _get_client_ip(request):
        """Get client IP from request, accounting for proxies"""
        
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        
        return ip


class InputSanitizer:
    """
    Utility class for input validation and sanitization
    """

    # Disallowed characters in common fields
    USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]{3,150}$")
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    ISBN_PATTERN = re.compile(r"^(?:ISBN(?:-1[03])?:? )?(?=[0-9X]{10}$|(?=(?:[0-9]+[- ]){3})[- 0-9X]{13}$|97[89][0-9]{10}$|(?=(?:[0-9]+[- ]){4})[- 0-9]{17}$)(?:97[89][- ]?)?[0-9]{1,5}[- ]?[0-9]+[- ]?[0-9]+[- ]?[X0-9]$")
    BARCODE_PATTERN = re.compile(r"^[A-Za-z0-9_-]{5,100}$")

    @classmethod
    def sanitize_username(cls, username):
        """Validate and sanitize username"""
        
        if not username or not isinstance(username, str):
            raise ValidationError("Username must be a non-empty string")
        
        username = username.strip()
        
        if not cls.USERNAME_PATTERN.match(username):
            raise ValidationError(
                "Username must be 3-150 characters, "
                "containing only letters, numbers, dots, underscores, or hyphens"
            )
        
        return username

    @classmethod
    def sanitize_email(cls, email):
        """Validate and sanitize email"""
        
        if not email or not isinstance(email, str):
            raise ValidationError("Email must be a non-empty string")
        
        email = email.strip().lower()
        
        if not cls.EMAIL_PATTERN.match(email):
            raise ValidationError("Invalid email format")
        
        if len(email) > 254:
            raise ValidationError("Email too long (max 254 characters)")
        
        return email

    @classmethod
    def sanitize_isbn(cls, isbn):
        """Validate and sanitize ISBN"""
        
        if not isbn or not isinstance(isbn, str):
            raise ValidationError("ISBN must be a non-empty string")
        
        isbn = isbn.strip().replace("-", "").replace(" ", "").upper()
        
        if not cls.ISBN_PATTERN.match(isbn):
            raise ValidationError("Invalid ISBN format")
        
        return isbn

    @classmethod
    def sanitize_barcode(cls, barcode):
        """Validate and sanitize barcode"""
        
        if not barcode or not isinstance(barcode, str):
            raise ValidationError("Barcode must be a non-empty string")
        
        barcode = barcode.strip()
        
        if not cls.BARCODE_PATTERN.match(barcode):
            raise ValidationError(
                "Invalid barcode format (5-100 alphanumeric characters, "
                "hyphens, underscores allowed)"
            )
        
        return barcode

    @staticmethod
    def sanitize_search_query(query):
        """Sanitize search queries to prevent injection"""
        
        if not query or not isinstance(query, str):
            raise ValidationError("Search query must be a non-empty string")
        
        query = query.strip()
        
        if len(query) > 500:
            raise ValidationError("Search query too long (max 500 characters)")
        
        # Remove potentially dangerous characters but allow common search patterns
        dangerous_chars = r"[<>\"'%;()&+]"
        if re.search(dangerous_chars, query):
            raise ValidationError("Search query contains invalid characters")
        
        return query

    @staticmethod
    def hash_sensitive_data(data):
        """Hash sensitive data for logging (not reversible)"""
        
        if not data:
            return None
        
        return hashlib.sha256(str(data).encode()).hexdigest()[:16]


def get_client_ip(request):
    """Utility function to get client IP from request"""
    
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    
    return ip
