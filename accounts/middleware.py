from django.shortcuts import redirect
from django.urls import reverse


class RequireAgreementMiddleware:
    """Redirect authenticated users who haven't accepted the user agreement."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            path = request.path
            allow_paths = [reverse("accounts:user_agreement"), reverse("accounts:logout")]
            user = request.user
            is_admin_account = user.is_superuser or user.is_staff or getattr(user, "user_type", "") in (
                "admin",
                "admin_staff",
                "staff",
            )
            if (
                not is_admin_account
                and not getattr(user, "agreed_to_terms", False)
                and path not in allow_paths
                and not path.startswith("/admin/")
            ):
                return redirect("accounts:user_agreement")
        return self.get_response(request)
