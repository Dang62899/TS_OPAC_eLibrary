from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from accounts.forms import AdminRegistrationForm
from accounts.models import User


class StaffUserManagementTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="staff-manager",
            password="test-password",
            user_type="staff",
            agreed_to_terms=True,
        )
        self.client.force_login(self.staff)

    def _registration_data(self, username, user_type="borrower"):
        return {
            "username": username,
            "email": f"{username}@example.com",
            "first_name": "New",
            "last_name": "Account",
            "password1": "ValidPass123!",
            "password2": "ValidPass123!",
            "user_type": user_type,
        }

    def test_staff_can_manage_borrowers_but_cannot_create_accounts(self):
        borrower = User.objects.create_user(
            username="managed-borrower",
            password="test-password",
            user_type="borrower",
        )
        another_staff = User.objects.create_user(
            username="another-staff",
            password="old-password",
            user_type="staff",
        )

        register_response = self.client.get(reverse("accounts:register"))
        manage_response = self.client.get(reverse("accounts:manage_users"))

        self.assertEqual(register_response.status_code, 302)
        self.assertNotContains(manage_response, "Add borrower/student")
        self.assertContains(manage_response, "Reset password")
        self.assertNotContains(
            manage_response,
            reverse("accounts:reset_user_password", args=[another_staff.pk]),
        )
        self.assertContains(
            manage_response,
            reverse("accounts:reset_user_password", args=[borrower.pk]),
        )

    def test_manage_users_filters_by_role_without_registry_fields(self):
        User.objects.create_user(username="filter-borrower", password="x", user_type="borrower")
        User.objects.create_user(username="filter-admin-staff", password="x", user_type="admin_staff")

        response = self.client.get(
            reverse("accounts:manage_users"),
            {"user_type": "borrower"},
        )

        self.assertContains(response, "filter-borrower")
        self.assertNotContains(response, "filter-admin-staff")
        self.assertContains(response, 'name="user_type"')
        self.assertNotContains(response, "Registry status")
        self.assertNotContains(response, "Unit / class")

    def test_manage_users_displays_borrower_profile_photo(self):
        borrower = User.objects.create_user(
            username="photo-borrower",
            password="test-password",
            user_type="borrower",
            photo=SimpleUploadedFile("profile.png", b"image-data"),
        )

        response = self.client.get(reverse("accounts:manage_users"))

        self.assertContains(response, borrower.photo.url)
        borrower.photo.delete(save=False)

    def test_admin_staff_can_create_borrower_student_accounts(self):
        admin_staff = User.objects.create_user(
            username="account-admin-staff",
            password="test-password",
            user_type="admin_staff",
            agreed_to_terms=True,
        )
        self.client.force_login(admin_staff)

        response = self.client.post(
            reverse("accounts:register"),
            self._registration_data("new-borrower"),
        )

        self.assertRedirects(response, reverse("accounts:manage_users"))
        borrower = User.objects.get(username="new-borrower")
        self.assertEqual(borrower.user_type, "borrower")
        self.assertFalse(borrower.is_staff)
        self.assertFalse(borrower.is_superuser)

    def test_admin_staff_cannot_create_privileged_accounts(self):
        admin_staff = User.objects.create_user(
            username="limited-admin-staff",
            password="test-password",
            user_type="admin_staff",
            agreed_to_terms=True,
        )
        self.client.force_login(admin_staff)

        response = self.client.post(
            reverse("accounts:register"),
            self._registration_data("attempted-admin", "admin"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="attempted-admin").exists())

    def test_admin_staff_has_app_admin_access_but_not_superuser_access(self):
        admin_staff = User.objects.create_user(
            username="limited-admin",
            password="test-password",
            user_type="admin_staff",
            agreed_to_terms=True,
        )
        superuser = User.objects.create_user(
            username="root-admin",
            password="test-password",
            user_type="admin",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(admin_staff)

        self.assertFalse(admin_staff.is_staff)
        self.assertFalse(admin_staff.is_superuser)
        self.assertEqual(self.client.get(reverse("catalog:manage_publications")).status_code, 200)
        manage_response = self.client.get(reverse("accounts:manage_users"))
        self.assertNotContains(manage_response, superuser.username)
        for route in ("edit_user", "reset_user_password", "delete_user"):
            response = self.client.get(reverse(f"accounts:{route}", args=[superuser.pk]))
            self.assertEqual(response.status_code, 404)

    def test_admin_registration_can_create_admin_staff_without_superuser_access(self):
        form = AdminRegistrationForm(
            data=self._registration_data("new-admin-staff", "admin_staff"),
        )

        self.assertTrue(form.is_valid(), form.errors)
        admin_staff = form.save()
        self.assertEqual(admin_staff.user_type, "admin_staff")
        self.assertTrue(admin_staff.is_library_admin)
        self.assertFalse(admin_staff.is_staff)
        self.assertFalse(admin_staff.is_superuser)

    def test_admin_registration_sets_superuser_permissions(self):
        form = AdminRegistrationForm(
            data=self._registration_data("new-admin", "admin"),
        )

        self.assertTrue(form.is_valid(), form.errors)
        admin_user = form.save()
        self.assertEqual(admin_user.user_type, "admin")
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)

    def test_staff_can_edit_borrower_profile_but_cannot_promote_account(self):
        borrower = User.objects.create_user(
            username="existing-borrower",
            password="test-password",
            user_type="borrower",
        )

        response = self.client.post(
            reverse("accounts:edit_user", args=[borrower.pk]),
            {
                "first_name": "Updated",
                "last_name": "Name",
                "email": "updated@example.com",
                "user_type": "admin",
            },
        )

        self.assertRedirects(response, reverse("accounts:manage_users"))
        borrower.refresh_from_db()
        self.assertEqual(borrower.first_name, "Updated")
        self.assertEqual(borrower.user_type, "borrower")

    def test_borrower_can_borrow_without_registry_status(self):
        borrower = User.objects.create_user(
            username="eligible-borrower",
            password="test-password",
            user_type="borrower",
        )

        self.assertTrue(borrower.can_borrow())

    def test_staff_account_is_not_eligible_for_borrowing(self):
        self.assertFalse(self.staff.can_borrow())

    def test_staff_can_reset_borrower_password(self):
        borrower = User.objects.create_user(
            username="password-target",
            password="old-password",
            user_type="borrower",
        )

        response = self.client.post(
            reverse("accounts:reset_user_password", args=[borrower.pk]),
            {"new_password1": "NewSecurePass123!", "new_password2": "NewSecurePass123!"},
        )

        self.assertRedirects(response, reverse("accounts:manage_users"))
        borrower.refresh_from_db()
        self.assertTrue(borrower.check_password("NewSecurePass123!"))

    def test_staff_cannot_edit_or_reset_staff_account(self):
        another_staff = User.objects.create_user(
            username="another-staff",
            password="old-password",
            user_type="staff",
        )

        edit_response = self.client.get(reverse("accounts:edit_user", args=[another_staff.pk]))
        reset_response = self.client.get(reverse("accounts:reset_user_password", args=[another_staff.pk]))

        self.assertEqual(edit_response.status_code, 404)
        self.assertEqual(reset_response.status_code, 404)

    def test_anonymous_user_can_reach_django_admin_login(self):
        anonymous_client = Client()

        response = anonymous_client.get(reverse("admin:login"))

        self.assertEqual(response.status_code, 200)
