import argparse
from io import BytesIO
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt
from pypdf import PdfReader


COPYRIGHT = "9533rd Research and Development Squadron | Jacksone Agtarap"
SLIDE_WIDTH = 10
SLIDE_HEIGHT = 5.625
NAVY = RGBColor(0, 32, 96)
BLUE = RGBColor(25, 82, 155)
GOLD = RGBColor(224, 169, 30)
INK = RGBColor(20, 36, 64)
MUTED = RGBColor(71, 84, 105)

OBSOLETE_MASTER_TEXT = (
    "C O N F I D E N T I A L",
    "Flight Plan Vision:",
    "FOR OFFICIAL USE ONLY",
    "Presented to: WC, 950CEWW",
    "Office Symbol",
    "CAPABLE    CREDIBLE   SUSTAINABLE",
)

FEATURE_DETAILS = {
    "Catalog search": (
        "Search the public collection and open matching records to move from a query to item details.",
        "Core discovery is visible; search quality depends on complete, consistent catalog metadata.",
    ),
    "Advanced catalog filters": (
        "Combine catalog fields and filters to narrow a broad result set to relevant resources.",
        "Useful for precise retrieval; incomplete metadata can hide otherwise relevant records.",
    ),
    "Research browse": (
        "Browse research papers using year and class groupings rather than a keyword search alone.",
        "The local demo has no papers tagged for these filters, so populated results still need validation.",
    ),
    "Publication details and availability": (
        "Review publication metadata, physical copies, attachments, and available borrower actions together.",
        "Brings decision information together; accuracy depends on maintained copy and attachment records.",
    ),
    "Borrower registration": (
        "Collect borrower identity and registration details through a self-service account form.",
        "The onboarding path is demonstrated; confirm eligibility checks and required fields in the staff workflow.",
    ),
    "Sign-in": (
        "Authenticate borrowers and staff before they enter the functions available to their account.",
        "The entry point is demonstrated; verify role boundaries and account recovery during acceptance testing.",
    ),
    "User agreement": (
        "Present the user agreement and record a borrower's acceptance before using the library.",
        "Makes policy acceptance visible; owners still need to approve wording and its update process.",
    ),
    "User registry": (
        "Let staff filter accounts by role, unit, and lifecycle status, then review class and access state.",
        "Supports student-to-alumni oversight; reconcile status changes with the authoritative roster.",
    ),
    "Profile and identity controls": (
        "Display profile information and identity settings, including class and unit details where configured.",
        "Confirm photo and personal-data visibility are restricted appropriately before live use.",
    ),
    "My library account": (
        "Give borrowers one place to review account status, loans, holds, requests, and loan history.",
        "Improves self-service; displayed account information depends on current circulation records.",
    ),
    "Staff password reset": (
        "Allow authorized staff to set a new password when a borrower needs account recovery.",
        "Provides a staff recovery path; share temporary credentials through a separate secure channel.",
    ),
    "Digital resources: view, preview, and download": (
        "Support document and presentation downloads, instructional video playback, and PDF previews.",
        "Multiple formats and controls are demonstrated; test permissions and OTP behavior in staging.",
    ),
    "Publication management": (
        "Search and maintain publication records and their associated physical copies.",
        "Centralizes catalog upkeep; consistent review helps prevent duplicate and stale records.",
    ),
    "Create publication record": (
        "Enter bibliographic metadata, authors, subjects, publication type, and other record details.",
        "Supports structured cataloging; review required fields and vocabulary consistency before rollout.",
    ),
    "Upload a digital attachment": (
        "Attach an uploaded file or external link and configure resource tags and download controls.",
        "Flexible content intake; confirm storage limits, link availability, and access settings before launch.",
    ),
    "Manage physical copies": (
        "Track item identifiers, library locations, circulation status, and physical condition.",
        "Supports location and availability visibility; accuracy depends on regular inventory reconciliation.",
    ),
    "Staff dashboard": (
        "Summarize circulation activity and provide staff with quick actions and trend/status charts.",
        "Useful as an operational overview; the counts shown are demo data, not live performance metrics.",
    ),
    "Circulation hub": (
        "Bring checkout, check-in, holds, borrower records, reports, and transit tools into one staff area.",
        "Makes common tasks easier to find; confirm role permissions and task paths during user acceptance.",
    ),
    "Check out an item": (
        "Record the borrower and item, capture notes, and calculate the expected due date.",
        "Captures the core checkout; verify loan rules, exception handling, and transaction history.",
    ),
    "Check in an item": (
        "Record returns and surface overdue or hold-related follow-up for staff.",
        "Supports return handling; timely status updates are needed for accurate follow-up.",
    ),
    "Manage holds": (
        "Review hold queues, position, pickup readiness, and pickup location.",
        "Makes queue states actionable; verify reservation order and pickup notifications in testing.",
    ),
    "Checkout requests": (
        "Review borrower requests and provide staff with approve or deny actions.",
        "Adds a staff decision point; confirm notifications and decision history in staging.",
    ),
    "Item transit": (
        "Track items as they move between library locations.",
        "Improves handoff visibility; record each send and receipt to keep item status accurate.",
    ),
    "Borrower management": (
        "Search borrower accounts and review status and active-loan limits.",
        "Consolidates borrower review; use validated registry data and least-privilege access.",
    ),
    "Notifications": (
        "Review staff and borrower notices and filter the list to unread items.",
        "Supports timely follow-up; verify delivery and retention in the target environment.",
    ),
    "Circulation reports": (
        "Provide navigation to overdue, statistics, borrower, holds, and resource-access reports.",
        "Surfaces key reporting tools; validate report totals and exports against source transactions.",
    ),
    "Circulation statistics": (
        "Summarize checkout and return totals, popular items, active borrowers, and circulation mix.",
        "Useful for trend review; the screenshot contains demo counts, not operational metrics.",
    ),
    "Resource Access Monitor": (
        "Let staff review recorded file views, previews, video plays, and downloads by resource.",
        "Improves accountability; logs need retention and privacy controls and are not proof of user intent.",
    ),
}

