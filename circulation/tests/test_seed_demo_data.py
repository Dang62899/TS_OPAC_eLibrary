from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from accounts.models import User
from catalog.models import Item, Location, Publication, PublicationType
from circulation.models import CheckoutRequest, Hold, InTransit, Loan


class SeedDemoDataTests(TestCase):
    def setUp(self):
        main = Location.objects.create(name="Main", code="MAIN")
        self.other = Location.objects.create(name="Reference", code="REF")
        publication_type = PublicationType.objects.create(name="Manual", code="MAN")
        for index in range(10):
            publication = Publication.objects.create(title=f"Seed Title {index}", publication_type=publication_type)
            Item.objects.create(publication=publication, location=main, barcode=f"SEED-{index}", status="available")

    def _seed(self):
        call_command("seed_demo_data", force=True, stdout=StringIO())

    def test_refuses_to_create_known_password_accounts_when_debug_is_off(self):
        with self.assertRaises(CommandError):
            call_command("seed_demo_data", stdout=StringIO())

        self.assertFalse(User.objects.filter(username__startswith="borrower_").exists())

    def test_creates_borrowers_with_the_expected_blocking_states(self):
        self._seed()

        alpha = User.objects.get(username="borrower_alpha")
        self.assertTrue(alpha.check_password("BorrowerPass123!"))
        self.assertTrue(alpha.can_borrow())
        delta = User.objects.get(username="borrower_delta")
        self.assertTrue(delta.is_blocked)
        self.assertFalse(delta.can_borrow())
        echo = User.objects.get(username="borrower_echo")
        self.assertTrue(echo.is_blocked)
        self.assertFalse(echo.can_borrow())

    def test_transactions_cover_each_state_and_keep_items_consistent(self):
        self._seed()

        self.assertEqual(
            set(Loan.objects.values_list("status", flat=True)),
            {"active", "returned", "overdue_returned"},
        )
        self.assertEqual(set(Hold.objects.values_list("status", flat=True)), {"waiting", "ready"})
        self.assertEqual(
            set(CheckoutRequest.objects.values_list("status", flat=True)),
            {"pending", "approved", "completed", "denied"},
        )
        self.assertEqual(InTransit.objects.count(), 1)
        for loan in Loan.objects.filter(status="active"):
            self.assertEqual(loan.item.status, "on_loan")
        approved = CheckoutRequest.objects.get(status="approved")
        self.assertEqual(approved.reserved_item.status, "on_hold_shelf")
        self.assertTrue(any(loan.is_overdue() for loan in Loan.objects.filter(status="active")))

    def test_running_twice_does_not_duplicate_anything(self):
        self._seed()
        first = (User.objects.count(), Loan.objects.count(), Hold.objects.count(), CheckoutRequest.objects.count())

        self._seed()

        second = (User.objects.count(), Loan.objects.count(), Hold.objects.count(), CheckoutRequest.objects.count())
        self.assertEqual(first, second)
