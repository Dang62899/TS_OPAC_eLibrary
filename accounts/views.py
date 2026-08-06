import random
from django.shortcuts import render, redirect, get_object_or_404
from .forms import build_login_challenge
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.core.cache import cache
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .forms import AdminRegistrationForm, BorrowerRegistrationForm, ProfileUpdateForm, LoginForm
from .decorators import admin_required, staff_or_admin_required
from circulation.models import Loan, Hold
from .models import User
from .security import AccountSecurityManager, TwoFactorAuthManager


def custom_login(request):
    """Custom login view with CAPTCHA and optional TOTP-based two-factor authentication."""
    if request.user.is_authenticated:
        if request.user.user_type == "admin":
            return redirect("circulation:admin_dashboard")
        elif request.user.user_type == "staff":
            return redirect("circulation:staff_dashboard")
        else:
            return redirect("accounts:my_account")

    auth_method = request.POST.get("auth_method", "") if request.method == "POST" else ""
    passkey_mode = auth_method == "passkey"

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
                    "passkey_mode": False,
                    "captcha_value": request.session.get("login_captcha_value"),
                    "captcha_prompt": request.session.get("login_captcha_prompt", "Enter the code shown in the image."),
                    "captcha_options": request.session.get("login_captcha_options", []),
                },
            )

        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data["username"], password=form.cleaned_data["password"])
            if user is None:
                if username:
                    AccountSecurityManager.record_failed_login(username)
                messages.error(request, "Invalid username or password.")
            else:
                auth_method = request.POST.get("auth_method")
                is_passkey_flow = auth_method == "passkey"

                if is_passkey_flow:
                    if not user.otp_secret:
                        messages.error(request, "This account has no authenticator secret. Please set up Google Authenticator in your profile first.")
                        return render(
                            request,
                            "accounts/login.html",
                            {
                                "form": form,
                                "requires_2fa": True,
                                "passkey_mode": True,
                                "username": user.username,
                                "captcha_value": request.session.get("login_captcha_value"),
                                "captcha_prompt": request.session.get("login_captcha_prompt", "Enter the code shown in the image."),
                                "captcha_options": request.session.get("login_captcha_options", []),
                            },
                        )

                    if not form.cleaned_data.get("totp_code"):
                        cache.set(f"pending_2fa_{user.id}", True, 300)
                        messages.info(request, "Please enter your Google Authenticator code to continue.")
                        return render(
                            request,
                            "accounts/login.html",
                            {
                                "form": form,
                                "requires_2fa": True,
                                "passkey_mode": True,
                                "auth_method": "passkey",
                                "username": user.username,
                                "captcha_value": request.session.get("login_captcha_value"),
                                "captcha_prompt": request.session.get("login_captcha_prompt", "Enter the code shown in the image."),
                                "captcha_options": request.session.get("login_captcha_options", []),
                            },
                        )

                    if not TwoFactorAuthManager.verify_totp(user, form.cleaned_data["totp_code"]):
                        messages.error(request, "Invalid Google Authenticator code.")
                        return render(
                            request,
                            "accounts/login.html",
                            {
                                "form": form,
                                "requires_2fa": True,
                                "passkey_mode": True,
                                "auth_method": "passkey",
                                "username": user.username,
                                "captcha_value": request.session.get("login_captcha_value"),
                                "captcha_prompt": request.session.get("login_captcha_prompt", "Enter the code shown in the image."),
                                "captcha_options": request.session.get("login_captcha_options", []),
                            },
                        )

                    cache.delete(f"pending_2fa_{user.id}")

                else:
                    if user.user_type in ["staff", "admin"] and getattr(user, "two_factor_enabled", False):
                        if not form.cleaned_data.get("totp_code"):
                            cache.set(f"pending_2fa_{user.id}", True, 300)
                            messages.info(request, "Please enter your authenticator code to continue.")
                            return render(
                                request,
                                "accounts/login.html",
                                {
                                    "form": form,
                                    "requires_2fa": True,
                                    "auth_method": auth_method,
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
                                    "auth_method": auth_method,
                                    "username": user.username,
                                    "captcha_value": request.session.get("login_captcha_value"),
                                    "captcha_prompt": request.session.get("login_captcha_prompt", "Enter the code shown in the image."),
                                    "captcha_options": request.session.get("login_captcha_options", []),
                                },
                            )

                        cache.delete(f"pending_2fa_{user.id}")

                auth_login(request, user)
                AccountSecurityManager.clear_failed_attempts(user.username)

                next_url = request.GET.get("next")
                if next_url:
                    return redirect(next_url)

                if user.user_type == "admin":
                    return redirect("circulation:admin_dashboard")
                elif user.user_type == "staff":
                    return redirect("circulation:staff_dashboard")
                else:
                    return redirect("accounts:my_account")
        else:
            messages.error(request, "Please correct the highlighted errors.")
    else:
        challenge = build_login_challenge()
        request.session["login_captcha_value"] = challenge["correct_value"]
        request.session["login_captcha_prompt"] = "Enter the distorted text shown in the image."
        request.session["login_captcha_options"] = challenge["samples"]
        request.session["login_captcha_image"] = challenge["image_data_url"]
        form = LoginForm(request=request)

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
            "requires_2fa": False,
            "passkey_mode": passkey_mode,
            "auth_method": auth_method,
            "captcha_value": request.session.get("login_captcha_value"),
            "captcha_prompt": request.session.get("login_captcha_prompt", "Enter the distorted text shown in the image."),
            "captcha_options": request.session.get("login_captcha_options", []),
            "captcha_image": request.session.get("login_captcha_image"),
        },
    )


@login_required
def setup_two_factor(request):
    """Enable or disable TOTP-based two-factor authentication for the current user."""
    if request.user.user_type not in ["staff", "admin", "borrower"]:
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
    if request.user.user_type not in ["staff", "admin", "borrower"]:
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


def register(request):
    """Register a new user"""
    if request.method == "POST":
        if request.user.is_authenticated and request.user.user_type == "admin":
            form = AdminRegistrationForm(request.POST, allowed_types=["staff", "admin"])
        else:
            form = BorrowerRegistrationForm(request.POST)

        if form.is_valid():
            form.save()
            if request.user.is_authenticated and request.user.user_type == "admin":
                messages.success(request, "New user has been created successfully.")
                return redirect("accounts:manage_users")
            messages.success(request, "Your account has been created! You can now log in.")
            return redirect("accounts:login")
    else:
        if request.user.is_authenticated and request.user.user_type == "admin":
            form = AdminRegistrationForm(allowed_types=["staff", "admin"])
        else:
            form = BorrowerRegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    """View user profile"""
    return render(request, "accounts/profile.html")


@login_required
def edit_profile(request):
    """Edit user profile"""
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, instance=request.user)
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
@admin_required
def edit_user(request, user_id):
    """Admin only - Edit any user"""
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"User {user.username} has been updated!")
            return redirect("accounts:manage_users")
    else:
        form = ProfileUpdateForm(instance=user)
    return render(request, "accounts/edit_user.html", {"form": form, "user_obj": user})


@login_required
@admin_required
def delete_user(request, user_id):
    """Admin only - Delete a user"""
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        username = user.username
        user.delete()
        messages.success(request, f"User {username} has been deleted!")
        return redirect("accounts:manage_users")
    return render(request, "accounts/delete_user.html", {"user_obj": user})