FEATURE_SUBTITLES = {
    "Digital resources: view, preview, and download": (
        "Preview PDFs, play instructional videos, and download digital resources."
    ),
    "Circulation statistics": (
        "Review circulation totals and trends by borrower and publication type."
    ),
}


def remove_shape(shape):
    shape._element.getparent().remove(shape._element)


def remove_old_template_markings(presentation):
    containers = []
    for master in presentation.slide_masters:
        containers.append(master)
        containers.extend(master.slide_layouts)

    for container in containers:
        for shape in list(container.shapes):
            if not getattr(shape, "has_text_frame", False):
                continue
            text = shape.text.strip()
            if "#" in text or any(marker in text for marker in OBSOLETE_MASTER_TEXT):
                remove_shape(shape)


def add_text(
    slide,
    text,
    left,
    top,
    width,
    height,
    size,
    color,
    bold=False,
    font_name="Arial",
    vertical_anchor=MSO_ANCHOR.MIDDLE,
):
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
    frame.vertical_anchor = vertical_anchor
    paragraph = frame.paragraphs[0]
    paragraph.text = text
    paragraph.font.name = font_name
    paragraph.font.size = Pt(size)
    paragraph.font.bold = bold
    paragraph.font.color.rgb = color
    return shape


def set_cover_title(shape):
    paragraph = shape.text_frame.paragraphs[0]
    if len(paragraph.runs) < 2:
        raise ValueError("The Air Force template cover title structure changed.")
    paragraph.runs[0].text = "TS eLibrary "
    paragraph.runs[1].text = "Feature-by-Feature Gallery"
    paragraph.runs[1].font.size = Pt(21)
    for run in paragraph.runs[2:]:
        run.text = ""


def remove_cover_date_and_footer(cover):
    obsolete_names = {
        "Google Shape;235;p39",
        "Google Shape;236;p39",
        "Google Shape;237;p39",
    }
    for shape in list(cover.shapes):
        if shape.name in obsolete_names:
            remove_shape(shape)


def add_cover_footer(cover):
    strip = cover.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        0,
        Inches(5.45),
        Inches(SLIDE_WIDTH),
        Inches(SLIDE_HEIGHT - 5.45),
    )
    strip.fill.solid()
    strip.fill.fore_color.rgb = NAVY
    strip.line.fill.background()

    gold_rule = cover.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        0,
        Inches(5.425),
        Inches(SLIDE_WIDTH),
        Inches(0.025),
    )
    gold_rule.fill.solid()
    gold_rule.fill.fore_color.rgb = GOLD
    gold_rule.line.fill.background()

    add_text(
        cover,
        COPYRIGHT,
        0.68,
        5.08,
        6.35,
        0.2,
        8,
        NAVY,
        font_name="Arial",
    )


def clear_non_cover_slides(presentation):
    slide_ids = presentation.slides._sldIdLst
    for slide_id in list(slide_ids)[1:]:
        presentation.part.drop_rel(slide_id.rId)
        slide_ids.remove(slide_id)


