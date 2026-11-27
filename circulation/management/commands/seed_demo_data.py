from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from accounts.models import User
from catalog.models import Attachment, Item, Location, Publication, ViewLog
from circulation.models import CheckoutRequest, Hold, InTransit, Loan, Notification

DEMO_PASSWORD = "BorrowerPass123!"
LOG_IP_PREFIX = "10.77.0."

BORROWERS = [
    # username, first name, last name, block reason
    ("borrower_alpha", "Alex", "Reyes", ""),
    ("borrower_bravo", "Bianca", "Santos", ""),
    ("borrower_charlie", "Carlo", "Mendoza", ""),
    ("borrower_delta", "Dana", "Cruz", "Account requires staff review"),
    ("borrower_echo", "Eli", "Garcia", "Unreturned item reported by staff"),
]

# username, file extension of the demo resource, action, minutes ago
ACCESS_EVENTS = [
    ("borrower_alpha", ".pdf", "preview", 30),
    ("borrower_alpha", ".pdf", "download", 28),
    ("borrower_alpha", ".mp4", "play", 95),
    ("borrower_bravo", ".pdf", "preview", 190),
    ("borrower_bravo", ".pptx", "download", 185),
    ("borrower_bravo", ".mp4", "play", 400),
    ("borrower_bravo", ".mp4", "download", 392),
    ("borrower_charlie", ".docx", "download", 700),
    ("borrower_charlie", ".pptx", "download", 1500),
    ("borrower_charlie", ".mp4", "play", 1520),
    ("borrower_delta", ".pdf", "preview", 2900),
    ("borrower_alpha", ".docx", "download", 4300),
]


