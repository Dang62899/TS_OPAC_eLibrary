from django.test import Client, TestCase
from django.urls import reverse
import pyotp

from accounts.models import User


class LoginRedirectTests(TestCase):
    def test_successful_login_redirects_home_even_with_external_next(self):
        user = User.objects.create_user(
            username="redirect-borrower",
            password="test-password",
            user_type="borrower",
        )
        client = Client()
        login_url = f"{reverse('accounts:login')}?next=https://attacker.example/"
        client.get(login_url)
        captcha = client.session["login_captcha_value"]

        response = client.post(
            login_url,
            {"username": user.username, "password": "test-password", "captcha": captcha},
        )

        self.assertRedirects(response, reverse("catalog:index"), fetch_redirect_response=False)

    def test_authenticated_user_visiting_login_is_sent_home(self):
        for user_type in ("borrower", "staff", "admin_staff", "admin"):
            with self.subTest(user_type=user_type):
                user = User.objects.create_user(
                    username=f"{user_type}-returning-user",
                    password="test-password",
                    user_type=user_type,
                    is_staff=user_type == "admin",
                    is_superuser=user_type == "admin",
                    agreed_to_terms=True,
                )
                client = Client()
                client.force_login(user)

                response = client.get(reverse("accounts:login"))

                self.assertRedirects(response, reverse("catalog:index"), fetch_redirect_response=False)

    def test_enabled_borrower_two_factor_is_not_bypassed_by_regular_login(self):
        user = User.objects.create_user(
            username="two-factor-borrower",
            password="test-password",
            user_type="borrower",
            two_factor_enabled=True,
            otp_secret=pyotp.random_base32(),
        )
        client = Client()
        login_url = reverse("accounts:login")
        client.get(login_url)

        response = client.post(
            login_url,
            {
                "username": user.username,
                "password": "test-password",
                "captcha": client.session["login_captcha_value"],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(client.session.get("_auth_user_id"))

    def test_brand_home_destination_preserves_authenticated_session(self):
        user = User.objects.create_user(
            username="brand-link-user",
            password="test-password",
            user_type="borrower",
            agreed_to_terms=True,
        )
        client = Client()
        client.force_login(user)

        response = client.get(reverse("catalog:index"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(client.session.get("_auth_user_id"), str(user.pk))