import argparse
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR
from pptx.util import Inches, Pt
from PIL import Image


NAVY = RGBColor(0, 32, 96)
BLUE = RGBColor(25, 82, 155)
INK = RGBColor(31, 41, 55)
MUTED = RGBColor(78, 91, 108)
PANEL = RGBColor(245, 248, 252)
PANEL_BORDER = RGBColor(216, 226, 238)

FEATURE_DETAILS = {
    3: (
        "Borrowers register; staff manage identity, unit, class, and student/alumni status.",
        "The local workflows are demonstrable. Verify eligibility against the official roster and train administrators on secure account and password management.",
    ),
    4: (
        "Registry and circulation tools connect borrower status with checkouts, returns, renewals, holds, requests, and item transit.",
        "Core staff tasks are represented locally. Validate loan rules, status transitions, and transaction history with staff before rollout.",
    ),
    5: (
        "Staff upload documents, presentations, videos, or links and configure metadata and download controls.",
        "Multiple resource types are demonstrated. Validate protected downloads, OTP, watermark output, permissions, and storage in staging.",
    ),
    6: (
        "Search across catalog fields, then narrow results by format, subject, author, year, class, unit, and access.",
        "Discovery is feature-rich; reliable results depend on complete catalog metadata and representative acceptance tests.",
    ),
    7: (
        "Record resource views, previews, video plays, and downloads for staff review and CSV reporting.",
        "Improves accountability. Define access permissions, privacy notices, and log retention before production use.",
    ),
    8: (
        "Browse research papers by year and class as an alternative to keyword search.",
        "The filter screen is present, but the local demo has no tagged papers. Add sample records and verify results before presenting this workflow as populated.",
    ),
}


SLIDE_CONTENT = {
    2: {
        "title": "PROJECT PROGRESS",
        "body": [
            "Accounts and registry",
            "Circulation and staff workflows",
            "Catalog search and discovery",
            "Digital resources and controlled downloads",
            "Monitoring, security, and local validation",
            "Staging readiness and remaining work",
            "",
            "",
        ],
        "body_index": 1,
        "title_index": 0,
    },
    3: {
        "title": "Current Progress",
        "body": [
            "Account creation is available to borrowers.",
            "The local registration screen includes identity and serial-number fields.",
            "Staff registry tools support role, unit, class, and lifecycle management.",
            "Local demonstration is available; production staging is not yet verified.",
        ],
        "body_index": 0,
        "title_index": 1,
    },
    4: {
        "title": "Accounts and Circulation",
        "body": [
            "Borrower and staff workflows:",
            "Registry tracks student-to-alumni status and history.",
            "Staff can create accounts, edit records, and reset passwords.",
            "Checkout, returns, renewals, holds, requests, and transit.",
            "Loan limits and lifecycle eligibility are enforced.",
        ],
        "body_index": 0,
        "title_index": 1,
    },
    5: {
        "title": "Digital Resources",
        "body": [
            "Content and access controls:",
            "PDF, DOCX, PPTX, and MP4 uploads use catalog metadata.",
            "Videos can be uploaded or linked.",
            "Password is required for downloads, not ordinary viewing.",
            "Download copies receive date and brand watermarks.",
        ],
        "body_index": 0,
        "title_index": 1,
    },
    6: {
        "title": "Catalog Search and Discovery",
        "body": [
            "Find resources with fewer steps:",
            "Search all fields or title, author, subject, call number, ISBN, and description.",
            "Boolean and exact-phrase search.",
            "Filter by format, author, subject, year, class, unit, and access.",
            "Research browse supports year/class filters.",
        ],
        "body_index": 0,
        "title_index": 1,
    },
    7: {
        "title": "Resource Access Monitoring",
        "body": [
            "Logs views, previews, video plays, and downloads.",
            "Records account/anonymous access, action, file type, time, IP, and resource.",
            "Staff can filter history and export CSV reports.",
        ],
        "body_index": 0,
        "title_index": 1,
    },
    8: {
        "title": "Research Browse",
        "body": [
            "Browse publications by year and class.",
            "This screen is from the live local application.",
            "The local demo has no publications tagged for research browsing.",
            "Add representative tagged records before presenting results.",
        ],
        "body_index": 0,
        "title_index": 1,
    },
    9: {
        "title": "Borrower Experience",
        "body": [
            "Borrower journey",
            "A straightforward path from discovery to access:",
            "1. Sign in and accept the user agreement.",
            "2. Search the catalog or choose a specific search field.",
            "3. Filter by format, author, subject, year, class, unit, or access.",
            "4. Review bibliographic details, copy availability, and location.",
            "5. Preview PDFs or play instructional videos when available.",
            "Downloads and account",
            "6. Enter the resource password when downloading a protected file.",
            "7. Complete OTP verification when the resource requires it.",
            "8. View current loans, due dates, holds, and requests in My Account.",
            "Borrower safeguards",
            "Renewals and requests follow lifecycle, eligibility, and loan-limit rules.",
            "Viewing or playback does not prompt for the download password.",
            "Graduated or otherwise ineligible accounts cannot use student-only actions.",
        ],
        "body_index": 0,
        "title_index": 1,
    },
    10: {
        "title": "Staff and Admin Workflow",
        "body": [
            "Operational oversight",
            "Manage the registry by role, unit, class, and lifecycle status.",
            "Create borrower accounts, update records, and reset passwords.",
            "Upload manuals, SOPs, presentations, curricula, briefings, and videos.",
            "Maintain resource metadata, download settings, and unit/class tags.",
            "Registry and accounts",
            "Process checkout, return, renewals, holds, requests, and item transit.",
            "Review overdue activity and circulation statistics.",
            "Circulation",
            "Monitor resource views, plays, previews, and downloads.",
            "Filter access history and export reports for follow-up.",
            "Resource oversight",
            "Role-specific permissions separate borrower, staff, and admin actions.",
        ],
        "body_index": 0,
        "title_index": 1,
    },
    11: {
        "title": "Readiness and Next Steps",
        "body": [
            "Local validation status",
            "Automated tests and Django system checks pass in the local environment.",
            "Search, accounts, circulation, access controls, and demo media are testable.",
            "No production deployment has been performed.",
            "Staging requirements",
            "Validate PostgreSQL, Redis/Celery, SMTP, HTTPS/domain, and private media.",
            "Run backup/restore, monitoring, and 1,000-record search performance tests.",
            "Recheck credentials and remove old sensitive history artifacts before sharing.",
            "Owner decisions",
            "Finalize approved agreement wording and confirm branding.",
            "Next gate: staging evidence and stakeholder acceptance.",
        ],
        "body_index": 0,
        "title_index": 1,
    },
}