def clear_slide_shapes(slide):
    for shape in list(slide.shapes):
        remove_shape(shape)


def add_footer(slide, page_text):
    strip = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        0,
        Inches(5.0),
        Inches(SLIDE_WIDTH),
        Inches(SLIDE_HEIGHT - 5.0),
    )
    strip.fill.solid()
    strip.fill.fore_color.rgb = RGBColor(255, 255, 255)
    strip.line.fill.background()

    rule = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0.35),
        Inches(5.0),
        Inches(9.3),
        Inches(0.025),
    )
    rule.fill.solid()
    rule.fill.fore_color.rgb = BLUE
    rule.line.fill.background()

    gold_rule = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0.35),
        Inches(5.025),
        Inches(9.3),
        Inches(0.012),
    )
    gold_rule.fill.solid()
    gold_rule.fill.fore_color.rgb = GOLD
    gold_rule.line.fill.background()

    add_text(slide, COPYRIGHT, 0.38, 5.12, 7.0, 0.2, 7.5, MUTED)
    add_text(slide, page_text, 7.75, 5.12, 1.85, 0.2, 7.5, NAVY, bold=True)


def extract_features(pdf_path):
    reader = PdfReader(str(pdf_path))
    if len(reader.pages) < 2:
        raise ValueError(f"Expected a cover and feature pages in {pdf_path}")

    features = []
    for page_number, page in enumerate(reader.pages[1:], start=2):
        lines = [
            line.strip()
            for line in (page.extract_text() or "").splitlines()
            if line.strip()
        ]
        if len(lines) < 3 or not page.images:
            raise ValueError(
                f"PDF page {page_number} is missing feature text or its screenshot."
            )
        features.append(
            (lines[0], lines[1], lines[2], page.images[0].data)
        )
    return features


def add_feature_slide(presentation, layout, feature, index, total):
    category, title, description, image_data = feature
    try:
        explanation, evaluation = FEATURE_DETAILS[title]
    except KeyError as error:
        raise ValueError(
            f"No explanation and evaluation are defined for {title!r}"
        ) from error
    subtitle = FEATURE_SUBTITLES.get(title, description)

    slide = presentation.slides.add_slide(layout)
    clear_slide_shapes(slide)

    add_text(
        slide,
        category.upper(),
        0.35,
        0.2,
        9.3,
        0.2,
        8.5,
        BLUE,
        bold=True,
        font_name="Arial",
    )
    title_size = 19 if len(title) > 40 else 22
    add_text(
        slide,
        title,
        0.35,
        0.39,
        9.3,
        0.46,
        title_size,
        NAVY,
        bold=True,
        font_name="Arial Black",
    )
    add_text(
        slide,
        subtitle,
        0.35,
        0.86,
        9.3,
        0.4,
        8.5,
        MUTED,
        font_name="Arial",
    )

    image_stream = BytesIO(image_data)
    with Image.open(image_stream) as screenshot:
        image_width, image_height = screenshot.size
    image_left = 0.35
    image_top = 1.3
    max_width = 5.45
    max_height = 3.58
    scale = min(max_width / image_width, max_height / image_height)
    width = Inches(image_width * scale)
    height = Inches(image_height * scale)
    left = Inches(image_left + (max_width - image_width * scale) / 2)
    top = Inches(image_top + (max_height - image_height * scale) / 2)
    image_stream.seek(0)
    slide.shapes.add_picture(image_stream, left, top, width=width, height=height)

    panel = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(5.95),
        Inches(1.3),
        Inches(3.7),
        Inches(3.58),
    )
    panel.fill.solid()
    panel.fill.fore_color.rgb = RGBColor(245, 248, 252)
    panel.line.color.rgb = RGBColor(218, 227, 238)

    add_text(
        slide,
        "HOW IT WORKS",
        6.15,
        1.5,
        3.3,
        0.22,
        8.5,
        BLUE,
        bold=True,
    )
    add_text(
        slide,
        explanation,
        6.15,
        1.79,
        3.3,
        1.08,
        10,
        INK,
        font_name="Arial",
        vertical_anchor=MSO_ANCHOR.TOP,
    )

    divider = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(6.15),
        Inches(3.01),
        Inches(3.3),
        Inches(0.018),
    )
    divider.fill.solid()
    divider.fill.fore_color.rgb = GOLD
    divider.line.fill.background()

    add_text(
        slide,
        "FEATURE EVALUATION",
        6.15,
        3.19,
        3.3,
        0.22,
        8.5,
        BLUE,
        bold=True,
    )
    add_text(
        slide,
        evaluation,
        6.15,
        3.48,
        3.3,
        1.22,
        10,
        INK,
        font_name="Arial",
        vertical_anchor=MSO_ANCHOR.TOP,
    )

    add_footer(slide, f"FEATURE {index:02} / {total:02}")
    return slide


