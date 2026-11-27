from django.test import TestCase
from django.urls import reverse

from accounts.forms import AdminRegistrationForm, BorrowerRegistrationForm
from accounts.models import User


class AccountCreationAccessTests(TestCase):
    def _registration_data(self, username, user_type="borrower"):
        return {
            "username": username,
            "email": f"{username}@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password1": "ValidPass123!",
            "password2": "ValidPass123!",
            "user_type": user_type,
        }

    def _login_admin(self, user_type):
        admin = User.objects.create_user(
            username=f"{user_type}-creator",
            password="test-password",
            user_type=user_type,
            is_staff=user_type == "admin",
            is_superuser=user_type == "admin",
            agreed_to_terms=True,
        )
        self.client.force_login(admin)
        return admin

    def test_registration_forms_have_no_registry_fields(self):
        registry_fields = {"service_number", "student_class", "unit", "status", "date_enrolled", "date_graduated"}

        self.assertTrue(registry_fields.isdisjoint(BorrowerRegistrationForm().fields))
        self.assertTrue(registry_fields.isdisjoint(AdminRegistrationForm().fields))

    def test_anonymous_users_cannot_create_accounts(self):
        response = self.client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 302)

        response = self.client.post(
            reverse("accounts:register"),
            self._registration_data("anonymous-account"),
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(username="anonymous-account").exists())

    def test_borrower_and_regular_staff_cannot_create_accounts(self):
        for user_type in ("borrower", "staff"):
            with self.subTest(user_type=user_type):
                account = User.objects.create_user(
                    username=f"{user_type}-account",
                    password="test-password",
                    user_type=user_type,
                )
                self.client.force_login(account)

                response = self.client.post(
                    reverse("accounts:register"),
                    self._registration_data(f"{user_type}-created-account"),
                )

                self.assertEqual(response.status_code, 302)
                self.assertFalse(
                    User.objects.filter(username=f"{user_type}-created-account").exists()
                )

    def test_admin_staff_can_create_borrower_accounts_only(self):
        self._login_admin("admin_staff")
        register_url = reverse("accounts:register")
        response = self.client.get(register_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["form"].fields["user_type"].choices),
            [("borrower", "Borrower / Student")],
        )

        response = self.client.post(
            register_url,
            self._registration_data("staff-created-borrower", "borrower"),
        )

        self.assertRedirects(response, reverse("accounts:manage_users"))
        self.assertEqual(User.objects.get(username="staff-created-borrower").user_type, "borrower")

        response = self.client.post(
            register_url,
            self._registration_data("staff-created-admin", "admin"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="staff-created-admin").exists())

    def test_administrator_can_create_admin_staff_accounts(self):
        self._login_admin("admin")

        response = self.client.post(
            reverse("accounts:register"),
            self._registration_data("administrator-created-staff", "admin_staff"),
        )

        self.assertRedirects(response, reverse("accounts:manage_users"))
        user = User.objects.get(username="administrator-created-staff")
        self.assertEqual(user.user_type, "admin_staff")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
