# Enhanced Security Module for TS OPAC eLibrary
# accounts/security.py

from django.contrib.auth.models import User
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
import logging
from datetime import timedelta
import hashlib
import secrets

logger = logging.getLogger('django.security')


class AccountSecurityManager:
    """Manage account security features (lockout, 2FA, etc.)"""
    
    FAILED_LOGIN_ATTEMPTS_KEY = "failed_login_{username}"
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION = 30 * 60  # 30 minutes in seconds
    
    @classmethod
    def record_failed_login(cls, username):
        """
        Record a failed login attempt and potentially lock the account
        
        Args:
            username (str): Username that failed login
            
        Returns:
            dict: Status information including lockout status
        """
        key = cls.FAILED_LOGIN_ATTEMPTS_KEY.format(username=username)
        attempts = cache.get(key, 0)
        attempts += 1
        
        # Set cache with expiration
        cache.set(key, attempts, cls.LOCKOUT_DURATION)
        
        logger.warning(f"Failed login attempt for {username} (attempt {attempts}/{cls.MAX_FAILED_ATTEMPTS})")
        
        return {
            'attempts': attempts,
            'max_attempts': cls.MAX_FAILED_ATTEMPTS,
            'is_locked': attempts >= cls.MAX_FAILED_ATTEMPTS,
            'locked_until': timezone.now() + timedelta(seconds=cls.LOCKOUT_DURATION) if attempts >= cls.MAX_FAILED_ATTEMPTS else None
        }
    
    @classmethod
    def clear_failed_attempts(cls, username):
        """Clear failed login attempts for a user"""
        key = cls.FAILED_LOGIN_ATTEMPTS_KEY.format(username=username)
        cache.delete(key)
        logger.info(f"Failed login attempts cleared for {username}")
    
    @classmethod
    def is_account_locked(cls, username):
        """Check if account is locked due to failed attempts"""
        key = cls.FAILED_LOGIN_ATTEMPTS_KEY.format(username=username)
        attempts = cache.get(key, 0)
        return attempts >= cls.MAX_FAILED_ATTEMPTS
    
    @classmethod
    def get_lockout_remaining_time(cls, username):
        """Get remaining lockout time in seconds"""
        key = cls.FAILED_LOGIN_ATTEMPTS_KEY.format(username=username)
        ttl = cache.ttl(key) if hasattr(cache, 'ttl') else 0
        return max(0, ttl)


class SessionSecurityManager:
    """Manage secure session handling"""
    
    SESSION_TOKEN_KEY = "session_token_{user_id}"
    
    @classmethod
    def create_session_token(cls, user):
        """Create a unique session token for user"""
        token = secrets.token_urlsafe(32)
        hashed_token = hashlib.sha256(token.encode()).hexdigest()
        
        # Store in cache
        cache.set(
            cls.SESSION_TOKEN_KEY.format(user_id=user.id),
            hashed_token,
            settings.SESSION_COOKIE_AGE
        )
        
        logger.info(f"Session token created for user {user.username}")
        return token
    
    @classmethod
    def validate_session_token(cls, user, token):
        """Validate session token"""
        hashed_token = hashlib.sha256(token.encode()).hexdigest()
        stored_token = cache.get(cls.SESSION_TOKEN_KEY.format(user_id=user.id))
        
        return stored_token == hashed_token
    
    @classmethod
    def invalidate_all_sessions(cls, user):
        """Logout user from all devices"""
        key = cls.SESSION_TOKEN_KEY.format(user_id=user.id)
        cache.delete(key)
        logger.warning(f"All sessions invalidated for user {user.username}")


class InputSanitizer:
    """Sanitize and validate user input"""
    
    DANGEROUS_CHARS = ['<', '>', '"', "'", '&', ';', '|', '*', '?']
    MAX_SEARCH_LENGTH = 255
    
    @classmethod
    def sanitize_search_query(cls, query):
        """
        Sanitize search query to prevent injection attacks
        
        Args:
            query (str): Raw search query
            
        Returns:
            str: Sanitized query
        """
        if not query:
            return ""
        
        # Limit length
        query = query[:cls.MAX_SEARCH_LENGTH]
        
        # Remove dangerous characters
        for char in cls.DANGEROUS_CHARS:
            query = query.replace(char, '')
        
        # Strip whitespace
        query = query.strip()
        
        return query
    
    @classmethod
    def validate_isbn(cls, isbn):
        """
        Validate ISBN-10 or ISBN-13
        
        Args:
            isbn (str): ISBN string
            
        Returns:
            bool: Whether ISBN is valid
        """
        # Remove hyphens and spaces
        isbn = isbn.replace('-', '').replace(' ', '')
        
        # Check length
        if len(isbn) not in [10, 13]:
            return False
        
        # Check if all characters are digits
        if not isbn.isdigit():
            return False
        
        # ISBN-10 validation
        if len(isbn) == 10:
            total = sum((int(char) * (10 - i)) for i, char in enumerate(isbn))
            return total % 11 == 0
        
        # ISBN-13 validation
        else:
            total = sum((int(char) * (1 if i % 2 == 0 else 3)) for i, char in enumerate(isbn))
            return total % 10 == 0
    
    @classmethod
    def validate_email(cls, email):
        """
        Validate email address
        
        Args:
            email (str): Email address
            
        Returns:
            bool: Whether email is valid
        """
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None


