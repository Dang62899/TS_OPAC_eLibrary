from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from catalog.models import Item, Location, Publication, PublicationType
from circulation.models import CheckoutRequest, Hold, Loan, Notification


class StateChangingMethodTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff = User.objects.create_user(
            username="circulation-staff",
            password="test-password",
            user_type="staff",
            agreed_to_terms=True,
        )
        self.borrower = User.objects.create_user(
            username="circulation-borrower",
            password="test-password",
            user_type="borrower",
            agreed_to_terms=True,
        )
        publication_type = PublicationType.objects.create(name="Manual", code="manual")
        self.publication = Publication.objects.create(
            title="Circulation POST Test",
            publication_type=publication_type,
        )
        location = Location.objects.create(name="Main", code="MAIN")
        item = Item.objects.create(
            publication=self.publication,
            location=location,
            barcode="POST-TEST-1",
            status="available",
        )
        self.loan = Loan.objects.create(
            item=item,
            borrower=self.borrower,
            due_date=timezone.now().date() + timezone.timedelta(days=14),
        )
        self.hold = Hold.objects.create(
            publication=self.publication,
            borrower=self.borrower,
            pickup_location=location,
        )
        self.notification = Notification.objects.create(
            borrower=self.borrower,
            notification_type="due_soon",
            title="Due soon",
        )

    def test_complete_checkout_request_get_renders_confirmation_form(self):
        item = Item.objects.create(
            publication=self.publication,
            location=self.hold.pickup_location,
            barcode="POST-TEST-REQUEST",
            status="on_hold_shelf",
        )
        checkout_request = CheckoutRequest.objects.create(
            publication=self.publication,
            borrower=self.borrower,
            status="approved",
            reserved_item=item,
        )
        self.client.force_login(self.staff)

        response = self.client.get(
            reverse("circulation:complete_checkout_request", args=[checkout_request.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Complete Checkout Request")
        self.assertContains(response, f"Item ID: {item.pk}")

    def test_state_changing_routes_reject_get(self):
        blocked_borrower = User.objects.create_user(
            username="blocked-borrower",
            password="test-password",
            user_type="borrower",
            is_blocked=True,
        )
        cases = [
            (self.staff, reverse("circulation:renew_loan", args=[self.loan.pk])),
            (self.borrower, reverse("circulation:renew_loan_online", args=[self.loan.pk])),
            (self.borrower, reverse("circulation:cancel_hold", args=[self.hold.pk])),
            (self.staff, reverse("circulation:unblock_borrower", args=[blocked_borrower.pk])),
            (self.borrower, reverse("circulation:mark_notification_read", args=[self.notification.pk])),
            (self.staff, reverse("circulation:set_hold_ready", args=[self.hold.pk])),
        ]

        for user, url in cases:
            with self.subTest(url=url):
                self.client.force_login(user)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 405)

        self.loan.refresh_from_db()
        self.hold.refresh_from_db()
        self.notification.refresh_from_db()
        blocked_borrower.refresh_from_db()
        self.assertEqual(self.loan.renewal_count, 0)
        self.assertEqual(self.hold.status, "waiting")
        self.assertFalse(self.notification.is_read)
        self.assertTrue(blocked_borrower.is_blocked)

    def test_notification_read_rejects_external_redirect_target(self):
        self.client.force_login(self.borrower)

        response = self.client.post(
            reverse("circulation:mark_notification_read", args=[self.notification.pk]),
            {"next": "https://attacker.example/"},
        )

        self.assertRedirects(response, reverse("circulation:notifications_list"))
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_checkout_and_checkin_reject_external_next_targets(self):
        self.client.force_login(self.staff)
        fallback = reverse("circulation:circulation_hub")

        for route in ["circulation:checkout", "circulation:checkin"]:
            with self.subTest(route=route):
                response = self.client.get(reverse(route), {"next": "https://attacker.example/"})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["next"], fallback)

    def test_blocked_borrower_cannot_place_hold(self):
        blocked_borrower = User.objects.create_user(
            username="blocked-hold-user",
            password="test-password",
            user_type="borrower",
            is_blocked=True,
            block_reason="Account requires staff review",
            agreed_to_terms=True,
        )
        self.client.force_login(blocked_borrower)

        response = self.client.post(
            reverse("circulation:place_hold", args=[self.publication.pk]),
            {"pickup_location": self.hold.pickup_location.pk},
        )

        self.assertRedirects(
            response,
            reverse("catalog:publication_detail", args=[self.publication.pk]),
        )
        self.assertFalse(Hold.objects.filter(borrower=blocked_borrower, publication=self.publication).exists())

    def test_blocked_borrower_cannot_request_checkout(self):
        blocked_borrower = User.objects.create_user(
            username="blocked-checkout-request",
            password="test-password",
            user_type="borrower",
            is_blocked=True,
            block_reason="Account requires staff review",
            agreed_to_terms=True,
        )
        Item.objects.create(
            publication=self.publication,
            location=self.hold.pickup_location,
            barcode="POST-TEST-REQUEST-AVAILABLE",
            status="available",
        )
        self.client.force_login(blocked_borrower)

        response = self.client.post(
            reverse("circulation:request_checkout", args=[self.publication.pk]),
            {"notes": "Blocked account test"},
        )

        self.assertRedirects(
            response,
            reverse("catalog:publication_detail", args=[self.publication.pk]),
        )
        self.assertFalse(
            CheckoutRequest.objects.filter(borrower=blocked_borrower, publication=self.publication).exists()
        )

    def test_blocked_borrower_cannot_renew_existing_loan(self):
        blocked_borrower = User.objects.create_user(
            username="blocked-renew-user",
            password="test-password",
            user_type="borrower",
            is_blocked=True,
            block_reason="Account requires staff review",
            agreed_to_terms=True,
        )
        self.loan.borrower = blocked_borrower
        self.loan.save(update_fields=["borrower"])
        self.client.force_login(blocked_borrower)

        response = self.client.post(reverse("circulation:renew_loan_online", args=[self.loan.pk]))

        self.assertRedirects(response, reverse("accounts:my_account"))
        self.loan.refresh_from_db()
        self.assertEqual(self.loan.renewal_count, 0)

    def test_blocked_borrower_cannot_complete_ready_hold(self):
        blocked_borrower = User.objects.create_user(
            username="blocked-complete-hold",
            password="test-password",
            user_type="borrower",
            is_blocked=True,
            block_reason="Account requires staff review",
            agreed_to_terms=True,
        )
        item = Item.objects.create(
            publication=self.publication,
            location=self.hold.pickup_location,
            barcode="POST-TEST-HOLD",
            status="on_hold_shelf",
        )
        hold = Hold.objects.create(
            publication=self.publication,
            borrower=blocked_borrower,
            pickup_location=self.hold.pickup_location,
            status="ready",
            reserved_item=item,
        )
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse("circulation:complete_hold", args=[hold.pk]),
            {"item_identifier": str(item.pk)},
        )

        self.assertRedirects(response, reverse("circulation:manage_holds"))
        self.assertFalse(Loan.objects.filter(item=item).exists())
        hold.refresh_from_db()
        self.assertEqual(hold.status, "ready")

    def test_staff_marking_hold_ready_reserves_an_available_item(self):
        item = Item.objects.create(
            publication=self.publication,
            location=self.hold.pickup_location,
            barcode="POST-TEST-READY",
            status="available",
        )
        self.client.force_login(self.staff)

        response = self.client.post(reverse("circulation:set_hold_ready", args=[self.hold.pk]))

        self.assertRedirects(response, reverse("circulation:manage_holds"))
        self.hold.refresh_from_db()
        item.refresh_from_db()
        self.assertEqual(self.hold.status, "ready")
        self.assertEqual(self.hold.reserved_item, item)
        self.assertEqual(item.status, "on_hold_shelf")

    def test_blocked_borrower_cannot_complete_approved_checkout_request(self):
        blocked_borrower = User.objects.create_user(
            username="blocked-complete-request",
            password="test-password",
            user_type="borrower",
            is_blocked=True,
            block_reason="Account requires staff review",
            agreed_to_terms=True,
        )
        item = Item.objects.create(
            publication=self.publication,
            location=self.hold.pickup_location,
            barcode="POST-TEST-REQUEST",
            status="on_hold_shelf",
        )
        checkout_request = CheckoutRequest.objects.create(
            publication=self.publication,
            borrower=blocked_borrower,
            status="approved",
            reserved_item=item,
        )
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse("circulation:complete_checkout_request", args=[checkout_request.pk]),
            {"item_identifier": str(item.pk)},
        )

        self.assertRedirects(response, reverse("circulation:manage_checkout_requests"))
        self.assertFalse(Loan.objects.filter(item=item).exists())
        checkout_request.refresh_from_db()
        self.assertEqual(checkout_request.status, "approved")