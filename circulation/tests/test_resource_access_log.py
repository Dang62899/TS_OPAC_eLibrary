import io

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from reportlab.pdfgen import canvas

from accounts.models import User
from catalog.models import Attachment, Publication, PublicationType, ViewLog


def pdf_bytes():
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(100, 750, "Monitor test")
    pdf.save()
    return buffer.getvalue()


class ResourceAccessMonitorTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.borrower = User.objects.create_user(
            username="monitored-borrower", password="pass1234", user_type="borrower", agreed_to_terms=True
        )
        self.staff = User.objects.create_user(
            username="monitor-staff", password="pass1234", user_type="staff", agreed_to_terms=True
        )
        self.admin = User.objects.create_user(
            username="monitor-admin", password="pass1234", user_type="admin", agreed_to_terms=True
        )
        publication_type = PublicationType.objects.create(name="Manual", code="MAN")
        self.publication = Publication.objects.create(title="Monitored Manual", publication_type=publication_type)

    def _pdf_attachment(self):
        attachment = Attachment.objects.create(
            publication=self.publication,
            file=SimpleUploadedFile("monitored.pdf", pdf_bytes(), content_type="application/pdf"),
            allow_download=True,
        )
        return attachment

    def test_download_and_preview_are_recorded_with_action_and_file_type(self):
        attachment = self._pdf_attachment()
        self.client.force_login(self.borrower)
        self.client.post(
            reverse("catalog:unlock_attachment", args=[attachment.pk]),
            {"password": "eLib@2026"},
        )

        self.client.get(reverse("catalog:preview_merged_attachment", args=[attachment.pk]))
        self.client.get(reverse("catalog:download_attachment", args=[attachment.pk]))

        preview = ViewLog.objects.get(attachment=attachment, action="preview")
        download = ViewLog.objects.get(attachment=attachment, action="download")
        self.assertEqual(download.username_snapshot, "monitored-borrower")
        self.assertEqual(download.file_format, "pdf")
        self.assertEqual(download.publication, self.publication)
        self.assertIn("Monitored Manual", download.resource_label)
        self.assertEqual(preview.username_snapshot, "monitored-borrower")

    def test_denied_download_is_not_recorded(self):
        attachment = self._pdf_attachment()
        self.client.force_login(self.borrower)

        response = self.client.get(reverse("catalog:download_attachment", args=[attachment.pk]))

        self.assertEqual(response.status_code, 403)
        self.assertFalse(ViewLog.objects.filter(attachment=attachment).exists())

    def test_video_play_is_logged_once_per_playback_not_per_range_request(self):
        video = Attachment.objects.create(
            publication=self.publication,
            file=SimpleUploadedFile("lesson.mp4", b"0123456789", content_type="video/mp4"),
            attachment_type="video",
            allow_download=True,
        )
        self.client.force_login(self.borrower)
        stream_url = reverse("catalog:stream_attachment", args=[video.pk])

        self.client.get(stream_url, HTTP_RANGE="bytes=0-3")
        self.client.get(stream_url, HTTP_RANGE="bytes=4-7")
        self.client.get(stream_url, HTTP_RANGE="bytes=8-9")

        plays = ViewLog.objects.filter(attachment=video, action="play")
        self.assertEqual(plays.count(), 1)
        self.assertEqual(plays.get().file_format, "mp4")

    def test_monitor_is_limited_to_staff_and_admin(self):
        url = reverse("circulation:resource_access_log")

        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.borrower)
        self.assertEqual(self.client.get(url).status_code, 302)
        for user in (self.staff, self.admin):
            self.client.force_login(user)
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_monitor_lists_activity_and_filters_by_user_action_and_type(self):
        attachment = self._pdf_attachment()
        ViewLog.objects.create(user=self.borrower, attachment=attachment, action="download")
        ViewLog.objects.create(user=self.staff, attachment=attachment, action="preview")
        self.client.force_login(self.admin)
        url = reverse("circulation:resource_access_log")

        everything = self.client.get(url)
        self.assertContains(everything, "monitored-borrower")
        self.assertContains(everything, "monitor-staff")

        downloads = self.client.get(url, {"action": "download"})
        self.assertContains(downloads, "monitored-borrower")
        self.assertNotContains(downloads, "monitor-staff")

        by_user = self.client.get(url, {"q": "monitor-staff"})
        self.assertContains(by_user, "monitor-staff")
        self.assertNotContains(by_user, "monitored-borrower")

        wrong_type = self.client.get(url, {"format": "mp4"})
        self.assertNotContains(wrong_type, "monitored-borrower")
        self.assertContains(wrong_type, "No matching activity")

    def test_log_entries_survive_deleting_the_user_and_the_file(self):
        attachment = self._pdf_attachment()
        log = ViewLog.objects.create(user=self.borrower, attachment=attachment, action="download")

        self.borrower.delete()
        attachment.delete()
        log.refresh_from_db()

        self.assertEqual(log.username_snapshot, "monitored-borrower")
        self.assertIn("Monitored Manual", log.resource_label)
        self.assertEqual(log.file_format, "pdf")

    def test_csv_export_neutralizes_spreadsheet_formulas(self):
        ViewLog.objects.create(
            publication=self.publication,
            action="download",
            username_snapshot="=cmd|' /C calc'!A0",
            resource_label="=HYPERLINK(\"http://example.com\")",
        )
        self.client.force_login(self.staff)

        response = self.client.get(reverse("circulation:resource_access_log"), {"export": "csv"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        body = response.content.decode()
        self.assertIn("'=cmd", body)
        self.assertIn("'=HYPERLINK", body)
        self.assertNotIn(",=cmd", body)
