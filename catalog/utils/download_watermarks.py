import io
import shutil
import subprocess
import tempfile
from pathlib import Path
from django.http import FileResponse

from .pdf_utils import apply_watermark_to_all_pages

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor
from pptx import Presentation
from pptx.dml.color import RGBColor as PptxRGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt as PptxPt


class WatermarkProcessingError(RuntimeError):
    """Raised when a downloadable file cannot be safely watermarked."""


class UnsupportedWatermarkFormat(ValueError):
    """Raised when the app has no watermark processor for a file type."""


def watermarked_attachment_response(attachment, watermark_text):
    filename = Path(attachment.file.name).name
    extension = Path(filename).suffix.lower()

    if extension == ".pdf":
        try:
            with attachment.file.open("rb") as source:
                output = io.BytesIO(apply_watermark_to_all_pages(source, watermark_text=watermark_text))
        except Exception as exc:
            raise WatermarkProcessingError("PDF watermarking failed") from exc
        return FileResponse(output, as_attachment=True, filename=filename, content_type="application/pdf")

    if extension in {".docx", ".pptx"}:
        with attachment.file.open("rb") as source:
            output = watermark_office_document(source, extension, watermark_text)
        content_type = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            if extension == ".docx"
            else "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
        return FileResponse(output, as_attachment=True, filename=filename, content_type=content_type)

    if extension == ".mp4":
        with attachment.file.open("rb") as source:
            output_path, temporary_directory = watermark_video_to_temp(source, watermark_text)
        response = FileResponse(
            output_path.open("rb"),
            as_attachment=True,
            filename=filename,
            content_type="video/mp4",
        )
        response._resource_closers.append(temporary_directory.cleanup)
        return response

    raise UnsupportedWatermarkFormat(extension or "unknown")


def watermark_office_document(input_stream, extension, watermark_text):
    extension = extension.lower()
    output = io.BytesIO()
    try:
        if extension == ".docx":
            document = Document(input_stream)
            for section in document.sections:
                paragraph = section.footer.add_paragraph()
                paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                run = paragraph.add_run(watermark_text)
                run.font.size = Pt(8)
                run.font.color.rgb = RGBColor(128, 128, 128)
            document.save(output)
        elif extension == ".pptx":
            presentation = Presentation(input_stream)
            for slide in presentation.slides:
                shape = slide.shapes.add_textbox(
                    Inches(0.3),
                    presentation.slide_height - Inches(0.35),
                    presentation.slide_width - Inches(0.6),
                    Inches(0.25),
                )
                paragraph = shape.text_frame.paragraphs[0]
                paragraph.alignment = PP_ALIGN.RIGHT
                run = paragraph.add_run()
                run.text = watermark_text
                run.font.size = PptxPt(9)
                run.font.color.rgb = PptxRGBColor(128, 128, 128)
            presentation.save(output)
        else:
            raise UnsupportedWatermarkFormat(extension)
    except UnsupportedWatermarkFormat:
        raise
    except Exception as exc:
        raise WatermarkProcessingError("Office document watermarking failed") from exc

    output.seek(0)
    return output


def _escape_filter_path(path):
    return str(Path(path).resolve()).replace("\\", "/").replace(":", r"\:")


def _find_font():
    candidates = (
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    )
    return next((path for path in candidates if path.is_file()), None)


def watermark_video_to_temp(input_stream, watermark_text):
    """Transcode an MP4 to a temporary watermarked MP4; caller owns directory cleanup."""
    temporary_directory = tempfile.TemporaryDirectory(prefix="elibrary-video-watermark-")
    directory = Path(temporary_directory.name)
    input_path = directory / "original.mp4"
    output_path = directory / "watermarked.mp4"
    text_path = directory / "watermark.txt"

    try:
        input_stream.seek(0)
        with input_path.open("wb") as destination:
            shutil.copyfileobj(input_stream, destination)
        text_path.write_text(watermark_text, encoding="utf-8")
        font_path = _find_font()
        if font_path is None:
            raise WatermarkProcessingError("No supported font is available for video watermarking")

        import imageio_ffmpeg

        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        filter_spec = (
            f"drawtext=textfile='{_escape_filter_path(text_path)}':"
            f"fontfile='{_escape_filter_path(font_path)}':"
            "fontcolor=white@0.9:fontsize=h/24:box=1:boxcolor=black@0.4:boxborderw=10:"
            "x=w-tw-20:y=h-th-20:expansion=none"
        )
        subprocess.run(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(input_path),
                "-vf",
                filter_spec,
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "27",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-movflags",
                "+faststart",
                str(output_path),
            ],
            check=True,
            capture_output=True,
            timeout=600,
        )
        if not output_path.is_file() or output_path.stat().st_size == 0:
            raise WatermarkProcessingError("Video watermarking produced no output")
        return output_path, temporary_directory
    except Exception as exc:
        temporary_directory.cleanup()
        if isinstance(exc, WatermarkProcessingError):
            raise
        raise WatermarkProcessingError("Video watermarking failed") from exc
