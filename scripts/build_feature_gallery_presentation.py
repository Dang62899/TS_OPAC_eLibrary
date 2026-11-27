import argparse
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt


COPYRIGHT = "9533rd Research and Development Squadron | Jacksone Agtarap"
SLIDE_WIDTH = 10
SLIDE_HEIGHT = SLIDE_WIDTH * 595 / 842
BACKGROUND = RGBColor(244, 247, 250)
NAVY = RGBColor(11, 47, 82)
TEAL = RGBColor(54, 181, 197)
INK = RGBColor(18, 43, 64)
MUTED = RGBColor(82, 103, 121)


def add_text(slide, text, left, top, width, height, size, color, bold=False):
    shape = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    frame = shape.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = 0
    frame.margin_right = 0
    frame.margin_top = 0
    frame.margin_bottom = 0
    frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    paragraph = frame.paragraphs[0]
    paragraph.text = text
    paragraph.font.name = "Aptos"
    paragraph.font.size = Pt(size)
    paragraph.font.bold = bold
    paragraph.font.color.rgb = color
    return shape


def add_background(slide):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = BACKGROUND
    band = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, 0, Inches(SLIDE_WIDTH), Inches(0.09)
    )
    band.fill.solid()
    band.fill.fore_color.rgb = NAVY
    band.line.fill.background()


def add_footer(slide, page_text):
    line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0.36),
        Inches(SLIDE_HEIGHT - 0.36),
        Inches(SLIDE_WIDTH - 0.72),
        Inches(0.008),
    )
    line.fill.solid()
    line.fill.fore_color.rgb = RGBColor(213, 224, 232)
    line.line.fill.background()
    add_text(
        slide,
        COPYRIGHT,
        0.38,
        SLIDE_HEIGHT - 0.31,
        6.8,
        0.18,
        7.5,
        MUTED,
    )
    add_text(
        slide,
        page_text,
        8.1,
        SLIDE_HEIGHT - 0.31,
        1.5,
        0.18,
        7.5,
        MUTED,
    ).text_frame.paragraphs[0].alignment = PP_ALIGN.RIGHT


def add_cover(presentation):
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = NAVY
    top_band = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, 0, Inches(SLIDE_WIDTH), Inches(0.12)
    )
    top_band.fill.solid()
    top_band.fill.fore_color.rgb = TEAL
    top_band.line.fill.background()

    add_text(slide, "TS eLibrary", 0.65, 0.72, 8.7, 0.55, 30, RGBColor(255, 255, 255), True)
    add_text(
        slide,
        "Feature-by-Feature Screenshots",
        0.65,
        1.34,
        8.7,
        0.48,
        22,
        RGBColor(255, 255, 255),
        True,
    )
    add_text(
        slide,
        "A visual walkthrough of the current local application",
        0.65,
        1.9,
        8.7,
        0.32,
        12,
        RGBColor(217, 231, 242),
    )

    categories = [
        ("CATALOG & RESEARCH", "Search, filters, research, publication details"),
        ("ACCOUNTS & IDENTITY", "Registration, profiles, registry, agreement"),
        ("DIGITAL COLLECTION", "Resources, uploads, previews, downloads"),
        ("CIRCULATION", "Loans, check-in, holds, requests, transit"),
        ("ADMIN & REPORTING", "Notifications, reports, access monitoring"),
    ]
    left = 0.65
    card_width = 1.72
    gap = 0.12
    for index, (category, details) in enumerate(categories):
        x = left + index * (card_width + gap)
        card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(x),
            Inches(2.62),
            Inches(card_width),
            Inches(1.48),
        )
        card.fill.solid()
        card.fill.fore_color.rgb = RGBColor(18, 64, 99)
        card.line.color.rgb = RGBColor(48, 101, 135)
        add_text(
            slide,
            category,
            x + 0.12,
            2.82,
            card_width - 0.24,
            0.35,
            9,
            TEAL,
            True,
        )
        add_text(
            slide,
            details,
            x + 0.12,
            3.25,
            card_width - 0.24,
            0.62,
            9,
            RGBColor(240, 246, 250),
        )

    add_text(
        slide,
        "Screenshots are from the local demo. Sample records may be shown; personal identifiers are obscured.",
        0.65,
        4.65,
        8.7,
        0.55,
        10,
        RGBColor(217, 231, 242),
    )
    add_text(
        slide,
        COPYRIGHT,
        0.65,
        SLIDE_HEIGHT - 0.48,
        8.7,
        0.2,
        8,
        RGBColor(217, 231, 242),
    )
    return slide


def extract_feature_pages(pdf_path):
    reader = PdfReader(str(pdf_path))
    if len(reader.pages) < 2:
        raise ValueError(f"Expected a cover and feature pages in {pdf_path}")

    features = []
    for page_number, page in enumerate(reader.pages[1:], start=1):
        lines = [
            line.strip()
            for line in (page.extract_text() or "").splitlines()
            if line.strip()
        ]
        if len(lines) < 3 or not page.images:
            raise ValueError(
                f"PDF page {page_number + 1} is missing its feature text or screenshot"
            )
        image_data = page.images[0].data
        features.append((lines[0], lines[1], lines[2], image_data))
    return features


def add_feature_slide(presentation, feature, index, total):
    category, title, description, image_data = feature
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    add_background(slide)

    add_text(slide, category, 0.42, 0.18, 9.16, 0.19, 8, TEAL, True)
    title_size = 20 if len(title) > 42 else 22
    add_text(slide, title, 0.42, 0.4, 9.16, 0.4, title_size, INK, True)
    add_text(slide, description, 0.42, 0.83, 9.16, 0.42, 9.5, MUTED)

    image = BytesIO(image_data)
    from PIL import Image

    with Image.open(image) as opened_image:
        image_width, image_height = opened_image.size
    max_width = 9.15
    max_height = 5.35
    scale = min(max_width / image_width, max_height / image_height)
    width = Inches(image_width * scale)
    height = Inches(image_height * scale)
    left = Inches((SLIDE_WIDTH - image_width * scale) / 2)
    top = Inches(1.34 + (max_height - image_height * scale) / 2)
    slide.shapes.add_picture(image, left, top, width=width, height=height)
    add_footer(slide, f"Feature {index:02} / {total:02}")
    return slide


def build_presentation(pdf_path, output_path):
    features = extract_feature_pages(pdf_path)
    presentation = Presentation()
    presentation.slide_width = Inches(SLIDE_WIDTH)
    presentation.slide_height = Inches(SLIDE_HEIGHT)
    presentation.core_properties.title = "TS eLibrary - Feature-by-Feature Screenshots"
    presentation.core_properties.subject = (
        "Local application screenshots organized by feature"
    )
    presentation.core_properties.author = COPYRIGHT

    add_cover(presentation)
    for index, feature in enumerate(features, start=1):
        add_feature_slide(presentation, feature, index, len(features))

    presentation.save(output_path)
    return len(features)


def main():
    parser = argparse.ArgumentParser(
        description="Build a feature-by-feature screenshot PowerPoint from the gallery PDF."
    )
    parser.add_argument(
        "--pdf",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "TS_eLibrary_Feature_Screenshots_2026-10-30.pdf",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "TS_eLibrary_Feature_Screenshots.pptx",
    )
    args = parser.parse_args()
    count = build_presentation(args.pdf, args.output)
    print(f"Created {args.output} with one cover and {count} feature slides.")


if __name__ == "__main__":
    main()