BORROWER_JOURNEY = [
    "Sign in and accept the user agreement.",
    "Search and filter by resource details.",
    "Review availability; preview PDFs or play videos.",
    "Enter the download password and OTP when required.",
    "Track loans, holds, and requests in My Account.",
]

STAFF_WORKFLOW = [
    "Registry: create accounts, update class/unit/status, and reset credentials.",
    "Collections: upload SOPs, curricula, presentations, briefings, and videos.",
    "Circulation: check out/in, renew, manage holds/requests, and track transit.",
    "Oversight: review overdue items, reports, and resource-access history.",
]

SCREENSHOTS = {
    3: ("live_registration.png", "Live screen: account registration", "Google Shape;258;p41"),
    4: ("avp_manage_users_redacted.png", "Live screen: user registry (identifying details obscured)", "Google Shape;269;p42"),
    5: ("avp_borrower_resources_redacted.png", "Live screen: preview/playback and download-password controls", None),
    6: ("avp_catalog_filters.png", "Live screen: catalog search with filters expanded", "Google Shape;291;p44"),
    7: ("avp_resource_monitor_redacted.png", "Live screen: access monitor (user and IP values obscured)", "Google Shape;302;p45"),
    8: ("live_research.png", "Live screen: research year/class filter; local sample has no tagged papers", "Google Shape;314;p46"),
}


def set_paragraph_text(paragraph, text):
    runs = paragraph.runs
    if not runs:
        paragraph.add_run().text = text
        return
    runs[0].text = text
    for run in runs[1:]:
        run.text = ""


def replace_paragraphs(shape, lines):
    paragraphs = shape.text_frame.paragraphs
    if len(lines) > len(paragraphs):
        raise ValueError(
            f"{shape.name} has {len(paragraphs)} paragraphs, but {len(lines)} were provided"
        )
    for index, paragraph in enumerate(paragraphs):
        set_paragraph_text(paragraph, lines[index] if index < len(lines) else "")


