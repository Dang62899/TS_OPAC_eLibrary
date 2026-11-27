#!/usr/bin/env python3
"""
Generate a simple PPTX presentation using the project's logo.

Usage:
    python scripts/generate_presentation.py output.pptx

This script depends on `python-pptx`.
"""
import sys
import os
from pptx import Presentation
from pptx.util import Inches

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# default logo location under static
DEFAULT_LOGO = os.environ.get("ELIBRARY_LOGO", "images/TS_Logo.jpg")
LOGO_PATH = os.path.join(BASE_DIR, "static", DEFAULT_LOGO)
ELIBRARY_NAME = os.environ.get("ELIBRARY_NAME", "TS eLibrary")

SLIDE_TITLE = f"{ELIBRARY_NAME} | 9532 Group Commander Briefing"
SLIDE_POINTS = [
    "Project overview and scope",
    "New features: Research, OTP checkout, watermarking",
    "Deployment and server requirements",
    "Training and next steps",
]


def make_presentation(output_path):
    prs = Presentation()
    # Title slide
    title_slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(title_slide_layout)
    title = slide.shapes.title
    subtitle = slide.placeholders[1]
    title.text = SLIDE_TITLE
    subtitle.text = "Prepared for Group Commander | Presenter: 9532"

    # Add logo to title slide if available
    if os.path.exists(LOGO_PATH):
        try:
            slide.shapes.add_picture(LOGO_PATH, Inches(6.5), Inches(0.2), width=Inches(1.6))
        except Exception:
            pass

    # Bullet slide
    bullet_layout = prs.slide_layouts[1]
    slide = prs.slides.add_slide(bullet_layout)
    title = slide.shapes.title
    body = slide.shapes.placeholders[1].text_frame
    title.text = "Agenda"
    body.text = SLIDE_POINTS[0]
    for p in SLIDE_POINTS[1:]:
        ptx = body.add_paragraph()
        ptx.text = p
        ptx.level = 0

    # Closing slide
    closing_layout = prs.slide_layouts[5] if len(prs.slide_layouts) > 5 else prs.slide_layouts[1]
    slide = prs.slides.add_slide(closing_layout)
    title = slide.shapes.title
    title.text = "Questions & Next Steps"
    if os.path.exists(LOGO_PATH):
        try:
            slide.shapes.add_picture(LOGO_PATH, Inches(0.2), Inches(5.6), width=Inches(1.2))
        except Exception:
            pass

    prs.save(output_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_presentation.py output.pptx")
        sys.exit(2)
    out = sys.argv[1]
    make_presentation(out)
    print(f"Presentation written to {out}")
