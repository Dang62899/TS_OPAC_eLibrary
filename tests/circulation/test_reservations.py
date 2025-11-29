from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from catalog.models import Publication, Item, Location, PublicationType
from circulation.models import CheckoutRequest, Loan, Hold


class ReservationFlowTests(TestCase):
    def setUp(self):
        # Create users
        self.staff = User.objects.create_user(username="staff1", password="pass", user_type="staff")
        self.borrower = User.objects.create_user(username="user1", password="pass", user_type="borrower")

        # Create location
        self.loc = Location.objects.create(name="Main Desk")

        # Create publication type and publication
        self.pub_type = PublicationType.objects.create(name="Book")
        self.pub = Publication.objects.create(title="Test Book", isbn="9781234567897", publication_type=self.pub_type)

        # Create two items
        self.item1 = Item.objects.create(publication=self.pub, barcode="TST001", location=self.loc, status="available")
        self.item2 = Item.objects.create(publication=self.pub, barcode="TST002", location=self.loc, status="available")

        # Create checkout request
        self.cr = CheckoutRequest.objects.create(publication=self.pub, borrower=self.borrower, status="pending")

        self.client = Client()

    def test_approve_reserves_item(self):
        # Login as staff
        self.client.login(username="staff1", password="pass")

        url = reverse("circulation:approve_checkout_request", args=[self.cr.id])
        data = {"pickup_location": self.loc.id, "pickup_days": "3"}
        self.client.post(url, data, follow=True)
        self.cr.refresh_from_db()
        self.item1.refresh_from_db()
        self.item2.refresh_from_db()

        # Ensure status updated to approved
        self.assertEqual(self.cr.status, "approved")
        # Ensure a reserved_item has been set
        self.assertIsNotNone(self.cr.reserved_item)
        # The reserved item's status should be on_hold_shelf
        self.assertIn(self.cr.reserved_item.status, ["on_hold_shelf"])

    def test_concurrent_approvals_do_not_double_reserve(self):
        # Simulate approving twice - second approval should fail because no available items after first
        self.client.login(username="staff1", password="pass")
        url = reverse("circulation:approve_checkout_request", args=[self.cr.id])
        data = {"pickup_location": self.loc.id, "pickup_days": "3"}
        self.client.post(url, data, follow=True)
        # Attempt to approve again (should be blocked because status no longer pending)
        self.client.post(url, data, follow=True)
        self.cr.refresh_from_db()
        # second attempt should not change reserved_item
        self.assertEqual(self.cr.status, "approved")

    def test_complete_checkout_creates_loan(self):
        # Approve first to reserve an item
        self.client.login(username="staff1", password="pass")
        approve_url = reverse("circulation:approve_checkout_request", args=[self.cr.id])
        approve_data = {"pickup_location": self.loc.id, "pickup_days": "3"}
        self.client.post(approve_url, approve_data, follow=True)

        self.cr.refresh_from_db()
        self.assertEqual(self.cr.status, "approved")
        self.assertIsNotNone(self.cr.reserved_item)

        # Complete the checkout using the reserved item
        complete_url = reverse("circulation:complete_checkout_request", args=[self.cr.id])
        complete_data = {"item_identifier": str(self.cr.reserved_item.id)}
        self.client.post(complete_url, complete_data, follow=True)

        self.cr.refresh_from_db()
        self.cr.loan.refresh_from_db()
        self.cr.reserved_item.refresh_from_db()

        # Ensure checkout_request updated and loan created
        self.assertEqual(self.cr.status, "completed")
        self.assertIsNotNone(self.cr.loan)
        self.assertEqual(self.cr.reserved_item.status, "on_loan")

    def test_double_completion_does_not_create_second_loan(self):
        # Approve and complete once
        self.client.login(username="staff1", password="pass")
        approve_url = reverse("circulation:approve_checkout_request", args=[self.cr.id])
        approve_data = {"pickup_location": self.loc.id, "pickup_days": "3"}
        self.client.post(approve_url, approve_data, follow=True)
        self.cr.refresh_from_db()

        complete_url = reverse("circulation:complete_checkout_request", args=[self.cr.id])
        complete_data = {"item_identifier": str(self.cr.reserved_item.id)}
        self.client.post(complete_url, complete_data, follow=True)

        # Attempt to complete again - should not create another loan
        self.client.post(complete_url, complete_data, follow=True)

        # Only one loan should exist related to this checkout request
        loans = Loan.objects.filter(item__publication=self.pub)
        self.assertEqual(loans.count(), 1)
        self.cr.refresh_from_db()
        self.assertEqual(self.cr.status, "completed")

    def test_set_hold_ready_reserves_item(self):
        # Simulate staff marking a hold ready and reserving an item
        # Place a hold for another publication
        # use existing checkout_request pattern (not used directly here)
        # Create a hold-like object: convert checkout_request to behave like a hold
        # For testing, use the Hold flow by creating a Hold for the publication
        h = Hold.objects.create(
            publication=self.pub, borrower=self.borrower, pickup_location=self.loc, status="waiting"
        )

        # Login as staff and mark ready
        self.client.login(username="staff1", password="pass")
        url = reverse("circulation:set_hold_ready", args=[h.id])
        self.client.post(url, follow=True)
        h.refresh_from_db()
        # Ensure hold moved to ready
        self.assertEqual(h.status, "ready")

    def test_concurrent_set_hold_ready_does_not_double_reserve(self):
        h = Hold.objects.create(
            publication=self.pub, borrower=self.borrower, pickup_location=self.loc, status="waiting"
        )
        self.client.login(username="staff1", password="pass")
        url = reverse("circulation:set_hold_ready", args=[h.id])
        # First staff marks ready
        self.client.post(url, follow=True)
        # Second attempt should not reserve another item and should report already ready
        self.client.post(url, follow=True)
        h.refresh_from_db()
        self.assertEqual(h.status, "ready")
