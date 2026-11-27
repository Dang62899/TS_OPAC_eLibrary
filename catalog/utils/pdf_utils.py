import io
from django.conf import settings
from django.utils import timezone

try:
    from pypdf import PdfReader, PdfWriter, Transformation
except ImportError:  # pragma: no cover - compatibility fallback for older environments
    from PyPDF2 import PdfReader, PdfWriter, Transformation

from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import os


def _create_watermark_pdf(text: str, page_width: float, page_height: float) -> bytes:
    """Generate a one-page PDF with the watermark text centered."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
    c.setFont("Helvetica", 12)
    c.setFillColorRGB(0.6, 0.6, 0.6)
    # Draw logo on top-left if available
    logo_path = None
    try:
        logo_rel = getattr(settings, "ELIBRARY_LOGO", "images/elibrary_logo.png")
        # STATICFILES_DIRS assumed to include BASE_DIR/static
        # Try typical static path
        possible = [
            os.path.join(settings.BASE_DIR, "static", logo_rel),
            os.path.join(settings.BASE_DIR, "staticfiles", logo_rel),
            os.path.join(settings.BASE_DIR, logo_rel),
        ]
        for p in possible:
            if os.path.exists(p):
                logo_path = p
                break
    except Exception:
        logo_path = None

    if logo_path:
        try:
            img = ImageReader(logo_path)
            # scale logo to fit width ~120 or page width*0.25
            iw, ih = img.getSize()
            max_w = min(120, page_width * 0.25)
            ratio = min(max_w / iw, (page_height * 0.12) / ih)
            w = iw * ratio
            h = ih * ratio
            # draw with transparency mask if supported
            c.drawImage(img, 20, page_height - h - 20, width=w, height=h, mask='auto')
        except Exception:
            pass

    # place text at bottom-right with margin
    margin = 40
    x = page_width - margin
    y = margin
    c.drawRightString(x, y, text)
    c.save()
    buffer.seek(0)
    return buffer.read()


def merge_first_two_pages_with_watermark(input_pdf_stream, watermark_text=None, combine_first_two=False):
    """Return the first two pages, optionally combined side by side, with a watermark."""
    reader = PdfReader(input_pdf_stream)
    writer = PdfWriter()

    num_pages = len(reader.pages)
    if combine_first_two and num_pages >= 2:
        first_page, second_page = reader.pages[0], reader.pages[1]
        first_width = float(first_page.mediabox.width)
        second_width = float(second_page.mediabox.width)
        page_height = max(float(first_page.mediabox.height), float(second_page.mediabox.height))
        combined_writer = PdfWriter()
        combined_page = combined_writer.add_blank_page(width=first_width + second_width, height=page_height)
        combined_page.merge_transformed_page(first_page, Transformation().translate(tx=0, ty=0))
        combined_page.merge_transformed_page(second_page, Transformation().translate(tx=first_width, ty=0))
        pages_to_include = [combined_page]
    else:
        pages_to_include = list(reader.pages[:2])

    for page in pages_to_include:
        # apply watermark if provided
        if watermark_text:
            # create watermark PDF matching page size
            media_box = page.mediabox
            page_width = float(media_box.right) - float(media_box.left)
            page_height = float(media_box.top) - float(media_box.bottom)
            wm_pdf = _create_watermark_pdf(watermark_text, page_width, page_height)
            wm_reader = PdfReader(io.BytesIO(wm_pdf))
            watermark_page = wm_reader.pages[0]
            page.merge_page(watermark_page)

        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output.read()


def apply_watermark_to_all_pages(input_pdf_stream, watermark_text=None):
    """Overlay the watermark (text + optional logo) on every page of the PDF.

    Returns the bytes of the new PDF.
    """
    reader = PdfReader(input_pdf_stream)
    writer = PdfWriter()

    for page in reader.pages:
        if watermark_text:
            media_box = page.mediabox
            page_width = float(media_box.right) - float(media_box.left)
            page_height = float(media_box.top) - float(media_box.bottom)
            wm_pdf = _create_watermark_pdf(watermark_text, page_width, page_height)
            wm_reader = PdfReader(io.BytesIO(wm_pdf))
            watermark_page = wm_reader.pages[0]
            page.merge_page(watermark_page)

        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output.read()


def watermark_text_for_date(fmt="%Y-%m-%d"):
    # Include configured library name in watermark if available
    date = timezone.localtime(timezone.now()).strftime(fmt)
    name = getattr(settings, "ELIBRARY_NAME", "Elibrary")
    return f"{date} - {name}"
