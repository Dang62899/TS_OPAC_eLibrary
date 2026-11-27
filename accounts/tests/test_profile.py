from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from accounts.forms import ProfileUpdateForm
from accounts.models import User


class ProfilePhotoTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="profile-user",
            password="test-password",
            email="profile@example.com",
            agreed_to_terms=True,
        )
        self.client.force_login(self.user)

    def test_profile_edit_persists_uploaded_photo(self):
        image_buffer = BytesIO()
        Image.new("RGB", (2, 2), color="navy").save(image_buffer, format="PNG")
        upload = SimpleUploadedFile("profile.png", image_buffer.getvalue(), content_type="image/png")

        response = self.client.post(
            reverse("accounts:edit_profile"),
            {"first_name": "Profile", "last_name": "User", "email": "profile@example.com", "photo": upload},
        )

        self.assertRedirects(response, reverse("accounts:profile"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.photo)
        self.assertTrue(self.user.photo.name.startswith("profiles/"))
        self.user.photo.delete(save=False)

    def test_profile_form_excludes_registry_fields(self):
        form = ProfileUpdateForm(instance=self.user)

        self.assertEqual(
            set(form.fields),
            {"first_name", "last_name", "email", "phone", "address", "date_of_birth", "photo"},
        )

    def test_forwarded_https_header_marks_proxy_request_secure(self):
        request = RequestFactory().get("/", HTTP_X_FORWARDED_PROTO="https")

        with override_settings(SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO", "https")):
            self.assertTrue(request.is_secure())

    @override_settings(MAX_PROFILE_PHOTO_SIZE_MB=1)
    def test_profile_edit_rejects_oversized_photo(self):
        import os

        image_buffer = BytesIO()
        Image.frombytes("RGB", (1000, 600), os.urandom(1000 * 600 * 3)).save(image_buffer, format="PNG")
        upload = SimpleUploadedFile("large.png", image_buffer.getvalue(), content_type="image/png")

        response = self.client.post(
            reverse("accounts:edit_profile"),
            {"first_name": "Profile", "last_name": "User", "email": "profile@example.com", "photo": upload},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "no larger than 1 MB")
        self.user.refresh_from_db()
        self.assertFalse(self.user.photo)

    def test_profile_displays_photo_without_registry_details(self):
        self.user.photo = SimpleUploadedFile("profile.png", b"profile-image", content_type="image/png")
        self.user.save(update_fields=["photo"])

        response = self.client.get(reverse("accounts:profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.photo.url)
        self.assertNotContains(response, "Registry status")
        self.assertNotContains(response, "Student class")
        self.user.photo.delete(save=False)

    def test_navigation_uses_uploaded_photo_as_account_avatar(self):
        self.user.photo = SimpleUploadedFile(
            "profile.png",
            b"profile-image",
            content_type="image/png",
        )
        self.user.save(update_fields=["photo"])

        response = self.client.get(reverse("catalog:index"))

        self.assertContains(response, 'class="account-menu__avatar"')
        self.assertContains(response, f'src="{self.user.photo.url}"')
        self.assertNotContains(response, 'class="bi bi-person-circle"')
        self.user.photo.delete(save=False)

    def test_navigation_shows_icon_when_no_profile_photo_is_uploaded(self):
        response = self.client.get(reverse("catalog:index"))

        self.assertContains(response, 'class="bi bi-person-circle"')

    def test_my_account_displays_account_without_registry_details(self):
        response = self.client.get(reverse("accounts:my_account"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Registry status")
        self.assertNotContains(response, "Student class")
