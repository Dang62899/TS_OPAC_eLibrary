import io
from datetime import timedelta

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from catalog.models import Attachment, Item, Location, Publication
from circulation.models import ActivityLog, CheckoutRequest, Hold, Loan, Notification

from .demo_video import build_video_bytes

DEMO_PASSWORD = "BorrowerPass123!"
RESOURCE_TAG = "demo-sample"
VIDEO_TAG = "demo-video"
TXN_MARK = "[demo2]"

# (publication title, attachment type, kind, label, year, class, unit, downloadable, extra tags)
RESOURCES = [
    ("Incident Reporting Procedures", "sop", "pdf", "Signed SOP - Incident Reporting", 2026, "", "HAS", True, "sop,signed"),
    ("Security Audit Procedures", "sop", "pdf", "Signed SOP - Security Audit", 2026, "", "951", True, "sop,signed"),
    ("Cybersecurity Incident Response Manual", "curriculum", "pdf", "Curriculum - Incident Response Course", 2026, "Class A", "HAS", True, "curriculum"),
    ("Network Maintenance SOP", "unit_briefing", "pdf", "Unit Briefing - Network Maintenance Status", 2026, "", "952", False, "briefing"),
    ("AI-Powered Chatbot for Customer Service", "other", "pdf", "Research Paper - AI Chatbot", 2024, "Class A", "HAS", True, "research"),
    ("Blockchain-Based Supply Chain Tracking", "other", "pdf", "Research Paper - Blockchain Supply Chain", 2025, "Class B", "951", True, "research"),
    ("Cybersecurity Threat Detection System", "other", "pdf", "Research Paper - Threat Detection", 2025, "Class A", "952", False, "research"),
    ("Mobile Application for Library Management", "other", "pdf", "Research Paper - Library Mobile App", 2026, "Class C", "953", True, "research"),
    ("Software Deployment Procedures", "sop", "docx", "SOP - Software Deployment", 2026, "", "HAS", True, "sop"),
    ("Data Center Operations SOP", "sop", "docx", "SOP - Data Center Operations", 2025, "", "951", True, "sop"),
    ("Email Security Procedures", "other", "docx", "Checklist - Email Security", 2026, "", "952", True, "checklist"),
    ("Linux System Administration Guide", "curriculum", "docx", "Lesson Plan - Linux Administration", 2026, "Class B", "HAS", True, "curriculum,lesson-plan"),
    ("Digital Forensics Investigation Techniques", "presentation", "pptx", "Presentation - Digital Forensics Basics", 2026, "Class A", "HAS", True, "presentation"),
    ("Phishing Attack Analysis and Prevention", "presentation", "pptx", "Presentation - Phishing Awareness", 2026, "Class B", "951", True, "presentation"),
    ("Ransomware Response and Recovery", "unit_briefing", "pptx", "Unit Briefing - Ransomware Readiness", 2026, "", "953", False, "briefing"),
    ("Cloud Infrastructure Management", "presentation", "pptx", "Presentation - Cloud Operations Overview", 2025, "Class C", "952", True, "presentation"),
    ("Network Intrusion Detection Tactics", "video", "link", "Instructional Video (link) - Intrusion Detection", 2026, "Class B", "HAS", True, "video,link"),
    ("Cloud Security Assessment Methods", "video", "link", "Instructional Video (link) - Cloud Security", 2026, "Class C", "951", True, "video,link"),
]