def add_textbox(slide, text, left, top, width, height, size, color, bold=False):
    shape = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    frame = shape.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = Inches(0.01)
    frame.margin_right = Inches(0.01)
    frame.margin_top = Inches(0.01)
    frame.margin_bottom = Inches(0.01)
    frame.vertical_anchor = MSO_ANCHOR.TOP
    paragraph = frame.paragraphs[0]
    paragraph.text = text
    paragraph.font.name = "Arial"
    paragraph.font.size = Pt(size)
    paragraph.font.bold = bold
    paragraph.font.color.rgb = color
    return shape


def remove_shape_element(shape):
    shape._element.getparent().remove(shape._element)


def add_panel(slide, left, top, width, height):
    panel = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(left),
        Inches(top),
        Inches(width),
        Inches(height),
    )
    panel.fill.solid()
    panel.fill.fore_color.rgb = PANEL
    panel.line.color.rgb = PANEL_BORDER
    return panel


def add_section(slide, title, body, left, top, width, body_height, body_size=14):
    add_textbox(slide, title, left, top, width, 0.22, 9.5, BLUE, bold=True)
    add_textbox(
        slide,
        body,
        left,
        top + 0.28,
        width,
        body_height,
        body_size,
        INK,
    )


def replace_feature_body(slide, body_shape, explanation, evaluation):
    remove_shape_element(body_shape)
    add_panel(slide, 0.35, 1.2, 4.52, 3.42)
    add_section(
        slide,
        "FEATURE EXPLANATION",
        explanation,
        0.58,
        1.48,
        4.06,
        1.02,
        body_size=14,
    )
    divider = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0.58),
        Inches(2.77),
        Inches(4.06),
        Inches(0.018),
    )
    divider.fill.solid()
    divider.fill.fore_color.rgb = RGBColor(224, 169, 30)
    divider.line.fill.background()
    add_section(
        slide,
        "FEATURE EVALUATION",
        evaluation,
        0.58,
        2.98,
        4.06,
        1.32,
        body_size=13.5,
    )


def add_workflow_slide_content(slide, body_shape, left_title, left_body, right_title, right_sections):
    remove_shape_element(body_shape)
    left, top, width, height = 0.4, 1.32, 4.52, 3.38
    right = 5.08
    add_panel(slide, left, top, width, height)
    add_panel(slide, right, top, width, height)
    add_section(
        slide,
        left_title,
        left_body,
        left + 0.24,
        top + 0.28,
        width - 0.48,
        height - 0.65,
        body_size=13,
    )

    section_top = top + 0.28
    for title, body, body_height in right_sections:
        add_section(
            slide,
            title,
            body,
            right + 0.24,
            section_top,
            width - 0.48,
            body_height,
            body_size=13,
        )
        section_top += body_height + 0.55


def add_readiness_content(slide, body_shape):
    remove_shape_element(body_shape)
    top, height = 1.32, 3.38
    left, right, width = 0.4, 5.08, 4.52
    add_panel(slide, left, top, width, height)
    add_panel(slide, right, top, width, height)
    add_section(
        slide,
        "VALIDATED LOCALLY",
        "Automated tests and Django checks run locally. Search, accounts, circulation, access controls, and demo media can be exercised. No production deployment has been performed.",
        left + 0.24,
        top + 0.28,
        width - 0.48,
        1.15,
        body_size=13,
    )
    add_section(
        slide,
        "REMAINING BEFORE LAUNCH",
        "Validate PostgreSQL, Redis/Celery, SMTP, HTTPS/domain, private media, backup/restore, monitoring, and search performance. Finalize agreement and branding; complete admin training and stakeholder acceptance.",
        left + 0.24,
        top + 1.83,
        width - 0.48,
        1.25,
        body_size=12.5,
    )
    add_section(
        slide,
        "READINESS EVALUATION",
        "Demonstration-ready locally; not production-ready. The next decision is to confirm server/staging ownership, validate the hosted environment, and close acceptance findings before operational approval.",
        right + 0.24,
        top + 0.28,
        width - 0.48,
        1.8,
        body_size=14,
    )
    add_textbox(
        slide,
        "NEXT GATE  |  Staging evidence and stakeholder acceptance",
        right + 0.24,
        top + 2.55,
        width - 0.48,
        0.48,
        10,
        BLUE,
        bold=True,
    )


