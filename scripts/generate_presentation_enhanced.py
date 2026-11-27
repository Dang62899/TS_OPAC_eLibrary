#!/usr/bin/env python3
"""
Generate an enhanced branded PPTX with multiple slides, speaker notes, and logo.
Usage:
    python scripts/generate_presentation_enhanced.py output.pptx
"""
import sys
import os
from pptx import Presentation
from pptx.util import Inches

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_LOGO = os.environ.get("ELIBRARY_LOGO", "images/TS_Logo.jpg")
LOGO_PATH = os.path.join(BASE_DIR, "static", DEFAULT_LOGO)
ELIBRARY_NAME = os.environ.get("ELIBRARY_NAME", "TS eLibrary")

SLIDES = [
    {
        "title": f"{ELIBRARY_NAME} | 9532 Briefing",
        "subtitle": "Group Commander Presentation",
        "notes": "Introduce the local eLibrary demonstration and its purpose: controlled access to research, SOPs, training resources, and circulation records.",
    },
    {
        "title": "Library and Research Workflows",
        "bullets": [
            "Search by title, author, subject, publication type, year, class, unit, and resource format",
            "Browse research papers by year and class",
            "Upload presentations, curricula, SOPs, and instructional videos",
            "Manage user registry, lifecycle status, and status history",
        ],
        "notes": "Demonstrate a combined search, research browse, registry status change, and document upload.",
    },
    {
        "title": "Access and Accountability",
        "bullets": [
            "Protected downloads and videos require a single-use OTP",
            "PDF previews and downloads include date and configured branding",
            "Document views record user, timestamp, and IP address",
            "Agreement acceptance and account lifecycle changes are recorded",
        ],
        "notes": "Email delivery depends on configured SMTP and Celery; local fallback behavior is intended for demonstration only.",
    },
    {
        "title": "Readiness and Handover",
        "bullets": [
            "Local Django checks and automated tests pass",
            "Production deployment has not been performed",
            "Production host, PostgreSQL, Redis, SMTP, domain, and TLS remain environment tasks",
            "Complete commander review, user acceptance, and administrator training before launch",
        ],
        "notes": "State clearly that this is a presentation-ready local build, not a live deployment. Confirm infrastructure ownership and acceptance before launch.",
    },
]


def add_logo_to_slide(slide):
    if os.path.exists(LOGO_PATH):
        try:
            slide.shapes.add_picture(LOGO_PATH, Inches(6.5), Inches(0.2), width=Inches(1.5))
        except Exception:
            pass


def make_enhanced_presentation(output_path):
    prs = Presentation()
    for i, s in enumerate(SLIDES):
        layout = prs.slide_layouts[1] if i > 0 else prs.slide_layouts[0]
        slide = prs.slides.add_slide(layout)
        title = slide.shapes.title
        title.text = s.get("title", "")
        if i == 0 and "subtitle" in s:
            try:
                subtitle = slide.placeholders[1]
                subtitle.text = s["subtitle"]
            except Exception:
                pass
        if "bullets" in s:
            tf = slide.shapes.placeholders[1].text_frame
            tf.text = s["bullets"][0]
            for b in s["bullets"][1:]:
                p = tf.add_paragraph()
                p.text = b
                p.level = 0
        # speaker notes
        if "notes" in s:
            notes_slide = slide.notes_slide
            notes_slide.notes_text_frame.text = s["notes"]
        add_logo_to_slide(slide)

    # Closing slide
    closing = prs.slide_layouts[5] if len(prs.slide_layouts) > 5 else prs.slide_layouts[1]
    slide = prs.slides.add_slide(closing)
    slide.shapes.title.text = "Questions & Contact"
    if os.path.exists(LOGO_PATH):
        try:
            slide.shapes.add_picture(LOGO_PATH, Inches(0.2), Inches(5.6), width=Inches(1.2))
        except Exception:
            pass

    prs.save(output_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_presentation_enhanced.py output.pptx")
        sys.exit(2)
    out = sys.argv[1]
    make_enhanced_presentation(out)
    print(f"Enhanced presentation written to {out}")
