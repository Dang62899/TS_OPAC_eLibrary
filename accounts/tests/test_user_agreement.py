from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User


class UserAgreementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="agreeuser", password="pass1234", email="agree@example.com")

    def test_user_agreement_flow(self):
        self.client.login(username="agreeuser", password="pass1234")
        url = reverse("accounts:user_agreement")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        # Post acceptance
        resp = self.client.post(url, {"accept_agreement": "on"})
        self.assertRedirects(resp, reverse("catalog:index"), fetch_redirect_response=False)
        self.assertEqual(self.client.session.get("_auth_user_id"), str(self.user.pk))
        self.user.refresh_from_db()
        self.assertTrue(self.user.agreed_to_terms)
        self.assertIsNotNone(self.user.agreed_at)

    def test_home_navigation_is_available_after_agreement(self):
        self.user.agreed_to_terms = True
        self.user.save(update_fields=["agreed_to_terms"])
        self.client.force_login(self.user)

        response = self.client.get(reverse("catalog:index"))

        self.assertContains(response, f'href="{reverse("catalog:index")}">Home</a>')
        self.assertEqual(self.client.session.get("_auth_user_id"), str(self.user.pk))

    def test_multiple_users_can_remain_signed_in_in_separate_sessions(self):
        self.user.agreed_to_terms = True
        self.user.save(update_fields=["agreed_to_terms"])
        second_user = User.objects.create_user(
            username="second-agreeuser",
            password="test-password",
            email="second-agree@example.com",
            agreed_to_terms=True,
        )
        second_client = Client()

        self.client.force_login(self.user)
        second_client.force_login(second_user)

        self.assertNotEqual(
            self.client.session.session_key,
            second_client.session.session_key,
        )
        self.assertEqual(self.client.get(reverse("catalog:index")).status_code, 200)
        self.assertEqual(
            second_client.get(reverse("catalog:index")).status_code,
            200,
        )
        self.assertEqual(self.client.session.get("_auth_user_id"), str(self.user.pk))
        self.assertEqual(
            second_client.session.get("_auth_user_id"),
            str(second_user.pk),
        )

    def test_user_agreement_requires_explicit_acceptance(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("accounts:user_agreement"), {})

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.agreed_to_terms)
        self.assertIsNone(self.user.agreed_at)

    def test_unaccepted_user_is_redirected_to_agreement(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("catalog:index"))

        self.assertRedirects(response, reverse("accounts:user_agreement"))


class AdminHomeNavigationTests(TestCase):
    def test_admin_without_agreement_can_open_home_and_stays_logged_in(self):
        admin = User.objects.create_user(username="adm1", password="x", user_type="admin", is_staff=True, is_superuser=True)
        self.client.force_login(admin)
        response = self.client.get(reverse("catalog:index"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session.get("_auth_user_id"), str(admin.pk))
