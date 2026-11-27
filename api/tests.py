"""Tests for API endpoints"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from unittest.mock import patch
from catalog.models import Item, Publication, PublicationType, Location
from circulation.models import Hold, Loan
from django.utils import timezone

User = get_user_model()


class APIAuthenticationTests(TestCase):
    """Test API authentication"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )

    def test_token_auth(self):
        """Test obtaining authentication token"""
        response = self.client.post(
            "/api/v1/auth/token/",
            {"username": "testuser", "password": "testpass123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)

    def test_anonymous_user_registration_is_denied(self):
        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "username": "newuser",
                "email": "new@example.com",
                "password": "securepass123",
                "password_confirm": "securepass123",
            },
        )
        self.assertIn(response.status_code, (401, 403))
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_admin_staff_can_create_borrower_through_api(self):
        admin_staff = User.objects.create_user(
            username="api-admin-staff",
            password="test-password",
            user_type="admin_staff",
            agreed_to_terms=True,
        )
        self.client.force_authenticate(user=admin_staff)

        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "username": "api-created-borrower",
                "email": "new@example.com",
                "password": "securepass123",
                "password_confirm": "securepass123",
            },
        )

        self.assertEqual(response.status_code, 201)
        created = User.objects.get(username="api-created-borrower")
        self.assertEqual(created.user_type, "borrower")
        self.assertFalse(created.is_staff)
        self.assertFalse(created.is_superuser)

    def test_user_cannot_promote_their_own_account_through_api(self):
        self.user.agreed_to_terms = True
        self.user.save(update_fields=["agreed_to_terms"])
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            f"/api/v1/users/{self.user.pk}/",
            {"user_type": "admin", "is_active": True, "is_blocked": False},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.user_type, "borrower")
        self.assertFalse(self.user.is_superuser)

    def test_api_token_requires_totp_for_enrolled_staff(self):
        staff = User.objects.create_user(
            username="api-2fa-staff",
            password="staff-password",
            user_type="staff",
            two_factor_enabled=True,
            otp_secret="test-secret",
        )

        denied = self.client.post(
            "/api/v1/auth/token/",
            {"username": staff.username, "password": "staff-password"},
        )
        self.assertEqual(denied.status_code, 401)

        with patch("api.views.TwoFactorAuthManager.verify_totp", return_value=True):
            allowed = self.client.post(
                "/api/v1/auth/token/",
                {"username": staff.username, "password": "staff-password", "totp_code": "123456"},
            )
        self.assertEqual(allowed.status_code, 200)
        self.assertIn("token", allowed.data)

    def test_api_user_must_accept_agreement_before_using_protected_endpoints(self):
        token, _ = Token.objects.get_or_create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        denied = self.client.get("/api/v1/publications/")
        self.assertEqual(denied.status_code, 403)
        self.assertIn("detail", denied.data)

        accepted = self.client.post("/api/v1/auth/agreement/")
        self.assertEqual(accepted.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.agreed_to_terms)

        allowed = self.client.get("/api/v1/publications/")
        self.assertEqual(allowed.status_code, 200)


