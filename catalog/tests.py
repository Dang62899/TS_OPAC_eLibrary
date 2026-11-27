import io
import subprocess
import tempfile

from django.test import TestCase
from docx import Document
import imageio_ffmpeg
from pptx import Presentation

from catalog.forms import AttachmentForm, SearchForm
from catalog.models import Attachment, Publication, PublicationType
from catalog.search import AdvancedSearch
from catalog.utils.download_watermarks import watermark_office_document, watermark_video_to_temp


class SearchFormTests(TestCase):
    def test_unit_filter_offers_requested_units(self):
        unit_choices = list(SearchForm().fields["unit"].choices)

        self.assertEqual(
            [value for value, _label in unit_choices],
            ["", "HAS", "951", "952", "953"],
        )

    def test_attachment_form_offers_requested_units(self):
        unit_choices = list(AttachmentForm().fields["unit"].choices)

        self.assertEqual(
            [value for value, _label in unit_choices],
            ["", "HAS", "951", "952", "953"],
        )

    def test_attachment_form_preserves_existing_legacy_unit(self):
        form = AttachmentForm(instance=Attachment(unit="Research"))

        self.assertIn("Research", [value for value, _label in form.fields["unit"].choices])


class DownloadWatermarkTests(TestCase):
    def test_docx_download_copy_has_watermark_in_each_section_footer(self):
        document = Document()
        document.add_paragraph("Demo download document")
        source = io.BytesIO()
        document.save(source)

        watermarked = watermark_office_document(
            io.BytesIO(source.getvalue()), ".docx", "TEST WATERMARK"
        )
        result = Document(watermarked)

        self.assertTrue(result.sections)
        self.assertTrue(
            all(
                any("TEST WATERMARK" in paragraph.text for paragraph in section.footer.paragraphs)
                for section in result.sections
            )
        )

    def test_pptx_download_copy_has_watermark_on_each_slide(self):
        presentation = Presentation()
        presentation.slides.add_slide(presentation.slide_layouts[6])
        presentation.slides.add_slide(presentation.slide_layouts[6])
        source = io.BytesIO()
        presentation.save(source)

        watermarked = watermark_office_document(
            io.BytesIO(source.getvalue()), ".pptx", "TEST WATERMARK"
        )
        result = Presentation(watermarked)

        self.assertEqual(len(result.slides), 2)
        for slide in result.slides:
            self.assertTrue(
                any("TEST WATERMARK" in shape.text for shape in slide.shapes if shape.has_text_frame)
            )

    def test_mp4_processor_outputs_a_watermarked_video(self):
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        with tempfile.TemporaryDirectory(prefix="elibrary-video-source-") as source_directory:
            source_path = f"{source_directory}/source.mp4"
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
                    "color=c=black:s=160x90:d=0.25",
                    "-an",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    source_path,
                ],
                check=True,
                capture_output=True,
                timeout=60,
            )
            with open(source_path, "rb") as source:
                output_path, temporary_directory = watermark_video_to_temp(source, "TEST WATERMARK")
            try:
                self.assertGreater(output_path.stat().st_size, 0)
            finally:
                temporary_directory.cleanup()


class AdvancedSearchTests(TestCase):
    def setUp(self):
        self.pub_type = PublicationType.objects.create(name="Manual", code="MAN", description="Manual")
        self.publication = Publication.objects.create(
            title="Emergency Response Manual",
            abstract="A practical guide for incident response.",
            publication_type=self.pub_type,
        )
        self.other_publication = Publication.objects.create(
            title="Network Security Guide",
            abstract="A guide for secure system administration.",
            publication_type=self.pub_type,
        )

    def test_boolean_and_phrase_search_returns_expected_results(self):
        result = AdvancedSearch.advanced_search(query='"Emergency Response" AND manual')

        self.assertEqual(result["total_count"], 1)
        self.assertEqual(list(result["results"]), [self.publication])

    def test_not_operator_excludes_matching_terms(self):
        result = AdvancedSearch.advanced_search(query='response NOT security')

        self.assertEqual(result["total_count"], 1)
        self.assertEqual(list(result["results"]), [self.publication])