# Generated instructional videos: (publication, title, subtitle, class, unit, downloadable, bullet points)
VIDEOS = [
    ("Web Application Security Testing", "Web Application Security Testing", "Module 1 | Instructional Video", "Class A", "HAS", True,
     ["Scope the application and map its entry points", "Test authentication and session handling", "Report findings with evidence and fixes"]),
    ("Social Engineering Defense Strategies", "Social Engineering Defense", "Awareness Training", "Class B", "951", True,
     ["Recognize pretexting, phishing and tailgating", "Verify identities before sharing information", "Report suspicious contact immediately"]),
    ("Malware Reverse Engineering Procedures", "Malware Analysis Walkthrough", "Module 3 | Instructional Video", "Class C", "952", False,
     ["Prepare an isolated analysis environment", "Perform static and dynamic analysis", "Document indicators of compromise"]),
    ("Wireless Network Security Procedures", "Securing Wireless Networks", "Network Operations Briefing", "Class A", "953", True,
     ["Use WPA3 and strong pre-shared keys", "Segment guest and administrative traffic", "Monitor for rogue access points"]),
    ("Ransomware Response and Recovery", "Ransomware Response Drill", "Unit Briefing Video", "Class B", "HAS", True,
     ["Isolate affected systems at once", "Preserve evidence and notify the chain of command", "Restore from verified offline backups"]),
    ("Incident Reporting Procedures", "How to File an Incident Report", "SOP Walkthrough", "Class A", "951", True,
     ["Collect who, what, when and where", "Complete the incident report form", "Submit to the duty officer within one hour"]),
    ("Linux System Administration Guide", "Linux Administration Basics", "Module 2 | Instructional Video", "Class B", "952", True,
     ["Manage users, groups and permissions", "Schedule jobs and monitor services", "Back up and restore configuration files"]),
    ("Cloud Infrastructure Management", "Cloud Operations Overview", "Module 4 | Instructional Video", "Class C", "953", True,
     ["Provision and tag cloud resources", "Control access with least privilege", "Track cost and availability"]),
    ("Digital Forensics Investigation Techniques", "Digital Forensics Primer", "Module 5 | Instructional Video", "Class A", "HAS", False,
     ["Acquire evidence with write blockers", "Maintain the chain of custody", "Analyze artifacts and write the report"]),
    ("Email Security Procedures", "Email Security Best Practices", "Awareness Training", "Class C", "951", True,
     ["Spot spoofed senders and unsafe links", "Encrypt sensitive attachments", "Report phishing through the proper channel"]),
]

# Capstone publications that also get year/class tags so research papers can be filtered by class.
RESEARCH_TAGS = {
    "AI-Powered Chatbot for Customer Service": (2024, "Class A"),
    "Blockchain-Based Supply Chain Tracking": (2025, "Class B"),
    "Cybersecurity Threat Detection System": (2025, "Class A"),
    "Mobile Application for Library Management": (2026, "Class C"),
    "IoT-Based Smart Home Automation System": (2024, "Class B"),
    "Predictive Analytics for Customer Behavior": (2025, "Class C"),
}


def _paragraphs(label):
    return [
        f"{label} - sample training content prepared for the TS eLibrary demonstration.",
        "Purpose: show how controlled resources are uploaded, watermarked, viewed and monitored.",
        "Scope: applies to students, alumni, instructors and library staff using the eLibrary.",
        "Responsibilities: staff upload and classify resources; borrowers access them under the user agreement.",
        "Handling: downloads are watermarked with the user name and date, and every access is logged.",
        "Note: this document contains fictitious sample data for demonstration only.",
    ]


def make_pdf(label):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    sections = ["Overview", "Procedures", "Responsibilities"]
    for number, section in enumerate(sections, 1):
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(72, 720, label)
        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawString(72, 690, f"{number}. {section}")
        pdf.setFont("Helvetica", 11)
        y = 660
        for line in _paragraphs(label):
            pdf.drawString(72, y, line[:95])
            y -= 22
        pdf.setFont("Helvetica-Oblique", 9)
        pdf.drawString(72, 50, f"TS eLibrary sample resource - page {number} of {len(sections)}")
        pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def make_docx(label):
    from docx import Document

    document = Document()
    document.add_heading(label, level=0)
    for heading in ("Purpose", "Procedure", "Responsibilities"):
        document.add_heading(heading, level=1)
        for line in _paragraphs(label)[:3]:
            document.add_paragraph(line)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def make_pptx(label):
    from pptx import Presentation

    deck = Presentation()
    title = deck.slides.add_slide(deck.slide_layouts[0])
    title.shapes.title.text = label
    title.placeholders[1].text = "TS eLibrary sample resource (demo data)"
    for heading in ("Objectives", "Key Points", "Summary"):
        slide = deck.slides.add_slide(deck.slide_layouts[1])
        slide.shapes.title.text = heading
        frame = slide.placeholders[1].text_frame
        frame.text = _paragraphs(label)[1]
        for line in _paragraphs(label)[2:5]:
            frame.add_paragraph().text = line
    buffer = io.BytesIO()
    deck.save(buffer)
    return buffer.getvalue()