def add_closing_slide(presentation, layout):
    slide = presentation.slides.add_slide(layout)
    clear_slide_shapes(slide)

    add_text(
        slide,
        "CLOSING REMARKS",
        0.45,
        0.3,
        9.1,
        0.35,
        9,
        BLUE,
        bold=True,
    )
    add_text(
        slide,
        "One library. From discovery to accountable access.",
        0.45,
        0.72,
        9.1,
        0.55,
        23,
        NAVY,
        bold=True,
        font_name="Arial Black",
    )
    add_text(
        slide,
        "The feature gallery shows the current local demonstration and the work still needed before launch.",
        0.45,
        1.32,
        9.1,
        0.38,
        10,
        MUTED,
    )

    cards = [
        (
            0.45,
            "CAPABILITIES",
            "Catalog search, registry, digital resources, circulation, and access monitoring are represented in one system.",
        ),
        (
            3.55,
            "OVERALL EVALUATION",
            "Core workflows are demonstrable locally. Research browse needs tagged records, dashboard values are demo data, and production readiness is not yet validated.",
        ),
        (
            6.65,
            "NEXT STEPS",
            "Confirm server/staging ownership, finalize name, logo, and agreement, then complete user acceptance, admin training, and production checks.",
        ),
    ]
    for left, heading, body in cards:
        card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(left),
            Inches(2.02),
            Inches(2.9),
            Inches(1.95),
        )
        card.fill.solid()
        card.fill.fore_color.rgb = RGBColor(245, 248, 252)
        card.line.color.rgb = RGBColor(218, 227, 238)
        add_text(
            slide,
            heading,
            left + 0.17,
            2.23,
            2.56,
            0.32,
            8.5,
            BLUE,
            bold=True,
        )
        add_text(
            slide,
            body,
            left + 0.17,
            2.65,
            2.56,
            1.12,
            9.5,
            INK,
            font_name="Arial",
            vertical_anchor=MSO_ANCHOR.TOP,
        )

    add_text(
        slide,
        "Thank you  |  Questions and discussion",
        0.45,
        4.25,
        9.1,
        0.45,
        16,
        NAVY,
        bold=True,
    )
    add_text(
        slide,
        "Decision requested: confirm the path to a hosted staging environment and stakeholder acceptance.",
        0.45,
        4.68,
        9.1,
        0.25,
        9,
        MUTED,
    )
    add_footer(slide, "CLOSING REMARKS")
    return slide


def build_presentation(template_path, pdf_path, output_path):
    presentation = Presentation(str(template_path))
    if len(presentation.slides) != 12:
        raise ValueError("Expected the supplied 12-slide Air Force template.")

    features = extract_features(pdf_path)
    blank_layout = presentation.slides[2].slide_layout
    cover = presentation.slides[0]

    remove_old_template_markings(presentation)
    set_cover_title(
        next(shape for shape in cover.shapes if shape.name == "Google Shape;231;p39")
    )
    remove_cover_date_and_footer(cover)
    add_cover_footer(cover)
    clear_non_cover_slides(presentation)

    for index, feature in enumerate(features, start=1):
        add_feature_slide(presentation, blank_layout, feature, index, len(features))
    add_closing_slide(presentation, blank_layout)

    presentation.core_properties.title = (
        "TS eLibrary - Feature-by-Feature Screenshot Gallery"
    )
    presentation.core_properties.subject = (
        "Feature explanations, evaluations, local application screenshots, and closing remarks"
    )
    presentation.core_properties.author = COPYRIGHT
    presentation.save(output_path)
    return len(features)


def main():
    repository = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Build the feature screenshot gallery using the supplied Air Force template."
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=Path(r"C:\Users\Dang\Downloads\E-Library.pptx"),
    )
    parser.add_argument(
        "--pdf",
        type=Path,
        default=repository / "TS_eLibrary_Feature_Screenshots_2026-10-30.pdf",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=repository / "TS_eLibrary_Feature_Screenshots.pptx",
    )
    args = parser.parse_args()
    count = build_presentation(args.template, args.pdf, args.output)
    print(
        f"Created {args.output} using the Air Force template "
        f"with one cover and {count} feature slides."
    )


if __name__ == "__main__":
    main()