class EncryptedFieldManager:
    """Manage encrypted fields for sensitive data"""
    
    @classmethod
    def encrypt_value(cls, value, key=None):
        """
        Encrypt a value (requires django-encrypted-model-fields)
        
        Args:
            value (str): Value to encrypt
            key (str): Encryption key (uses settings default if None)
            
        Returns:
            str: Encrypted value
        """
        from cryptography.fernet import Fernet
        
        if key is None:
            key = settings.ENCRYPTION_KEY
        
        cipher_suite = Fernet(key)
        encrypted = cipher_suite.encrypt(value.encode())
        return encrypted.decode()
    
    @classmethod
    def decrypt_value(cls, encrypted_value, key=None):
        """
        Decrypt a value
        
        Args:
            encrypted_value (str): Encrypted value
            key (str): Encryption key (uses settings default if None)
            
        Returns:
            str: Decrypted value
        """
        from cryptography.fernet import Fernet
        
        if key is None:
            key = settings.ENCRYPTION_KEY
        
        cipher_suite = Fernet(key)
        decrypted = cipher_suite.decrypt(encrypted_value.encode())
        return decrypted.decode()


class AuditLogger:
    """Log sensitive data access for compliance"""
    
    @classmethod
    def log_data_access(cls, user, data_type, action, details=None):
        """
        Log access to sensitive data
        
        Args:
            user (User): User accessing data
            data_type (str): Type of data accessed (e.g., 'user_profile', 'checkout_history')
            action (str): Action performed (e.g., 'view', 'edit', 'export')
            details (dict): Additional details to log
        """
        timestamp = timezone.now()
        
        log_entry = {
            'timestamp': timestamp.isoformat(),
            'user_id': user.id,
            'username': user.username,
            'data_type': data_type,
            'action': action,
            'ip_address': getattr(user, 'ip_address', 'unknown'),
            'details': details or {}
        }
        
        logger.info(f"Data access: {log_entry}")
    
    @classmethod
    def log_security_event(cls, event_type, user=None, details=None):
        """
        Log security events
        
        Args:
            event_type (str): Type of security event
            user (User): User involved (if applicable)
            details (dict): Event details
        """
        timestamp = timezone.now()
        
        log_entry = {
            'timestamp': timestamp.isoformat(),
            'event_type': event_type,
            'user_id': user.id if user else None,
            'username': user.username if user else None,
            'details': details or {}
        }
        
        logger.warning(f"Security event: {log_entry}")


class PasswordSecurityManager:
    """Manage password security policies"""
    
    MIN_PASSWORD_LENGTH = 12
    REQUIRE_UPPERCASE = True
    REQUIRE_NUMBERS = True
    REQUIRE_SPECIAL_CHARS = True
    
    @classmethod
    def validate_password_strength(cls, password):
        """
        Validate password against security requirements
        
        Args:
            password (str): Password to validate
            
        Returns:
            tuple: (is_valid, error_messages)
        """
        errors = []
        
        # Check length
        if len(password) < cls.MIN_PASSWORD_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_PASSWORD_LENGTH} characters")
        
        # Check for uppercase
        if cls.REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        # Check for numbers
        if cls.REQUIRE_NUMBERS and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        # Check for special characters
        if cls.REQUIRE_SPECIAL_CHARS:
            special_chars = set('!@#$%^&*()_+-=[]{}|;:,.<>?')
            if not any(c in special_chars for c in password):
                errors.append("Password must contain at least one special character (!@#$%^&*)")
        
        return (len(errors) == 0, errors)


class TwoFactorAuthManager:
    """Manage two-factor authentication"""
    
    TOTP_KEY = "totp_secret_{user_id}"
    
    @classmethod
    def generate_totp_secret(cls, user):
        """
        Generate TOTP (Time-based One-Time Password) secret
        Requires 'pyotp' library
        
        Args:
            user (User): User to generate secret for
            
        Returns:
            str: TOTP secret
        """
        import pyotp
        
        secret = pyotp.random_base32()
        cache.set(cls.TOTP_KEY.format(user_id=user.id), secret, None)
        
        logger.info(f"2FA secret generated for user {user.username}")
        return secret
    
    @classmethod
    def verify_totp(cls, user, token):
        """
        Verify TOTP token
        
        Args:
            user (User): User to verify
            token (str): TOTP token from authenticator app
            
        Returns:
            bool: Whether token is valid
        """
        import pyotp
        
        secret = cache.get(cls.TOTP_KEY.format(user_id=user.id))
        if not secret:
            return False
        
        totp = pyotp.TOTP(secret)
        return totp.verify(token)


# ============================================================================
# MIDDLEWARE
# ============================================================================

class SecurityHeadersMiddleware:
    """Add security headers to all responses"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Prevent clickjacking
        response['X-Frame-Options'] = 'DENY'
        
        # Enable XSS protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Force HTTPS
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' cdn.jsdelivr.net; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        
        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Feature Policy
        response['Permissions-Policy'] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )
        
        return response
