from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "email", "first_name", "last_name", "user_type", "is_blocked", "library_card_number"]
    list_filter = ["user_type", "is_blocked", "is_staff", "is_active"]
    search_fields = ["username", "email", "first_name", "last_name", "library_card_number"]

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Library Information",
            {"fields": ("user_type", "library_card_number", "phone", "address", "date_of_birth", "max_items_allowed")},
        ),
        ("Borrowing Status", {"fields": ("is_blocked", "block_reason")}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Additional Information", {"fields": ("user_type", "email", "first_name", "last_name")}),
    )