def replace_title_runs(shape, title, subtitle):
    paragraph = shape.text_frame.paragraphs[0]
    if len(paragraph.runs) < 2:
        raise ValueError("The title slide no longer has separate title/subtitle runs")
    paragraph.runs[0].text = title + " "
    paragraph.runs[1].text = subtitle
    for run in paragraph.runs[2:]:
        run.text = ""


def remove_shape(slide, shape_name):
    for shape in slide.shapes:
        if shape.name == shape_name:
            shape._element.getparent().remove(shape._element)
            return


def add_screenshot(slide, image_path, caption, left, top, max_width, max_height):
    if not image_path.is_file():
        raise FileNotFoundError(f"Required live project screenshot not found: {image_path}")
    with Image.open(image_path) as image:
        image_width, image_height = image.size
    scale = min(max_width / image_width, max_height / image_height)
    width = Inches(image_width * scale)
    height = Inches(image_height * scale)
    left_emu = Inches(left)
    top_emu = Inches(top + (max_height - image_height * scale) / 2)
    slide.shapes.add_picture(str(image_path), left_emu, top_emu, width=width, height=height)

    caption_shape = slide.shapes.add_textbox(
        Inches(left), Inches(top + max_height + 0.04), Inches(max_width), Inches(0.25)
    )
    paragraph = caption_shape.text_frame.paragraphs[0]
    paragraph.text = caption
    paragraph.font.size = Pt(9)
    paragraph.font.italic = True
    paragraph.font.color.rgb = RGBColor(90, 100, 110)
    caption_shape.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE


def remove_legacy_template_text(presentation):
    obsolete_markers = (
        "C O N F I D E N T I A L",
        "Flight Plan Vision:",
        "FOR OFFICIAL USE ONLY",
        "Presented to: WC, 950CEWW",
        "Office Symbol",
        "CAPABLE    CREDIBLE   SUSTAINABLE",
    )
    masters_and_layouts = []
    for master in presentation.slide_masters:
        masters_and_layouts.append(master)
        masters_and_layouts.extend(master.slide_layouts)
    for container in masters_and_layouts:
        for shape in list(container.shapes):
            if not getattr(shape, "has_text_frame", False):
                continue
            if any(marker in shape.text for marker in obsolete_markers):
                shape._element.getparent().remove(shape._element)


def update_footer(slide, presentation_date=None):
    for shape in slide.shapes:
        if not getattr(shape, "has_text_frame", False):
            continue
        if not shape.text.startswith("Presented to:"):
            continue
        paragraphs = shape.text_frame.paragraphs
        if len(paragraphs) >= 3:
            set_paragraph_text(paragraphs[0], "Presented to: 9532TS")
            set_paragraph_text(paragraphs[1], "Presented by: 9533RD RDS")
            set_paragraph_text(
                paragraphs[2],
                f"Date Presented: {presentation_date}" if presentation_date else "",
            )


