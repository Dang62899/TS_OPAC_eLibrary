"""
Custom permissions for API endpoints
"""

from rest_framework import permissions


class HasAcceptedAgreement(permissions.BasePermission):
    message = "You must accept the user agreement before using the API."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "agreed_to_terms", False)
        )


class IsAuthenticatedAndAgreed(permissions.IsAuthenticated):
    message = "You must accept the user agreement before using the API."

    def has_permission(self, request, view):
        return super().has_permission(request, view) and getattr(
            request.user, "agreed_to_terms", False
        )


class IsAdminUserAndAgreed(permissions.BasePermission):
    message = "An accepted admin account is required."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_library_admin
            and getattr(request.user, "agreed_to_terms", False)
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission to check if user is the owner of the object or is admin
    """

    def has_object_permission(self, request, view, obj):
        if not getattr(request.user, "agreed_to_terms", False):
            return False
        # Admins can do anything
        if request.user and request.user.is_authenticated and request.user.is_library_admin:
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
            and getattr(request.user, "agreed_to_terms", False)
            and request.user.is_library_staff
        )


class IsAdminOrStaff(permissions.BasePermission):
    """
    Permission to check if user is admin or staff
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "agreed_to_terms", False)
            and request.user.is_library_staff
        )


class IsAdmin(permissions.BasePermission):
    """
    Permission to check if user is admin
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "agreed_to_terms", False)
            and request.user.is_library_admin
        )


class IsBorrower(permissions.BasePermission):
    """
    Permission to check if user is a borrower
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "agreed_to_terms", False)
            and request.user.user_type == "borrower"
        )


class IsBorrowerOrStaff(permissions.BasePermission):
    """
    Permission to check if user is borrower or staff
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "agreed_to_terms", False)
            and request.user.user_type in ["borrower", "staff", "admin_staff", "admin"]
        )


class IsNotBlocked(permissions.BasePermission):
    """
    Permission to check if borrower is not blocked
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "agreed_to_terms", False)
            and not request.user.is_blocked
        )
