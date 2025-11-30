from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .forms import BorrowerRegistrationForm, ProfileUpdateForm
from .decorators import admin_required, staff_or_admin_required
from circulation.models import Loan, Hold
from .models import User


def custom_login(request):
    """Custom login view that redirects based on user type"""
    if request.user.is_authenticated:
        # Already logged in, redirect to appropriate page based on user type
        if request.user.user_type == "admin":
            return redirect("circulation:admin_dashboard")
        elif request.user.user_type == "staff":
            return redirect("circulation:staff_dashboard")
        else:
            return redirect("accounts:my_account")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")

            # Get next URL from GET parameter or default based on user type
            next_url = request.GET.get("next")
            if next_url:
                return redirect(next_url)

            # Redirect based on user type
            if user.user_type == "admin":
                return redirect("circulation:admin_dashboard")
            elif user.user_type == "staff":
                return redirect("circulation:staff_dashboard")
            else:
                return redirect("accounts:my_account")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, "accounts/login.html", {"form": form})


def register(request):
    """Register a new borrower"""
    if request.method == "POST":
        form = BorrowerRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your account has been created! You can now log in.")
            return redirect("accounts:login")
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
