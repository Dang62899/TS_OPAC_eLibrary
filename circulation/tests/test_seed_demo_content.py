import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings

from accounts.models import User
from catalog.models import Attachment, Item, Location, Publication, PublicationType
from circulation.management.commands.seed_demo_content import RESOURCES, VIDEOS
from circulation.models import ActivityLog, CheckoutRequest, Loan

TEST_MEDIA_ROOT = tempfile.mkdtemp(prefix="elib-test-media-")


@override_settings(DEBUG=True, MEDIA_ROOT=TEST_MEDIA_ROOT)
class SeedDemoContentTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)
    def setUp(self):
        User.objects.create_user(username="admin", password="x", user_type="admin", is_staff=True)
        User.objects.create_user(username="staff_test", password="x", user_type="staff", is_staff=True)
        for name in ("alpha", "bravo", "charlie", "delta", "echo"):
            User.objects.create_user(username=f"borrower_{name}", password="x", user_type="borrower")
        ptype = PublicationType.objects.create(name="Manual")
        location = Location.objects.create(name="Main", code="MAIN")
        titles = {row[0] for row in RESOURCES} | {row[0] for row in VIDEOS} | {f"Filler {n}" for n in range(14)}
        for number, title in enumerate(sorted(titles)):
            publication = Publication.objects.create(title=title, publication_type=ptype)
            for copy in range(2):
                Item.objects.create(
                    publication=publication, barcode=f"B{number:03d}{copy}", location=location, status="available",
                )
        video_pub = Publication.objects.get(title="Web Application Security Testing")
        Attachment.objects.create(
            publication=video_pub, attachment_type="video",
            file=SimpleUploadedFile("source.mp4", b"\x00\x00\x00\x18ftypmp42"),
        )

    def test_seeds_resources_and_transactions_once(self):
        call_command("seed_demo_content", verbosity=0)
        attachments = Attachment.objects.filter(tags__contains="demo-sample")
        self.assertEqual(attachments.count(), len(RESOURCES) + len(VIDEOS))
        videos = Attachment.objects.filter(tags__contains="demo-video")
        self.assertEqual(videos.count(), len(VIDEOS))
        sizes = {video.file.size for video in videos}
        self.assertGreater(min(sizes), 10_000)
        self.assertGreater(len(sizes), 1)
        self.assertTrue(attachments.filter(file__iendswith=".pdf").exists())
        self.assertTrue(attachments.filter(file__iendswith=".docx").exists())
        self.assertTrue(attachments.filter(file__iendswith=".pptx").exists())
        self.assertTrue(attachments.filter(is_external=True).exists())
        self.assertEqual(Loan.objects.filter(notes__startswith="[demo2]").count(), 7)
        self.assertEqual(CheckoutRequest.objects.filter(notes__startswith="[demo2]").count(), 5)
        self.assertTrue(ActivityLog.objects.filter(user__username="admin").exists())
        self.assertTrue(Loan.objects.filter(checkout_staff__username="staff_demo").exists())

        call_command("seed_demo_content", verbosity=0)
        self.assertEqual(Attachment.objects.filter(tags__contains="demo-sample").count(), len(RESOURCES) + len(VIDEOS))
        self.assertEqual(Loan.objects.filter(notes__startswith="[demo2]").count(), 7)
