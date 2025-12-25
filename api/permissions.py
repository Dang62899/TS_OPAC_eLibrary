"""
Custom permissions for API endpoints
"""

from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission to check if user is the owner of the object or is admin
    """

    def has_object_permission(self, request, view, obj):
        # Admins can do anything
        if request.user and request.user.user_type == "admin":
            return True
        # Users can only view/edit their own profiles
        return obj == request.user


class IsStaffOrAdmin(permissions.BasePermission):
    """
    Permission to check if user is staff or admin
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.user_type in ["staff", "admin"]
        )


class IsAdmin(permissions.BasePermission):
    """
    Permission to check if user is admin
    """

    def has_permission(self, request, view):
        return request.user and request.user.user_type == "admin"


class IsBorrower(permissions.BasePermission):
    """
    Permission to check if user is a borrower
    """

    def has_permission(self, request, view):
        return request.user and request.user.user_type == "borrower"


class IsBorrowerOrStaff(permissions.BasePermission):
    """
    Permission to check if user is borrower or staff
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.user_type in ["borrower", "staff", "admin"]
        )


class IsNotBlocked(permissions.BasePermission):
    """
    Permission to check if borrower is not blocked
    """

    def has_permission(self, request, view):
        return request.user and not request.user.is_blocked
