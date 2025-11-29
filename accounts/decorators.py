"""
Custom decorators for role-based access control
"""

from django.contrib.auth.decorators import user_passes_test


def is_admin(user):
    """Check if user is an admin"""
    return user.is_authenticated and user.user_type == "admin"


def is_staff_or_admin(user):
    """Check if user is staff or admin"""
    return user.is_authenticated and user.user_type in ["staff", "admin"]


def is_borrower(user):
    """Check if user is a borrower (regular user)"""
    return user.is_authenticated and user.user_type == "borrower"


def admin_required(function=None, redirect_field_name="next", login_url=None):
    """
    Decorator for views that checks that the user is an admin,
    redirecting to the login page if necessary.
    """
    actual_decorator = user_passes_test(is_admin, login_url=login_url, redirect_field_name=redirect_field_name)
    if function:
        return actual_decorator(function)
    return actual_decorator


def staff_or_admin_required(function=None, redirect_field_name="next", login_url=None):
    """
    Decorator for views that checks that the user is staff or admin,
    redirecting to the login page if necessary.
    """
    actual_decorator = user_passes_test(is_staff_or_admin, login_url=login_url, redirect_field_name=redirect_field_name)
    if function:
        return actual_decorator(function)
    return actual_decorator


def borrower_required(function=None, redirect_field_name="next", login_url=None):
    """
    Decorator for views that checks that the user is a borrower,
    redirecting to the login page if necessary.
    """
    actual_decorator = user_passes_test(is_borrower, login_url=login_url, redirect_field_name=redirect_field_name)
    if function:
        return actual_decorator(function)
    return actual_decorator
