from django.shortcuts import render, redirect, get_object_or_404
from .forms import build_login_challenge
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.forms import SetPasswordForm
from django.contrib import messages
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Q
from .forms import (
    AdminRegistrationForm,
    AgreementAcceptanceForm,
    LoginForm,
    ProfileUpdateForm,
)
from .decorators import admin_required, staff_or_admin_required
from circulation.models import Loan, Hold
from .models import User
from .security import AccountSecurityManager, TwoFactorAuthManager
from django.utils import timezone


@login_required
def user_agreement(request):
    """Display the user agreement and record acceptance."""
    form = AgreementAcceptanceForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        # Record acceptance
        request.user.agreed_to_terms = True
        request.user.agreed_at = timezone.now()
        request.user.save(update_fields=["agreed_to_terms", "agreed_at"])
        messages.success(request, "Thank you for accepting the user agreement.")
        return redirect("catalog:index")

    # Agreement text can be stored in docs or settings; keep a short placeholder here
    agreement_text = "By using this Elibrary you agree to abide by the terms of use and SOPs."
    return render(
        request,
        "accounts/user_agreement.html",
        {"agreement_text": agreement_text, "form": form},
    )


def custom_login(request):
    """Custom login view with CAPTCHA and optional TOTP-based two-factor authentication."""
    if request.user.is_authenticated:
        return redirect("catalog:index")

    if request.method == "POST":
        form = LoginForm(request.POST, request=request)
        username = request.POST.get("username", "").strip()
        if username and AccountSecurityManager.is_account_locked(username):
            remaining_seconds = AccountSecurityManager.get_lockout_remaining_time(username)
            remaining_minutes = max(1, remaining_seconds // 60)
            messages.error(
                request,
                f"Account locked due to too many failed login attempts. Try again in {remaining_minutes} minute{'s' if remaining_minutes != 1 else ''}.",
            )
            return render(
                request,
                "accounts/login.html",
                {
                    "form": form,
                    "requires_2fa": False,
                    "captcha_value": request.session.get("login_captcha_value"),
                    "captcha_prompt": request.session.get("login_captcha_prompt", "Enter the code shown in the image."),
                    "captcha_options": request.session.get("login_captcha_options", []),
                },
            )

        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )
            if user is None:
                if username:
                    AccountSecurityManager.record_failed_login(username)
                messages.error(request, "Invalid username or password.")
            else:
                if user.two_factor_enabled:
                    if not form.cleaned_data.get("totp_code"):
                        cache.set(f"pending_2fa_{user.id}", True, 300)
                        messages.info(request, "Please enter your authenticator code to continue.")
                        return render(
                            request,
                            "accounts/login.html",
                            {
                                "form": form,
                                "requires_2fa": True,
                                "username": user.username,
                                "captcha_value": request.session.get("login_captcha_value"),
                                "captcha_prompt": request.session.get("login_captcha_prompt", "Enter the code shown in the image."),
                                "captcha_options": request.session.get("login_captcha_options", []),
                            },
                        )

                    if not TwoFactorAuthManager.verify_totp(user, form.cleaned_data["totp_code"]):
                        messages.error(request, "Invalid authenticator code.")
                        return render(
                            request,
                            "accounts/login.html",
                            {
                                "form": form,
                                "requires_2fa": True,
                                "username": user.username,
                                "captcha_value": request.session.get("login_captcha_value"),
                                "captcha_prompt": request.session.get("login_captcha_prompt", "Enter the code shown in the image."),
                                "captcha_options": request.session.get("login_captcha_options", []),
                            },
                        )

                    cache.delete(f"pending_2fa_{user.id}")

                auth_login(request, user)
                AccountSecurityManager.clear_failed_attempts(user.username)
                return redirect("catalog:index")
        else:
            messages.error(request, "Please correct the highlighted errors.")
    else:
        challenge = build_login_challenge()
        request.session["login_captcha_value"] = challenge["correct_value"]
        request.session["login_captcha_prompt"] = "Complete the security check."
        request.session["login_captcha_options"] = challenge["samples"]
        request.session["login_captcha_image"] = challenge["image_data_url"]
        form = LoginForm(request=request)

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
            "requires_2fa": False,
            "captcha_value": request.session.get("login_captcha_value"),
            "captcha_prompt": request.session.get("login_captcha_prompt", "Complete the security check."),
            "captcha_options": request.session.get("login_captcha_options", []),
            "captcha_image": request.session.get("login_captcha_image"),
        },
    )


@login_required
def setup_two_factor(request):
    """Enable or disable TOTP-based two-factor authentication for the current user."""
    if request.user.user_type not in ["staff", "admin_staff", "admin", "borrower"]:
        messages.error(request, "Two-factor authentication is not available for this account type.")
        return redirect("accounts:profile")

    if request.method == "POST":
        token = request.POST.get("totp_code", "").strip()
        if not token:
            messages.error(request, "Please enter the authenticator code.")
        else:
            if TwoFactorAuthManager.verify_totp(request.user, token):
                request.user.two_factor_enabled = True
                request.user.save(update_fields=["two_factor_enabled"])
                messages.success(request, "Two-factor authentication has been enabled.")
                return redirect("accounts:profile")
            messages.error(request, "The authenticator code was invalid. Please try again.")

    if not request.user.otp_secret:
        TwoFactorAuthManager.generate_totp_secret(request.user)

    context = {
        "otp_secret": request.user.otp_secret,
        "two_factor_enabled": request.user.two_factor_enabled,
    }
    return render(request, "accounts/setup_2fa.html", context)


