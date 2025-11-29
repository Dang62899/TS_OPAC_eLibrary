from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Extended User model for library system"""

    USER_TYPES = (
        ("borrower", "Borrower"),
        ("staff", "Staff"),
        ("admin", "Administrator"),
    )

    user_type = models.CharField(max_length=20, choices=USER_TYPES, default="borrower")
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    library_card_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    is_blocked = models.BooleanField(default=False)
    block_reason = models.TextField(blank=True)
    max_items_allowed = models.IntegerField(default=5)

    class Meta:
        ordering = ["username"]

    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"

    def can_borrow(self):
        """Check if user can borrow items"""
        if self.is_blocked:
            return False
        from circulation.models import Loan

        current_loans = Loan.objects.filter(borrower=self, status="active").count()
        return current_loans < self.max_items_allowed

    def get_active_loans_count(self):
        """Get number of active loans"""
        from circulation.models import Loan

        return Loan.objects.filter(borrower=self, status="active").count()
