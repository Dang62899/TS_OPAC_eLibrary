"""
Custom exception handler for API error responses.
Ensures error messages don't leak sensitive information.
"""

import logging
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that:
    1. Uses DRF's default exception handler
    2. Logs detailed error information
    3. Returns generic error messages to client (no sensitive info)
    4. Includes request tracking for debugging
    5. Preserves auth responses
    """
    
    # Get DRF's response
    response = drf_exception_handler(exc, context)
    
    # Get request context
    request = context.get('request')
    view = context.get('view')
    
    # Log the exception with details (for internal debugging)
    _log_exception(exc, request, view, response)
    
    # Only sanitize non-auth responses (preserve 401 as-is)
    if response is not None and response.status_code != 401:
        response = _sanitize_response(response, request)
    
    return response


def _log_exception(exc, request, view, response):
    """Log exception with relevant context"""
    
    status_code = response.status_code if response else 500
    
    log_data = {
        'exception': exc.__class__.__name__,
        'method': request.method if request else 'UNKNOWN',
        'path': request.path if request else 'UNKNOWN',
        'user': str(request.user) if request else 'ANONYMOUS',
        'status_code': status_code,
    }
    
    if status_code >= 500:
        # Server errors - log at ERROR level
        logger.error(f"Server error: {log_data}", exc_info=True)
    elif status_code >= 400:
        # Client errors - log at WARNING level
        logger.warning(f"Client error: {log_data}")
    else:
        # Success - log at INFO level
        logger.info(f"Response: {log_data}")


def _sanitize_response(response, request):
    """
    Sanitize error response to avoid leaking sensitive information.
    In production, we don't want to expose internal error details.
    
    Note: 401 responses are not sanitized here to preserve authentication
    error messages from DRF's token authentication.
    """
    
    status_code = response.status_code
    
    if status_code == 404:
        response.data = {"detail": "Resource not found."}
    elif status_code == 403:
        response.data = {"detail": "You do not have permission to perform this action."}
    elif status_code == 429:
        response.data = {"detail": "Request throttled. Please try again later."}
    elif status_code >= 500:
        # Don't expose internal server error details
        response.data = {"detail": "Internal server error. Please contact support."}
    
    return response
