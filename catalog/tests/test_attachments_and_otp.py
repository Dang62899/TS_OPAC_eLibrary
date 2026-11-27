from django.test import TestCase, Client
from django.test import override_settings
from django.core.cache import cache
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from unittest.mock import patch
from docx import Document
from pptx import Presentation
from accounts.models import User
from catalog.models import Publication, PublicationType, Attachment, DownloadOTP, ViewLog
from catalog.forms import AttachmentForm
from catalog.utils.pdf_utils import watermark_text_for_date
import io
import os
import subprocess
import tempfile
from reportlab.pdfgen import canvas
import imageio_ffmpeg
from PIL import Image


def create_test_pdf_bytes():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 750, "Test PDF")
    c.showPage()
    c.drawString(100, 750, "Second page")
    c.save()
    buffer.seek(0)
    return buffer.read()


def create_test_mp4_bytes():
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    with tempfile.TemporaryDirectory(prefix="elibrary-test-video-") as temp_dir:
        path = os.path.join(temp_dir, "source.mp4")
        subprocess.run(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "color=c=black:s=320x180:d=0.5:r=24",
                "-an",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                path,
            ],
            check=True,
            capture_output=True,
            timeout=60,
        )
        with open(path, "rb") as video_file:
            return video_file.read()


class AttachmentOTPTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user = User.objects.create_user(
            username="tester",
            password="pass1234",
            email="tester@example.com",
            agreed_to_terms=True,
        )
        self.pub_type = PublicationType.objects.create(name="Paper", code="paper")
        self.pub = Publication.objects.create(title="Research 1", publication_type=self.pub_type)

    @override_settings(DEBUG=True)
    def test_upload_attachment_and_request_otp(self):
        self.client.login(username="tester", password="pass1234")

        pdf_bytes = create_test_pdf_bytes()
        uploaded = SimpleUploadedFile("test.pdf", pdf_bytes, content_type="application/pdf")

        attach = Attachment.objects.create(publication=self.pub, file=uploaded, allow_download=False, attachment_type="presentation", uploader=self.user)

        # Request OTP (login required)
        url = reverse("catalog:request_download_otp", args=[attach.id])
        get_response = self.client.get(url)
        self.assertEqual(get_response.status_code, 405)
        self.assertFalse(DownloadOTP.objects.filter(attachment=attach).exists())

        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, reverse("catalog:publication_detail", args=[self.pub.pk]))

        # Ensure an OTP record was created
        otps = DownloadOTP.objects.filter(attachment=attach)
        self.assertTrue(otps.exists())

    @override_settings(DOWNLOAD_OTP_TIMEOUT_MINUTES=7, DEBUG=True)
    def test_download_otp_expiry_uses_configured_duration(self):
        self.user.email = ""
        self.user.save(update_fields=["email"])
        attachment = Attachment.objects.create(
            publication=self.pub,
            is_external=True,
            external_url="https://example.com/resource",
            allow_download=False,
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse("catalog:request_download_otp", args=[attachment.pk]))

        self.assertEqual(response.status_code, 200)
        otp = DownloadOTP.objects.get(attachment=attachment)
        self.assertAlmostEqual((otp.expires_at - otp.created_at).total_seconds(), 7 * 60, delta=1)

    @override_settings(DEBUG=False)
    def test_otp_code_is_not_displayed_when_production_email_is_unavailable(self):
        self.user.email = ""
        self.user.save(update_fields=["email"])
        attachment = Attachment.objects.create(
            publication=self.pub,
            is_external=True,
            external_url="https://example.com/resource",
            allow_download=False,
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse("catalog:request_download_otp", args=[attachment.pk]))

        self.assertEqual(response.status_code, 503)
        self.assertNotContains(response, DownloadOTP.objects.get(attachment=attachment).code, status_code=503)

    def test_attachment_form_requires_file_or_external_url(self):
        missing_file_form = AttachmentForm(data={"attachment_type": "presentation"})
        self.assertFalse(missing_file_form.is_valid())
        self.assertIn("file", missing_file_form.errors)

        missing_url_form = AttachmentForm(
            data={"attachment_type": "video", "is_external": "on"}
        )
        self.assertFalse(missing_url_form.is_valid())
        self.assertIn("external_url", missing_url_form.errors)

        link_form = AttachmentForm(
            data={
                "attachment_type": "video",
                "is_external": "on",
                "external_url": "https://example.com/video",
            }
        )
        self.assertTrue(link_form.is_valid(), link_form.errors)

    def test_downloadable_attachment_uses_shared_password(self):
        form = AttachmentForm(
            data={
                "attachment_type": "video",
                "is_external": "on",
                "external_url": "https://example.com/video",
                "allow_download": "on",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertNotIn("download_password", form.fields)
        attachment = form.save(commit=False)
        self.assertTrue(attachment.has_download_password)
        self.assertTrue(attachment.check_download_password("eLib@2026"))
        self.assertFalse(attachment.check_download_password("WrongPassword123!"))
        self.assertFalse(attachment.check_download_password(""))

    def test_video_attachment_stores_description_and_duration(self):
        form = AttachmentForm(
            data={
                "attachment_type": "video",
                "is_external": "on",
                "external_url": "https://example.com/video",
                "description": "Safety briefing",
                "duration_seconds": "95",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        attachment = form.save(commit=False)
        self.assertEqual(attachment.description, "Safety briefing")
        self.assertEqual(attachment.duration_seconds, 95)

    def test_attachment_form_rejects_unsupported_file_extensions(self):
        form = AttachmentForm(
            data={"attachment_type": "presentation"},
            files={"file": SimpleUploadedFile("payload.exe", b"not a document")},
        )

        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    @override_settings(MAX_ATTACHMENT_SIZE_MB=1)
    def test_attachment_form_rejects_oversized_files(self):
        form = AttachmentForm(
            data={"attachment_type": "presentation"},
            files={"file": SimpleUploadedFile("large.pdf", b"x" * (1024 * 1024 + 1))},
        )

        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    def test_preview_merged_attachment_pdf(self):
        pdf_bytes = create_test_pdf_bytes()
        uploaded = SimpleUploadedFile("test.pdf", pdf_bytes, content_type="application/pdf")
        attach = Attachment.objects.create(publication=self.pub, file=uploaded, allow_download=True, attachment_type="presentation", uploader=self.user)

        self.client.force_login(self.user)
        url = reverse("catalog:preview_merged_attachment", args=[attach.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/pdf")
        view_log = ViewLog.objects.get(attachment=attach)
        self.assertEqual(view_log.user, self.user)

    def test_preview_can_combine_first_two_pages_on_one_sheet(self):
        pdf_bytes = create_test_pdf_bytes()
        attachment = Attachment.objects.create(
            publication=self.pub,
            file=SimpleUploadedFile("two-pages.pdf", pdf_bytes, content_type="application/pdf"),
            attachment_type="presentation",
            merge_first_two_pages=True,
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("catalog:preview_merged_attachment", args=[attachment.pk]))

        self.assertEqual(response.status_code, 200)
        from pypdf import PdfReader

        preview = PdfReader(io.BytesIO(response.content))
        self.assertEqual(len(preview.pages), 1)

    def test_protected_pdf_preview_requires_valid_otp_grant(self):
        attachment = Attachment.objects.create(
            publication=self.pub,
            file=SimpleUploadedFile("restricted-preview.pdf", create_test_pdf_bytes(), content_type="application/pdf"),
            attachment_type="presentation",
            allow_download=False,
        )
        preview_url = reverse("catalog:preview_merged_attachment", args=[attachment.pk])

        anonymous_response = self.client.get(preview_url)
        self.assertEqual(anonymous_response.status_code, 302)
        self.assertTrue(anonymous_response.url.startswith(reverse("accounts:login")))
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(preview_url).status_code, 403)

        DownloadOTP.objects.create(
            attachment=attachment,
            user=self.user,
            code="456789",
            expires_at=timezone.now() + timezone.timedelta(minutes=15),
        )
        confirmation = self.client.post(
            reverse("catalog:confirm_attachment_otp", args=[attachment.pk]),
            {"code": "456789"},
        )
        self.assertEqual(confirmation.status_code, 200)
        self.assertEqual(self.client.get(preview_url).status_code, 200)

    def test_download_otp_requires_authenticated_owner_and_is_one_time(self):
        attachment = Attachment.objects.create(
            publication=self.pub,
            is_external=True,
            external_url="https://example.com/resource",
            allow_download=False,
            attachment_type="video",
        )
        otp = DownloadOTP.objects.create(
            attachment=attachment,
            user=self.user,
            code="123456",
            expires_at=timezone.now() + timezone.timedelta(minutes=15),
        )
        confirm_url = reverse("catalog:confirm_download", args=[otp.code])

        anonymous_response = self.client.post(confirm_url)
        self.assertEqual(anonymous_response.status_code, 302)

        other_user = User.objects.create_user(
            username="other", password="pass1234", agreed_to_terms=True
        )
        self.client.force_login(other_user)
        unauthorized_response = self.client.post(confirm_url)
        self.assertEqual(unauthorized_response.status_code, 400)
        otp.refresh_from_db()
        self.assertFalse(otp.used)

        self.client.force_login(self.user)
        response = self.client.post(confirm_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], attachment.external_url)
        otp.refresh_from_db()
        self.assertTrue(otp.used)

        replay_response = self.client.post(confirm_url)
        self.assertEqual(replay_response.status_code, 400)

    def test_otp_confirmed_pdf_download_is_watermarked_on_every_page(self):
        from pypdf import PdfReader

        attachment = Attachment.objects.create(
            publication=self.pub,
            file=SimpleUploadedFile("protected.pdf", create_test_pdf_bytes(), content_type="application/pdf"),
            allow_download=False,
            uploader=self.user,
        )
        otp = DownloadOTP.objects.create(
            attachment=attachment,
            user=self.user,
            code="789012",
            expires_at=timezone.now() + timezone.timedelta(minutes=15),
        )
        self.client.force_login(self.user)

        with patch("catalog.views.watermark_text_for_date", return_value="TEST WATERMARK"):
            response = self.client.post(
                reverse("catalog:confirm_attachment_otp", args=[attachment.pk]),
                {"code": otp.code},
            )

        self.assertEqual(response.status_code, 200)
        reader = PdfReader(io.BytesIO(b"".join(response.streaming_content)))
        self.assertEqual(len(reader.pages), 2)
        for page in reader.pages:
            self.assertIn("TEST WATERMARK", page.extract_text())
        otp.refresh_from_db()
        self.assertTrue(otp.used)

    def test_otp_pdf_download_fails_closed_when_watermarking_fails(self):
        attachment = Attachment.objects.create(
            publication=self.pub,
            file=SimpleUploadedFile("protected.pdf", create_test_pdf_bytes(), content_type="application/pdf"),
            allow_download=False,
            uploader=self.user,
        )
        otp = DownloadOTP.objects.create(
            attachment=attachment,
            user=self.user,
            code="789013",
            expires_at=timezone.now() + timezone.timedelta(minutes=15),
        )
        self.client.force_login(self.user)

        with patch(
            "catalog.utils.download_watermarks.apply_watermark_to_all_pages",
            side_effect=ValueError("Invalid PDF"),
        ):
            response = self.client.post(
                reverse("catalog:confirm_attachment_otp", args=[attachment.pk]),
                {"code": otp.code},
            )

        self.assertEqual(response.status_code, 500)
        self.assertNotIn(b"Test PDF", response.content)
        otp.refresh_from_db()
        self.assertFalse(otp.used)

    def test_downloadable_attachment_is_audited_and_forced_as_download(self):
        pdf_bytes = create_test_pdf_bytes()
        attachment = Attachment.objects.create(
            publication=self.pub,
            file=SimpleUploadedFile("download.pdf", pdf_bytes, content_type="application/pdf"),
            allow_download=True,
            uploader=self.user,
        )
        self.client.force_login(self.user)

        download_url = reverse("catalog:download_attachment", args=[attachment.pk])
        self.assertEqual(self.client.get(download_url).status_code, 403)
        unlock_response = self.client.post(
            reverse("catalog:unlock_attachment", args=[attachment.pk]),
            {"password": "eLib@2026"},
        )
        self.assertEqual(unlock_response.status_code, 302)
        response = self.client.get(download_url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Disposition"].startswith("attachment;"))
        self.assertEqual(ViewLog.objects.filter(user=self.user, attachment=attachment).count(), 1)
        from pypdf import PdfReader

        pdf_data = b"".join(response.streaming_content)
        reader = PdfReader(io.BytesIO(pdf_data))
        self.assertEqual(len(reader.pages), 2)
        for page in reader.pages:
            self.assertIn(watermark_text_for_date(), page.extract_text())

    def test_mp4_download_is_password_gated_and_watermarked(self):
        source_bytes = create_test_mp4_bytes()
        attachment = Attachment.objects.create(
            publication=self.pub,
            file=SimpleUploadedFile("download.mp4", source_bytes, content_type="video/mp4"),
            attachment_type="video",
            allow_download=True,
        )
        self.client.force_login(self.user)
        download_url = reverse("catalog:download_attachment", args=[attachment.pk])

        self.assertEqual(self.client.get(download_url).status_code, 403)
        self.client.post(
            reverse("catalog:unlock_attachment", args=[attachment.pk]),
            {"password": "eLib@2026"},
        )
        response = self.client.get(download_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "video/mp4")
        watermarked_bytes = b"".join(response.streaming_content)
        self.assertNotEqual(watermarked_bytes, source_bytes)

        with tempfile.TemporaryDirectory(prefix="elibrary-watermarked-output-") as temp_dir:
            path = os.path.join(temp_dir, "watermarked.mp4")
            with open(path, "wb") as output_file:
                output_file.write(watermarked_bytes)
            raw_frame = subprocess.run(
                [
                    imageio_ffmpeg.get_ffmpeg_exe(),
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-i",
                    path,
                    "-frames:v",
                    "1",
                    "-f",
                    "rawvideo",
                    "-pix_fmt",
                    "rgb24",
                    "pipe:1",
                ],
                check=True,
                capture_output=True,
                timeout=60,
            ).stdout
        frame = Image.frombytes("RGB", (320, 180), raw_frame)
        watermark_region = frame.crop((240, 130, 320, 180))
        self.assertTrue(any(max(pixel) > 100 for pixel in watermark_region.getdata()))

    def test_docx_and_pptx_downloads_include_watermarks(self):
        document = Document()
        document.add_paragraph("Demo Word file")
        docx_source = io.BytesIO()
        document.save(docx_source)

        presentation = Presentation()
        presentation.slides.add_slide(presentation.slide_layouts[6])
        pptx_source = io.BytesIO()
        presentation.save(pptx_source)

        self.client.force_login(self.user)
        for filename, content, extension in (
            ("demo.docx", docx_source.getvalue(), ".docx"),
            ("demo.pptx", pptx_source.getvalue(), ".pptx"),
        ):
            with self.subTest(filename=filename):
                attachment = Attachment.objects.create(
                    publication=self.pub,
                    file=SimpleUploadedFile(filename, content),
                    allow_download=True,
                )
                self.client.post(
                    reverse("catalog:unlock_attachment", args=[attachment.pk]),
                    {"password": "eLib@2026"},
                )
                response = self.client.get(reverse("catalog:download_attachment", args=[attachment.pk]))
                self.assertEqual(response.status_code, 200)
                output = b"".join(response.streaming_content)
                if extension == ".docx":
                    result = Document(io.BytesIO(output))
                    self.assertTrue(
                        any(
                            watermark_text_for_date() in paragraph.text
                            for section in result.sections
                            for paragraph in section.footer.paragraphs
                        )
                    )
                else:
                    result = Presentation(io.BytesIO(output))
                    self.assertTrue(
                        any(
                            watermark_text_for_date() in shape.text
                            for slide in result.slides
                            for shape in slide.shapes
                            if shape.has_text_frame
                        )
                    )

    def test_password_download_fails_closed_for_legacy_resource(self):
        attachment = Attachment.objects.create(
            publication=self.pub,
            file=SimpleUploadedFile("legacy.pdf", create_test_pdf_bytes(), content_type="application/pdf"),
            allow_download=True,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("catalog:download_attachment", args=[attachment.pk]))

        self.assertEqual(response.status_code, 403)

    def test_download_password_lockout_and_hash_are_not_exposed(self):
        attachment = Attachment.objects.create(
            publication=self.pub,
            is_external=True,
            external_url="https://example.com/password-protected-resource",
            attachment_type="video",
            allow_download=True,
        )
        self.client.force_login(self.user)

        detail = self.client.get(reverse("catalog:publication_detail", args=[self.pub.pk]))
        self.assertContains(detail, 'type="password"')
        self.assertNotContains(detail, "eLib@2026")

        unlock_url = reverse("catalog:unlock_attachment", args=[attachment.pk])
        for _ in range(5):
            self.client.post(unlock_url, {"password": "WrongPassword123!"})

        self.client.post(unlock_url, {"password": "eLib@2026"})
        self.assertEqual(
            self.client.get(reverse("catalog:download_attachment", args=[attachment.pk])).status_code,
            403,
        )

    def test_one_time_code_cannot_bypass_download_password(self):
        attachment = Attachment.objects.create(
            publication=self.pub,
            file=SimpleUploadedFile("password.pdf", create_test_pdf_bytes(), content_type="application/pdf"),
            allow_download=True,
        )
        otp = DownloadOTP.objects.create(
            attachment=attachment,
            user=self.user,
            code="987654",
            expires_at=timezone.now() + timezone.timedelta(minutes=15),
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse("catalog:confirm_download", args=[otp.code]))

        self.assertEqual(response.status_code, 403)
        otp.refresh_from_db()
        self.assertFalse(otp.used)

    def test_view_log_retention_removes_only_expired_records(self):
        from catalog.tasks import purge_expired_view_logs

        old_log = ViewLog.objects.create(user=self.user, publication=self.pub)
        recent_log = ViewLog.objects.create(user=self.user, publication=self.pub)
        ViewLog.objects.filter(pk=old_log.pk).update(
            timestamp=timezone.now() - timezone.timedelta(days=366)
        )

        with override_settings(VIEW_LOG_RETENTION_DAYS=365):
            deleted_count = purge_expired_view_logs.run()

        self.assertEqual(deleted_count, 1)
        self.assertFalse(ViewLog.objects.filter(pk=old_log.pk).exists())
        self.assertTrue(ViewLog.objects.filter(pk=recent_log.pk).exists())

    def test_uploaded_video_stream_supports_http_byte_ranges(self):
        attachment = Attachment.objects.create(
            publication=self.pub,
            file=SimpleUploadedFile("lesson.mp4", b"0123456789", content_type="video/mp4"),
            attachment_type="video",
            allow_download=True,
        )
        self.client.force_login(self.user)
        stream_url = reverse("catalog:stream_attachment", args=[attachment.pk])
        download_url = reverse("catalog:download_attachment", args=[attachment.pk])
        self.assertEqual(self.client.get(download_url).status_code, 403)

        response = self.client.get(
            stream_url,
            HTTP_RANGE="bytes=2-5",
        )

        self.assertEqual(response.status_code, 206)
        self.assertEqual(response["Content-Type"], "video/mp4")
        self.assertEqual(response["Content-Range"], "bytes 2-5/10")
        self.assertIn("inline", response["Content-Disposition"])
        self.assertEqual(b"".join(response.streaming_content), b"2345")

    def test_protected_video_stream_requires_otp(self):
        attachment = Attachment.objects.create(
            publication=self.pub,
            file=SimpleUploadedFile("protected.mp4", b"0123456789", content_type="video/mp4"),
            attachment_type="video",
            allow_download=False,
        )
        self.client.force_login(self.user)
        stream_url = reverse("catalog:stream_attachment", args=[attachment.pk])

        self.assertEqual(self.client.get(stream_url).status_code, 403)
        otp = DownloadOTP.objects.create(
            attachment=attachment,
            user=self.user,
            code="654321",
            expires_at=timezone.now() + timezone.timedelta(minutes=15),
        )
        response = self.client.post(
            reverse("catalog:confirm_attachment_otp", args=[attachment.pk]),
            {"code": otp.code},
        )

        self.assertRedirects(response, reverse("catalog:publication_detail", args=[self.pub.pk]))
        self.assertEqual(self.client.get(stream_url, HTTP_RANGE="bytes=0-1").status_code, 206)

    def test_restricted_attachment_cannot_bypass_otp(self):
        attachment = Attachment.objects.create(
            publication=self.pub,
            is_external=True,
            external_url="https://example.com/resource",
            allow_download=False,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("catalog:download_attachment", args=[attachment.pk]))

        self.assertEqual(response.status_code, 403)
        self.assertFalse(ViewLog.objects.filter(user=self.user, attachment=attachment).exists())

    def test_protected_attachment_file_is_not_publicly_served_from_media_url(self):
        attachment = Attachment.objects.create(
            publication=self.pub,
            file=SimpleUploadedFile("private.pdf", b"private-resource", content_type="application/pdf"),
            allow_download=False,
            uploader=self.user,
        )

        response = self.client.get(attachment.file.url)

        self.assertEqual(response.status_code, 404)

    def test_publication_detail_renders_resource_actions_and_staff_upload_link(self):
        attachment = Attachment.objects.create(
            publication=self.pub,
            is_external=True,
            external_url="https://example.com/video",
            allow_download=False,
            attachment_type="video",
        )
        detail_url = reverse("catalog:publication_detail", args=[self.pub.pk])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 302)
        self.client.force_login(self.user)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Request access code")
        self.assertNotContains(response, "Log in to access")
        self.assertContains(response, "Instructional Video")
        self.assertNotContains(response, 'href="https://example.com/video"')

        staff = User.objects.create_user(
            username="resource-staff",
            password="pass1234",
            user_type="staff",
            agreed_to_terms=True,
        )
        self.client.force_login(staff)
        response = self.client.get(reverse("catalog:publication_detail", args=[self.pub.pk]))
        self.assertContains(response, "Add resource")
        self.assertContains(response, reverse("catalog:confirm_attachment_otp", args=[attachment.pk]))

    def test_downloadable_external_video_url_is_hidden_from_anonymous_visitors(self):
        attachment = Attachment.objects.create(
            publication=self.pub,
            is_external=True,
            external_url="https://example.com/public-video",
            allow_download=True,
            attachment_type="video",
        )
        detail_url = reverse("catalog:publication_detail", args=[self.pub.pk])

        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 302)

        self.client.force_login(self.user)
        response = self.client.get(detail_url)
        self.assertContains(response, attachment.external_url)
        self.assertContains(response, reverse("catalog:unlock_attachment", args=[attachment.pk]))
        self.assertEqual(
            self.client.get(reverse("catalog:download_attachment", args=[attachment.pk])).status_code,
            403,
        )
        self.client.post(
            reverse("catalog:unlock_attachment", args=[attachment.pk]),
            {"password": "eLib@2026"},
        )
        response = self.client.get(reverse("catalog:download_attachment", args=[attachment.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], attachment.external_url)


class AttachmentFileTypeLabelTests(TestCase):
    def test_file_type_label(self):
        from catalog.models import Attachment
        cases = [("attachments/a.pdf", False, "other", "PDF"), ("attachments/a.pptx", False, "other", "PowerPoint"), ("attachments/a.mp4", False, "video", "Video"), ("", True, "video", "Video Link"), ("", True, "other", "Link")]
        for name, external, kind, expected in cases:
            self.assertEqual(Attachment(file=name, is_external=external, attachment_type=kind).file_type_label, expected)
