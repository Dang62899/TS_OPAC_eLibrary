from django.test import TestCase
from django.test import Client

from accounts.forms import build_login_challenge
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
            agreed_to_terms=True,
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
        self.assertRedirects(response, "/")

    def test_passkey_submission_cannot_authenticate(self):
        client = Client()
        client.get("/accounts/login/")
        response = client.post(
            "/accounts/login/",
            {
                "username": self.user.username,
                "captcha": client.session["login_captcha_value"],
                "auth_method": "passkey",
                "totp_code": pyotp.TOTP(self.user.otp_secret or pyotp.random_base32()).now(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", client.session)
        self.assertNotContains(response, "passkey")

    def test_regular_login_still_requires_password(self):
        client = Client()
        client.get("/accounts/login/")
        response = client.post(
            "/accounts/login/",
            {"username": self.user.username, "captcha": client.session["login_captcha_value"]},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", client.session)

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
            agreed_to_terms=True,
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
        self.assertContains(response, "Security check")
        self.assertContains(response, "Type the characters you see in the image.")

    def test_login_page_displays_generated_captcha_challenge(self):
        client = Client()
        response = client.get("/accounts/login/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Security check")
        self.assertContains(response, "Type the characters you see in the image.")
        self.assertContains(response, 'name="captcha"')

    def test_login_page_uses_image_captcha_instead_of_option_grid(self):
        client = Client()
        response = client.get("/accounts/login/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "captcha-image")
        self.assertNotContains(response, "captcha-option-btn")

    def test_login_page_renders_distorted_captcha_image(self):
        client = Client()
        response = client.get("/accounts/login/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "captcha-image")

    def test_login_challenge_is_randomly_generated(self):
        values = {build_login_challenge()["correct_value"] for _ in range(20)}

        self.assertGreater(len(values), 15)
        for value in values:
            self.assertIn(len(value), (5, 6))
            self.assertTrue(value.isalnum() and value.isupper() or value.isdigit())

    def test_login_page_uses_modern_auth_layout(self):
        client = Client()
        response = client.get("/accounts/login/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'auth-shell')
        self.assertContains(response, 'auth-illustration')
        self.assertContains(response, 'auth-panel')
        self.assertNotContains(response, "passkey")
        self.assertNotContains(response, 'class="site-header"')
        self.assertContains(response, "images/9532_training_squadron_seal.png")
        self.assertContains(response, 'class="project-seal"')
        self.assertNotContains(response, "brand-badge")
        self.assertNotContains(response, "login-submit-seal")
        self.assertContains(response, "class=\"login-panel-footer\"")
        self.assertContains(response, "9533rd Research and Development Squadron | Jacksone Agtarap")