class Command(BaseCommand):
    help = "Create sample borrower accounts, circulation transactions, and resource access history."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Allow running when DEBUG is off. Never use this on a production system.",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError("Refusing to create demo accounts with a known password while DEBUG is off.")

        with transaction.atomic():
            borrowers = self._create_borrowers()
            self._create_transactions(borrowers)
            self._create_access_history(borrowers)

        self.stdout.write("")
        self.stdout.write(f"Sample borrower password: {DEMO_PASSWORD}")

    def _create_borrowers(self):
        borrowers = {}
        for username, first, last, block_reason in BORROWERS:
            user = User.objects.filter(username=username).first()
            if user is None:
                user = User.objects.create_user(
                    username=username,
                    email=f"{username}@example.com",
                    password=DEMO_PASSWORD,
                    first_name=first,
                    last_name=last,
                    user_type="borrower",
                    is_blocked=bool(block_reason),
                    block_reason=block_reason,
                    agreed_to_terms=True,
                    agreed_at=timezone.now(),
                )
                self.stdout.write(f"created {username}{', blocked' if block_reason else ''}")
            else:
                self.stdout.write(f"exists  {username}")
            borrowers[username] = user
        return borrowers

    def _create_transactions(self, borrowers):
        if Loan.objects.filter(notes__startswith="[demo]").exists():
            self.stdout.write("transactions already seeded; skipping")
            return

        now = timezone.now()
        today = now.date()
        staff = (
            User.objects.filter(username="staff_test").first()
            or User.objects.filter(user_type__in=["staff", "admin_staff", "admin"]).first()
        )
        single_copy = Publication.objects.annotate(copies=Count("items")).filter(copies=1)
        items = list(
            Item.objects.filter(status="available", publication__in=single_copy)
            .select_related("publication", "location")
            .order_by("publication_id")
        )
        if len(items) < 10:
            raise CommandError(f"Need 10 single-copy available publications, found {len(items)}.")
        alpha, bravo, charlie, delta = (borrowers[name] for name in ("borrower_alpha", "borrower_bravo", "borrower_charlie", "borrower_delta"))
        main = Location.objects.filter(code="MAIN").first() or items[0].location

        def loan(item, borrower, checkout_days_ago, due_days_from_today, status, note, **extra):
            return Loan.objects.create(
                item=item,
                borrower=borrower,
                checkout_date=now - timedelta(days=checkout_days_ago),
                due_date=today + timedelta(days=due_days_from_today),
                status=status,
                notes=f"[demo] {note}",
                checkout_staff=staff,
                **extra,
            )

        active = loan(items[0], alpha, 4, 10, "active", "active loan")
        loan(items[1], bravo, 14, 7, "active", "renewed loan", renewal_count=1)
        overdue = loan(items[2], charlie, 25, -5, "active", "overdue loan")
        returned = loan(
            items[3], alpha, 40, -12, "returned", "returned on time",
            return_date=now - timedelta(days=30), return_staff=staff,
        )
        loan(
            items[4], bravo, 45, -10, "overdue_returned", "returned late",
            return_date=now - timedelta(days=6), return_staff=staff,
        )

        Hold.objects.create(
            publication=items[0].publication, borrower=bravo, pickup_location=main,
            status="waiting", notes="[demo] waiting for the only copy",
        ).update_queue_position()

        ready_item = items[5]
        ready_item.status = "on_hold_shelf"
        ready_item.save()
        Hold.objects.create(
            publication=ready_item.publication, borrower=alpha, reserved_item=ready_item,
            pickup_location=ready_item.location, status="ready", notes="[demo] ready for pickup",
        )

        CheckoutRequest.objects.create(
            publication=items[6].publication, borrower=charlie, status="pending", notes="[demo] pending request",
        )
        approved_item = items[7]
        approved_item.status = "on_hold_shelf"
        approved_item.save()
        CheckoutRequest.objects.create(
            publication=approved_item.publication, borrower=bravo, status="approved",
            reserved_item=approved_item, reviewed_by=staff, review_date=now,
            pickup_location=approved_item.location, pickup_by_date=now + timedelta(days=3),
            notes="[demo] approved request",
        )
        CheckoutRequest.objects.create(
            publication=returned.item.publication, borrower=alpha, status="completed", loan=returned,
            reviewed_by=staff, review_date=now - timedelta(days=41), notes="[demo] completed request",
        )
        CheckoutRequest.objects.create(
            publication=items[8].publication, borrower=delta, status="denied", reviewed_by=staff,
            review_date=now - timedelta(days=2), notes="[demo] denied request",
            staff_notes="Blocked borrower accounts are not eligible for checkout.",
        )

        transit_item = items[9]
        destination = Location.objects.exclude(pk=transit_item.location_id).first()
        if destination is not None:
            InTransit.objects.create(
                item=transit_item, from_location=transit_item.location, to_location=destination,
                notes="[demo] moving between locations",
            )
            transit_item.status = "in_transit"
            transit_item.save()

        Notification.objects.create(
            borrower=alpha, notification_type="due_soon", loan=active, title="Demo: due soon",
            message=f"\"{active.item.publication.title}\" is due on {active.due_date:%B %d, %Y}.",
        )
        Notification.objects.create(
            borrower=charlie, notification_type="overdue", loan=overdue, title="Demo: overdue notice",
            message=f"\"{overdue.item.publication.title}\" was due on {overdue.due_date:%B %d, %Y}.",
        )
        Notification.objects.create(
            borrower=alpha, notification_type="hold_ready", title="Demo: hold ready",
            message=f"\"{ready_item.publication.title}\" is ready for pickup.",
        )
        self.stdout.write("created 5 loans, 2 holds, 4 checkout requests, 1 transfer, 3 notifications")

    def _create_access_history(self, borrowers):
        if ViewLog.objects.filter(ip_address__startswith=LOG_IP_PREFIX).exists():
            self.stdout.write("access history already seeded; skipping")
            return

        attachments = {}
        for attachment in Attachment.objects.filter(publication__title="Demo Media Resources"):
            if attachment.file:
                attachments.setdefault(attachment.file.name[attachment.file.name.rfind("."):].lower(), attachment)
        if not attachments:
            self.stdout.write("no 'Demo Media Resources' files found; skipped access history")
            return

        now = timezone.now()
        created = 0
        for number, (username, extension, action, minutes_ago) in enumerate(ACCESS_EVENTS, 1):
            attachment = attachments.get(extension)
            if attachment is None:
                continue
            log = ViewLog.objects.create(
                user=borrowers[username],
                attachment=attachment,
                publication_id=attachment.publication_id,
                action=action,
                ip_address=f"{LOG_IP_PREFIX}{number}",
            )
            ViewLog.objects.filter(pk=log.pk).update(timestamp=now - timedelta(minutes=minutes_ago))
            created += 1
        self.stdout.write(f"created {created} resource access records")
