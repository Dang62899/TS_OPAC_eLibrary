from django.test import TestCase
from django.test import Client
from django.core.cache import cache

from accounts.models import User
from accounts.security import TwoFactorAuthManager
import pyotp


class TwoFactorAuthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="SecurePass123!",
            user_type="staff",
        )

    def test_generate_totp_secret_persists_secret_for_user(self):
        secret = TwoFactorAuthManager.generate_totp_secret(self.user)

        self.user.refresh_from_db()
        self.assertTrue(secret)
        self.assertEqual(self.user.otp_secret, secret)
        self.assertFalse(self.user.two_factor_enabled)

    def test_verify_totp_uses_stored_secret(self):
        secret = TwoFactorAuthManager.generate_totp_secret(self.user)
        token = pyotp.TOTP(secret).now()

        self.assertTrue(TwoFactorAuthManager.verify_totp(self.user, token))

    def test_staff_account_without_2fa_does_not_require_totp(self):
        self.user.two_factor_enabled = False
        self.user.save(update_fields=["two_factor_enabled"])

        client = Client()
        client.get("/accounts/login/")
        captcha_value = client.session["login_captcha_value"]

        response = client.post(
            "/accounts/login/",
            {
                "username": self.user.username,
                "password": "SecurePass123!",
                "captcha": captcha_value,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, "/circulation/staff-dashboard/")

    def test_passkey_mode_prompts_for_totp_code(self):
        self.user.otp_secret = pyotp.random_base32()
        self.user.save(update_fields=["otp_secret"])

        client = Client()
        response = client.get("/accounts/login/")
        captcha_value = client.session["login_captcha_value"]

        response = client.post(
            "/accounts/login/",
            {
                "username": self.user.username,
                "password": "SecurePass123!",
                "captcha": captcha_value,
                "auth_method": "passkey",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter your Google Authenticator code")
        self.assertContains(response, "name=\"auth_method\" value=\"passkey\"")

    def test_disabling_two_factor_requires_valid_code(self):
        self.user.two_factor_enabled = True
        self.user.otp_secret = pyotp.random_base32()
        self.user.save(update_fields=["two_factor_enabled", "otp_secret"])

        client = Client()
        client.force_login(self.user)
        response = client.post("/accounts/disable-2fa/", follow=True)

        self.assertContains(response, "Please enter the authenticator code")
        self.user.refresh_from_db()
        self.assertTrue(self.user.two_factor_enabled)

    def test_setup_page_shows_disable_action_when_two_factor_enabled(self):
        self.user.two_factor_enabled = True
        self.user.otp_secret = pyotp.random_base32()
        self.user.save(update_fields=["two_factor_enabled", "otp_secret"])

        client = Client()
        client.force_login(self.user)
        response = client.get("/accounts/setup-2fa/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Disable 2FA")

    def test_regular_user_can_access_2fa_management_page(self):
        borrower = User.objects.create_user(
            username="borrower",
            email="borrower@example.com",
            password="SecurePass123!",
            user_type="borrower",
        )
        borrower.two_factor_enabled = True
        borrower.otp_secret = pyotp.random_base32()
        borrower.save(update_fields=["two_factor_enabled", "otp_secret"])

        client = Client()
        client.force_login(borrower)
        response = client.get("/accounts/setup-2fa/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Disable 2FA")

    def test_login_page_displays_captcha_challenge(self):
        client = Client()
        response = client.get("/accounts/login/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Captcha challenge")
        self.assertContains(response, "Select the icon")

    def test_login_page_displays_generated_captcha_challenge(self):
        client = Client()
        response = client.get("/accounts/login/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Captcha challenge")
        self.assertContains(response, "Enter the code shown in the image")
        self.assertContains(response, 'name="captcha"')

    def test_login_page_displays_visual_captcha_option_grid(self):
        client = Client()
        response = client.get("/accounts/login/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "captcha-option-btn")

    def test_login_page_renders_distorted_captcha_image(self):
        client = Client()
        response = client.get("/accounts/login/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "captcha-image")