@login_required
def disable_two_factor(request):
    """Disable TOTP-based two-factor authentication for the current user."""
    if request.user.user_type not in ["staff", "admin_staff", "admin", "borrower"]:
        messages.error(request, "Two-factor authentication is not available for this account type.")
        return redirect("accounts:profile")

    if request.method == "POST":
        token = request.POST.get("totp_code", "").strip()
        if not token:
            messages.error(request, "Please enter the authenticator code to disable 2FA.")
        elif TwoFactorAuthManager.verify_totp(request.user, token):
            request.user.two_factor_enabled = False
            request.user.otp_secret = ""
            request.user.save(update_fields=["two_factor_enabled", "otp_secret"])
            messages.success(request, "Two-factor authentication has been disabled.")
            return redirect("accounts:profile")
        else:
            messages.error(request, "The authenticator code was invalid. Please try again.")

    if not request.user.otp_secret:
        TwoFactorAuthManager.generate_totp_secret(request.user)

    context = {
        "otp_secret": request.user.otp_secret,
        "two_factor_enabled": request.user.two_factor_enabled,
        "disable_only": True,
    }
    return render(request, "accounts/setup_2fa.html", context)


@login_required
@admin_required
def register(request):
    """Create accounts for borrowers/students and administrative roles."""
    allowed_types = (
        ["borrower"]
        if request.user.user_type == "admin_staff"
        else ["borrower", "staff", "admin_staff", "admin"]
    )
    form = AdminRegistrationForm(request.POST or None, allowed_types=allowed_types)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "New user has been created successfully.")
        return redirect("accounts:manage_users")
    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    """View user profile"""
    return render(request, "accounts/profile.html")


@login_required
def edit_profile(request):
    """Edit user profile"""
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated!")
            return redirect("accounts:profile")
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, "accounts/edit_profile.html", {"form": form})


@login_required
def my_account(request):
    """View borrower's account - loans and holds"""
    from circulation.models import CheckoutRequest

    active_loans = (
        Loan.objects.filter(borrower=request.user, status="active")
        .select_related("item__publication")
        .order_by("due_date")
    )

    loan_history = (
        Loan.objects.filter(borrower=request.user, status__in=["returned", "overdue_returned"])
        .select_related("item__publication")
        .order_by("-return_date")[:10]
    )

    active_holds = (
        Hold.objects.filter(borrower=request.user, status__in=["waiting", "ready"])
        .select_related("publication")
        .order_by("hold_date")
    )

    checkout_requests = (
        CheckoutRequest.objects.filter(borrower=request.user, status__in=["pending", "approved"])
        .select_related("publication")
        .order_by("-request_date")
    )

    context = {
        "active_loans": active_loans,
        "loan_history": loan_history,
        "active_holds": active_holds,
        "checkout_requests": checkout_requests,
    }
    return render(request, "accounts/my_account.html", context)


@login_required
@staff_or_admin_required
def manage_users(request):
    """Staff/Admin view to manage users"""
    users = User.objects.all().order_by("-date_joined")
    search_query = request.GET.get("search", "")
    user_type_filter = request.GET.get("user_type", "")
    if request.user.user_type == "admin_staff":
        users = users.filter(is_superuser=False)

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
            | Q(library_card_number__icontains=search_query)
        )

    if user_type_filter:
        users = users.filter(user_type=user_type_filter)

    paginator = Paginator(users, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "search_query": search_query,
        "user_type_filter": user_type_filter,
    }
    return render(request, "accounts/manage_users.html", context)


@login_required
@staff_or_admin_required
def edit_user(request, user_id):
    """Staff can edit borrower profiles; admins can edit managed accounts."""
    users = User.objects.all()
    if request.user.user_type == "staff":
        users = users.filter(user_type="borrower")
    elif request.user.user_type == "admin_staff":
        users = users.filter(is_superuser=False)
    user = get_object_or_404(users, id=user_id)
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User {user.username} has been updated!")
            return redirect("accounts:manage_users")
    else:
        form = ProfileUpdateForm(instance=user)
    return render(request, "accounts/edit_user.html", {"form": form, "user_obj": user})


@login_required
@staff_or_admin_required
def reset_user_password(request, user_id):
    """Allow staff/admin to set a new password for a managed user."""
    users = User.objects.all()
    if request.user.user_type == "staff":
        users = users.filter(user_type="borrower")
    elif request.user.user_type == "admin_staff":
        users = users.filter(is_superuser=False)
    user = get_object_or_404(users, id=user_id)
    form = SetPasswordForm(user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Password reset for {user.username}. Share the temporary password securely.")
        return redirect("accounts:manage_users")
    return render(request, "accounts/reset_user_password.html", {"form": form, "user_obj": user})


@login_required
@admin_required
def delete_user(request, user_id):
    """Allow app admins to delete non-superuser accounts."""
    users = User.objects.all()
    if request.user.user_type == "admin_staff":
        users = users.filter(is_superuser=False)
    user = get_object_or_404(users, id=user_id)
    if user.pk == request.user.pk:
        return redirect("accounts:manage_users")
    if request.method == "POST":
        username = user.username
        user.delete()
        messages.success(request, f"User {username} has been deleted!")
        return redirect("accounts:manage_users")
    return render(request, "accounts/delete_user.html", {"user_obj": user})