class Command(BaseCommand):
    help = "Add sample PDFs, DOCX, PPTX and videos plus a staff/borrower transaction history for demos."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Allow running when DEBUG is off.")

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError("Refusing to create demo accounts with a known password while DEBUG is off.")

        with transaction.atomic():
            admin = User.objects.filter(username="admin").first() or User.objects.filter(user_type="admin").first()
            if admin is None:
                raise CommandError("No admin account found.")
            self._tag_research(admin)
            self._create_resources(admin)
            self._create_videos(admin)
            self._create_transactions(admin)

    def _create_videos(self, admin):
        # Replace the earlier byte-identical copies of one clip with distinct generated videos.
        stale = Attachment.objects.filter(tags__contains=RESOURCE_TAG, file__startswith="attachments/sample_video_")
        if stale.exists():
            for attachment in stale:
                attachment.file.delete(save=False)
            stale.delete()

        if Attachment.objects.filter(tags__contains=VIDEO_TAG).exists():
            self.stdout.write("demo videos already seeded; skipping")
            return

        created = 0
        for index, (pub_title, title, subtitle, class_name, unit, downloadable, bullets) in enumerate(VIDEOS, 1):
            publication = Publication.objects.filter(title=pub_title).first()
            if publication is None:
                self.stdout.write(f"missing publication: {pub_title}")
                continue
            data = build_video_bytes(title, subtitle, bullets, seconds=24)
            if data is None:
                raise CommandError("Video encoder unavailable. Run: pip install imageio-ffmpeg")
            attachment = Attachment(
                publication=publication, attachment_type="video", allow_download=downloadable, uploader=admin,
                year=2026, class_field=class_name, unit=unit, tags=f"{RESOURCE_TAG},{VIDEO_TAG},video",
                description=f"Instructional Video - {title}", duration_seconds=24,
            )
            attachment.file.save(f"demo_video_{index:02d}.mp4", ContentFile(data), save=False)
            attachment.save()
            created += 1
        self.stdout.write(f"created {created} instructional videos (24 sec each)")

    def _tag_research(self, admin):
        for title, (year, class_name) in RESEARCH_TAGS.items():
            Publication.objects.filter(title=title).update(research_year=year, research_class=class_name)
        self.stdout.write(f"tagged {len(RESEARCH_TAGS)} research papers by year/class")

    def _create_resources(self, admin):
        if Attachment.objects.filter(tags__contains=RESOURCE_TAG).exists():
            self.stdout.write("sample resources already seeded; skipping")
            return

        makers = {"pdf": make_pdf, "docx": make_docx, "pptx": make_pptx}
        created = {"pdf": 0, "docx": 0, "pptx": 0, "link": 0}
        for index, (title, kind_type, kind, label, year, class_name, unit, downloadable, tags) in enumerate(RESOURCES, 1):
            publication = Publication.objects.filter(title=title).first()
            if publication is None:
                self.stdout.write(f"missing publication: {title}")
                continue
            attachment = Attachment(
                publication=publication,
                attachment_type=kind_type,
                allow_download=downloadable,
                uploader=admin,
                year=year,
                class_field=class_name,
                unit=unit,
                tags=f"{RESOURCE_TAG},{tags}",
                description=label,
                merge_first_two_pages=(kind == "pdf" and index % 2 == 1),
            )
            if kind == "link":
                attachment.is_external = True
                attachment.external_url = f"https://example.com/training-videos/{index}"
                attachment.duration_seconds = 300 + index * 20
            else:
                attachment.file.save(f"sample_{index}.{kind}", ContentFile(makers[kind](label)), save=False)
            attachment.save()
            created[kind] += 1
        self.stdout.write(
            "created {pdf} PDFs, {docx} DOCX, {pptx} PPTX, {link} video links".format(**created)
        )

    def _create_transactions(self, admin):
        if Loan.objects.filter(notes__startswith=TXN_MARK).exists():
            self.stdout.write("staff/borrower transactions already seeded; skipping")
            return

        now = timezone.now()
        today = now.date()
        staff_a = User.objects.filter(username="staff_test").first()
        staff_b, created = User.objects.get_or_create(
            username="staff_demo",
            defaults=dict(
                email="staff_demo@example.com", first_name="Maria", last_name="Lopez",
                user_type="staff", is_staff=True, agreed_to_terms=True, agreed_at=now,
            ),
        )
        if created:
            staff_b.set_password(DEMO_PASSWORD)
            staff_b.save()
        staff_a = staff_a or staff_b
        borrowers = {
            name: User.objects.filter(username=name).first()
            for name in ("borrower_alpha", "borrower_bravo", "borrower_charlie", "borrower_delta", "borrower_echo")
        }
        if not all(borrowers.values()):
            raise CommandError("Run `manage.py seed_demo_data` first to create the sample borrowers.")
        alpha, bravo, charlie, delta, echo = borrowers.values()

        items = list(
            Item.objects.filter(status="available")
            .select_related("publication", "location")
            .order_by("publication_id", "id")
        )
        seen, picks = set(), []
        for item in items:
            if item.publication_id not in seen and item.publication.items.count() >= 2:
                seen.add(item.publication_id)
                picks.append(item)
        if len(picks) < 12:
            raise CommandError(f"Need 12 multi-copy publications with an available copy, found {len(picks)}.")
        main = Location.objects.filter(code="MAIN").first() or picks[0].location

        log_entries = []

        def log(action, user, description, days_ago=0.0, obj=None):
            entry = ActivityLog.objects.create(
                action=action, user=user, description=description,
                content_type="catalog.Publication" if obj is not None else "",
                object_id=obj.pk if obj is not None else None,
                object_repr=str(obj)[:200] if obj is not None else "",
                ip_address="10.77.1.10",
            )
            log_entries.append((entry.pk, now - timedelta(days=days_ago)))

        def loan(item, borrower, staff, days_ago, due_in, status, note, **extra):
            record = Loan.objects.create(
                item=item, borrower=borrower, checkout_date=now - timedelta(days=days_ago),
                due_date=today + timedelta(days=due_in), status=status, notes=f"{TXN_MARK} {note}",
                checkout_staff=staff, **extra,
            )
            log("checkout", staff, f"Checked out '{item.publication.title}' to {borrower.username}", days_ago, item.publication)
            return record

        # Admin sets up staff and borrower accounts
        if created:
            log("user_created", admin, "Created staff account staff_demo (Maria Lopez)", 21)
        for name, user in borrowers.items():
            log("user_created", admin, f"Created student account {name} ({user.get_full_name()})", 20)
        log("permission_change", admin, "Granted staff circulation permissions to staff_demo", 20)
        log("login", admin, "Administrator signed in", 14)
        log("report_generated", admin, "Generated monthly circulation and access report", 7)
        log("backup", admin, "Created full database backup", 3)

        # Staff process circulation for borrowers
        a1 = loan(picks[0], alpha, staff_b, 3, 11, "active", "active loan processed by staff_demo")
        loan(picks[1], bravo, admin, 6, 8, "active", "checked out directly by admin")
        r1 = loan(picks[2], charlie, staff_a, 35, -20, "returned", "returned on time",
                  return_date=now - timedelta(days=22), return_staff=staff_a)
        log("checkin", staff_a, f"Returned '{picks[2].publication.title}' from {charlie.username}", 22, picks[2].publication)
        r2 = loan(picks[3], alpha, staff_b, 28, -14, "returned", "returned on time",
                  return_date=now - timedelta(days=16), return_staff=staff_b)
        log("checkin", staff_b, f"Returned '{picks[3].publication.title}' from {alpha.username}", 16, picks[3].publication)
        renewed = loan(picks[4], bravo, staff_a, 18, 5, "active", "renewed twice", renewal_count=2)
        log("renewal", staff_a, f"Renewed '{picks[4].publication.title}' for {bravo.username}", 4, picks[4].publication)
        overdue = loan(picks[5], charlie, staff_b, 24, -4, "active", "overdue loan")
        late = loan(picks[6], echo, staff_a, 40, -25, "overdue_returned", "returned late",
                    return_date=now - timedelta(days=15), return_staff=staff_a)
        log("checkin", staff_a, f"Returned '{picks[6].publication.title}' from {echo.username} (late)", 15, picks[6].publication)

        # Holds
        Hold.objects.create(
            publication=picks[0].publication, borrower=charlie, pickup_location=main,
            status="waiting", notes=f"{TXN_MARK} waiting for the next copy",
        ).update_queue_position()
        log("hold_placed", charlie, f"Placed hold on '{picks[0].publication.title}'", 2, picks[0].publication)
        ready = picks[7]
        ready.status = "on_hold_shelf"
        ready.save()
        Hold.objects.create(
            publication=ready.publication, borrower=bravo, reserved_item=ready, pickup_location=ready.location,
            status="ready", ready_date=now - timedelta(days=1), expiry_date=now + timedelta(days=4),
            notes=f"{TXN_MARK} ready for pickup",
        )
        log("hold_ready", staff_b, f"Hold ready for {bravo.username}: '{ready.publication.title}'", 1, ready.publication)

        # Checkout requests, reviewed by staff or admin
        CheckoutRequest.objects.create(
            publication=picks[8].publication, borrower=alpha, status="pending", notes=f"{TXN_MARK} pending request",
        )
        CheckoutRequest.objects.create(
            publication=picks[9].publication, borrower=bravo, status="pending", notes=f"{TXN_MARK} pending request",
        )
        approved = picks[10]
        approved.status = "on_hold_shelf"
        approved.save()
        CheckoutRequest.objects.create(
            publication=approved.publication, borrower=charlie, status="approved", reserved_item=approved,
            reviewed_by=staff_b, review_date=now - timedelta(hours=20), pickup_location=approved.location,
            pickup_by_date=now + timedelta(days=3), notes=f"{TXN_MARK} approved request",
        )
        CheckoutRequest.objects.create(
            publication=r2.item.publication, borrower=alpha, status="completed", loan=r2,
            reviewed_by=staff_b, review_date=now - timedelta(days=29), notes=f"{TXN_MARK} completed request",
        )
        CheckoutRequest.objects.create(
            publication=picks[11].publication, borrower=echo, status="denied", reviewed_by=admin,
            review_date=now - timedelta(days=3), notes=f"{TXN_MARK} denied request",
            staff_notes="Account is blocked pending return of an unreturned item.",
        )
        log("other", staff_b, f"Approved checkout request from {charlie.username}: '{approved.publication.title}'", 1, approved.publication)
        log("other", admin, f"Denied checkout request from {echo.username}: blocked account", 3, picks[11].publication)

        # Borrower sign-ins and notifications
        for user, days in ((alpha, 3), (bravo, 2), (charlie, 2), (alpha, 1)):
            log("login", user, f"{user.username} signed in", days)
        log("login", staff_a, "Staff signed in", 5)
        log("login", staff_b, "Staff signed in", 3)

        Notification.objects.create(
            borrower=alpha, notification_type="due_soon", loan=a1, title="Demo: due soon",
            message=f"\"{a1.item.publication.title}\" is due on {a1.due_date:%B %d, %Y}.",
        )
        Notification.objects.create(
            borrower=charlie, notification_type="overdue", loan=overdue, title="Demo: overdue notice",
            message=f"\"{overdue.item.publication.title}\" was due on {overdue.due_date:%B %d, %Y}.",
        )
        Notification.objects.create(
            borrower=bravo, notification_type="hold_ready", title="Demo: hold ready",
            message=f"\"{ready.publication.title}\" is ready for pickup.",
        )

        for pk, stamp in log_entries:
            ActivityLog.objects.filter(pk=pk).update(timestamp=stamp)
        self.stdout.write(
            f"created 7 loans, 2 holds, 5 checkout requests, 3 notifications and {len(log_entries)} activity log entries"
        )
        self.stdout.write(f"staff_demo password (DEBUG only): {DEMO_PASSWORD}")