def build_presentation(template_path, output_path, presentation_date):
    presentation = Presentation(template_path)
    if len(presentation.slides) != 12:
        raise ValueError("Expected the supplied 12-slide E-Library template")
    remove_legacy_template_text(presentation)

    cover = presentation.slides[0]
    replace_title_runs(
        next(shape for shape in cover.shapes if shape.name == "Google Shape;231;p39"),
        "TS eLibrary",
        "Feature Progress AVP",
    )
    date_shape = next(
        shape for shape in cover.shapes if shape.name == "Google Shape;235;p39"
    )
    set_paragraph_text(
        date_shape.text_frame.paragraphs[0],
        " " + presentation_date if presentation_date else "",
    )

    for slide_number, content in SLIDE_CONTENT.items():
        slide = presentation.slides[slide_number - 1]
        title = slide.shapes[content["title_index"]]
        set_paragraph_text(title.text_frame.paragraphs[0], content["title"])
        if slide_number == 2:
            body = slide.shapes[content["body_index"]]
            replace_paragraphs(body, content["body"])
            body.left = Inches(0.8)
            body.top = Inches(1.82)
            body.width = Inches(6.55)
            body.height = Inches(3.0)
            for paragraph in body.text_frame.paragraphs:
                paragraph.font.size = Pt(20)
                for run in paragraph.runs:
                    run.font.size = Pt(20)
        else:
            body = slide.shapes[content["body_index"]]
            if slide_number in FEATURE_DETAILS:
                explanation, evaluation = FEATURE_DETAILS[slide_number]
                replace_feature_body(slide, body, explanation, evaluation)
            elif slide_number == 9:
                add_workflow_slide_content(
                    slide,
                    body,
                    "BORROWER JOURNEY",
                    "\n".join(
                        f"{index}. {step}"
                        for index, step in enumerate(BORROWER_JOURNEY, start=1)
                    ),
                    "BORROWER FEATURE EVALUATION",
                    [
                        (
                            "WHAT IT ENABLES",
                            "Connects discovery, protected access, and account self-service in one borrower path.",
                            0.72,
                        ),
                        (
                            "ASSESSMENT",
                            "The workflow is represented locally. Validate permissions, password/OTP handling, account eligibility, and notifications with borrower acceptance testing.",
                            1.1,
                        ),
                    ],
                )
            elif slide_number == 10:
                add_workflow_slide_content(
                    slide,
                    body,
                    "STAFF OPERATIONS",
                    "\n".join(STAFF_WORKFLOW),
                    "STAFF FEATURE EVALUATION",
                    [
                        (
                            "WHAT IT ENABLES",
                            "Brings registry, collection, circulation, and monitoring tasks into a staff workflow.",
                            0.78,
                        ),
                        (
                            "ASSESSMENT",
                            "Verify role boundaries, roster accuracy, secure password-reset handoff, and report totals before production. Train administrators on these controls.",
                            1.06,
                        ),
                    ],
                )
            elif slide_number == 11:
                add_readiness_content(slide, body)
        update_footer(slide, presentation_date)

    screenshot_dir = Path(__file__).resolve().parents[1] / "presentation_images"
    for slide_number, (filename, caption, old_shape_name) in SCREENSHOTS.items():
        slide = presentation.slides[slide_number - 1]
        if old_shape_name:
            remove_shape(slide, old_shape_name)
        if slide_number == 7:
            remove_shape(slide, "Google Shape;303;p45")
        add_screenshot(
            slide,
            screenshot_dir / filename,
            caption,
            left=5.18,
            top=1.15,
            max_width=4.55,
            max_height=3.4,
        )

    # This template graphic displays percentages that are not project metrics.
    remove_shape(presentation.slides[4], "Google Shape;280;p43")

    for slide in presentation.slides:
        for shape in list(slide.shapes):
            if not getattr(shape, "has_text_frame", False):
                continue
            if "\u2039#\u203a" in shape.text:
                shape._element.getparent().remove(shape._element)

    update_footer(cover, presentation_date)

    closing = presentation.slides[11]
    closing_text = next(
        shape
        for shape in closing.shapes
        if getattr(shape, "has_text_frame", False) and shape.text.strip()
    )
    set_paragraph_text(
        closing_text.text_frame.paragraphs[0],
        "TS eLibrary | Thank you",
    )
    add_textbox(
        closing,
        "CLOSING REMARKS",
        0.62,
        3.72,
        4.85,
        0.22,
        10,
        BLUE,
        bold=True,
    )
    add_textbox(
        closing,
        "TS eLibrary brings discovery, digital learning, circulation, and resource oversight into one experience.\nNext: complete server staging, user acceptance, and administrator handover.\nThank you. Questions and discussion.",
        0.62,
        4.02,
        4.85,
        1.22,
        11.5,
        NAVY,
    )

    presentation.core_properties.title = (
        "TS eLibrary - Feature Progress AVP"
    )
    presentation.core_properties.subject = (
        "Current implementation progress and pre-deployment readiness"
    )
    presentation.core_properties.author = "TS eLibrary Project Team"
    presentation.save(output_path)


def main():
    parser = argparse.ArgumentParser(
        description="Build a TS eLibrary progress AVP using the supplied PowerPoint template."
    )
    parser.add_argument("--template", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--date",
        default=None,
        help="Optional presentation date shown on slides; omitted by default",
    )
    args = parser.parse_args()
    if not args.template.is_file():
        parser.error(f"Template not found: {args.template}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    build_presentation(args.template, args.output, args.date)
    print(f"Created {args.output}")


if __name__ == "__main__":
    main()