class APICatalogTests(TestCase):
    """Test catalog endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            agreed_to_terms=True,
        )
        self.client.force_authenticate(user=self.user)

    def test_list_publications(self):
        """Test listing publications"""
        response = self.client.get("/api/v1/publications/")
        self.assertEqual(response.status_code, 200)

    def test_list_requires_auth(self):
        """Test that publications list requires authentication"""
        client = APIClient()
        response = client.get("/api/v1/publications/")
        self.assertEqual(response.status_code, 401)

    def test_issued_token_authenticates_protected_api_requests(self):
        token_response = self.client.post(
            "/api/v1/auth/token/",
            {"username": self.user.username, "password": "testpass123"},
        )
        self.assertEqual(token_response.status_code, 200)

        token_client = APIClient()
        token_client.credentials(HTTP_AUTHORIZATION=f"Token {token_response.data['token']}")
        response = token_client.get("/api/v1/publications/")

        self.assertEqual(response.status_code, 200)

    def test_publication_borrow_action_creates_hold(self):
        publication_type = PublicationType.objects.create(name="Manual", code="manual")
        publication = Publication.objects.create(title="Borrow Action Test", publication_type=publication_type)
        location = Location.objects.create(name="Main Library", code="MAIN")

        response = self.client.post(
            f"/api/v1/publications/{publication.pk}/borrow/",
            {"pickup_location": location.pk},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Hold.objects.filter(publication=publication, borrower=self.user).exists())

    def test_blocked_borrower_cannot_use_publication_borrow_action(self):
        publication_type = PublicationType.objects.create(name="Manual", code="manual")
        publication = Publication.objects.create(title="Graduated Borrow Action", publication_type=publication_type)
        location = Location.objects.create(name="Main Library", code="MAIN")
        blocked_borrower = User.objects.create_user(
            username="blocked-borrow-action",
            password="test-password",
            user_type="borrower",
            is_blocked=True,
            block_reason="Account requires staff review",
        )
        self.client.force_authenticate(user=blocked_borrower)

        response = self.client.post(
            f"/api/v1/publications/{publication.pk}/borrow/",
            {"pickup_location": location.pk},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Hold.objects.filter(publication=publication, borrower=blocked_borrower).exists())

    def test_borrower_cannot_update_loan_through_api(self):
        publication_type = PublicationType.objects.create(name="Manual", code="manual")
        publication = Publication.objects.create(title="Loan Update Test", publication_type=publication_type)
        location = Location.objects.create(name="Main Library", code="MAIN")
        item = Item.objects.create(publication=publication, location=location, barcode="API-LOAN-1")
        loan = Loan.objects.create(
            item=item,
            borrower=self.user,
            due_date=timezone.now().date() + timezone.timedelta(days=14),
        )

        response = self.client.patch(
            f"/api/v1/loans/{loan.pk}/",
            {"due_date": "2030-01-01", "renewal_count": 99},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        loan.refresh_from_db()
        self.assertNotEqual(str(loan.due_date), "2030-01-01")
        self.assertEqual(loan.renewal_count, 0)

    def test_borrower_cannot_update_hold_through_api(self):
        publication_type = PublicationType.objects.create(name="Manual", code="manual")
        publication = Publication.objects.create(title="Hold Update Test", publication_type=publication_type)
        location = Location.objects.create(name="Main Library", code="MAIN")
        other_location = Location.objects.create(name="Archive", code="ARCHIVE")
        hold = Hold.objects.create(publication=publication, borrower=self.user, pickup_location=location)

        response = self.client.patch(
            f"/api/v1/holds/{hold.pk}/",
            {"pickup_location": other_location.pk},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        hold.refresh_from_db()
        self.assertEqual(hold.pickup_location, location)

    def test_staff_completing_hold_uses_valid_fulfilled_status(self):
        publication_type = PublicationType.objects.create(name="Manual", code="manual")
        publication = Publication.objects.create(title="Complete Hold Test", publication_type=publication_type)
        location = Location.objects.create(name="Main Library", code="MAIN")
        item = Item.objects.create(
            publication=publication,
            location=location,
            barcode="API-COMPLETE-HOLD",
            status="on_hold_shelf",
        )
        hold = Hold.objects.create(
            publication=publication,
            borrower=self.user,
            pickup_location=location,
            status="ready",
            reserved_item=item,
        )
        staff = User.objects.create_user(
            username="hold-completion-staff",
            password="staff-password",
            user_type="staff",
            agreed_to_terms=True,
        )
        self.client.force_authenticate(user=staff)

        response = self.client.post(f"/api/v1/holds/{hold.pk}/complete/")

        self.assertEqual(response.status_code, 200)
        hold.refresh_from_db()
        self.assertEqual(hold.status, "fulfilled")
        loan = Loan.objects.get(item=item, borrower=self.user)
        self.assertEqual(loan.checkout_staff, staff)

    def test_staff_marking_hold_ready_reserves_available_item(self):
        publication_type = PublicationType.objects.create(name="Manual", code="manual")
        publication = Publication.objects.create(title="Ready Hold Test", publication_type=publication_type)
        location = Location.objects.create(name="Main Library", code="MAIN")
        hold = Hold.objects.create(publication=publication, borrower=self.user, pickup_location=location)
        item = Item.objects.create(
            publication=publication,
            location=location,
            barcode="API-READY-HOLD",
            status="available",
        )
        staff = User.objects.create_user(
            username="hold-ready-staff",
            password="staff-password",
            user_type="staff",
            agreed_to_terms=True,
        )
        self.client.force_authenticate(user=staff)

        response = self.client.post(f"/api/v1/holds/{hold.pk}/set_ready/")

        self.assertEqual(response.status_code, 200)
        hold.refresh_from_db()
        item.refresh_from_db()
        self.assertEqual(hold.status, "ready")
        self.assertEqual(item.status, "on_hold_shelf")
        hold.refresh_from_db()
        self.assertEqual(hold.reserved_item, item)

    def test_borrower_cannot_change_hold_staff_status(self):
        publication_type = PublicationType.objects.create(name="Manual", code="manual")
        publication = Publication.objects.create(title="Hold Permissions Test", publication_type=publication_type)
        location = Location.objects.create(name="Main Library", code="MAIN")
        hold = Hold.objects.create(publication=publication, borrower=self.user, pickup_location=location)

        ready = self.client.post(f"/api/v1/holds/{hold.pk}/set_ready/")
        complete = self.client.post(f"/api/v1/holds/{hold.pk}/complete/")

        self.assertEqual(ready.status_code, 403)
        self.assertEqual(complete.status_code, 403)
        hold.refresh_from_db()
        self.assertEqual(hold.status, "waiting")

    def test_staff_can_read_borrower_stats_api(self):
        staff = User.objects.create_user(
            username="api-stats-staff",
            password="staff-password",
            user_type="staff",
            agreed_to_terms=True,
        )
        self.client.force_authenticate(user=staff)

        response = self.client.get(f"/api/v1/users/{self.user.pk}/stats/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("borrowing_limit", response.data)
        self.assertEqual(response.data["borrowing_limit"], self.user.max_items_allowed)

    def test_blocked_borrower_cannot_renew_loan_through_api(self):
        publication_type = PublicationType.objects.create(name="Manual", code="manual")
        publication = Publication.objects.create(title="Graduate Renew Test", publication_type=publication_type)
        location = Location.objects.create(name="Main Library", code="MAIN")
        item = Item.objects.create(publication=publication, location=location, barcode="API-RENEW-1")
        blocked_borrower = User.objects.create_user(
            username="blocked-api-renew",
            password="test-password",
            user_type="borrower",
            is_blocked=True,
            block_reason="Account requires staff review",
        )
        loan = Loan.objects.create(
            item=item,
            borrower=blocked_borrower,
            due_date=timezone.now().date() + timezone.timedelta(days=14),
        )
        self.client.force_authenticate(user=blocked_borrower)

        response = self.client.post(f"/api/v1/loans/{loan.pk}/renew/")

        self.assertEqual(response.status_code, 403)
        loan.refresh_from_db()
        self.assertEqual(loan.renewal_count, 0)

    def test_staff_api_cannot_create_loan_for_blocked_borrower(self):
        publication_type = PublicationType.objects.create(name="Manual", code="manual")
        publication = Publication.objects.create(title="Graduated Loan Create", publication_type=publication_type)
        location = Location.objects.create(name="Main Library", code="MAIN")
        item = Item.objects.create(publication=publication, location=location, barcode="API-GRAD-LOAN")
        blocked_borrower = User.objects.create_user(
            username="blocked-api-loan-create",
            password="test-password",
            user_type="borrower",
            is_blocked=True,
            block_reason="Account requires staff review",
            agreed_to_terms=True,
        )
        staff = User.objects.create_user(
            username="loan-create-staff",
            password="staff-password",
            user_type="staff",
            agreed_to_terms=True,
        )
        self.client.force_authenticate(user=staff)

        response = self.client.post(
            "/api/v1/loans/",
            {
                "item": item.pk,
                "borrower": blocked_borrower.pk,
                "due_date": (timezone.now().date() + timezone.timedelta(days=14)).isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Loan.objects.filter(item=item, borrower=blocked_borrower).exists())

    def test_borrower_can_create_hold_through_api(self):
        publication_type = PublicationType.objects.create(name="Manual", code="manual")
        publication = Publication.objects.create(title="API Hold Test", publication_type=publication_type)
        location = Location.objects.create(name="Main Library", code="MAIN")

        response = self.client.post(
            "/api/v1/holds/",
            {"publication": publication.pk, "pickup_location": location.pk},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["borrower"], self.user.pk)
        self.assertEqual(response.data["queue_position"], 1)
        self.assertEqual(Hold.objects.filter(borrower=self.user, publication=publication).count(), 1)

    def test_blocked_borrower_cannot_create_api_hold(self):
        publication_type = PublicationType.objects.create(name="Manual", code="manual")
        publication = Publication.objects.create(title="Graduated Hold Test", publication_type=publication_type)
        location = Location.objects.create(name="Main Library", code="MAIN")
        blocked_borrower = User.objects.create_user(
            username="blocked-api-user",
            password="test-password",
            user_type="borrower",
            is_blocked=True,
            block_reason="Account requires staff review",
        )
        self.client.force_authenticate(user=blocked_borrower)

        response = self.client.post(
            "/api/v1/holds/",
            {"publication": publication.pk, "pickup_location": location.pk},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Hold.objects.filter(borrower=blocked_borrower, publication=publication).exists())
