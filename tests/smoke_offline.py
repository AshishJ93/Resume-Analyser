"""Offline smoke tests for launch readiness (no live API required)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pypdf import PdfReader

from app import (
    format_updated_resume_text,
    parse_model_json,
    render_buffering_stage,
    render_receive_checklist,
    render_salary_block,
    score_color,
    score_label,
)
from pdf_templates import TEMPLATES, build_cover_letter_pdf, build_resume_pdf
from ui_theme import STYLE_HTML


RESUME_PDF = Path(
    r"c:\Users\ashis\.cursor\projects\c-Users-ashis-OneDrive-Documents-AI-BootCamp-Resume-Analyser\attachments\3a8f09e9-25ee-4cb4-a377-f22143060b7e\AshishJain_POResume_04022026.pdf"
)

SAMPLE_UPDATED = {
    "full_name": "Ashish Jain",
    "headline": "Product Owner | Payments | Agile",
    "summary": "Product Owner with 11+ years in banking and payments.",
    "contact": {
        "email": "ashish93jain@gmail.com",
        "phone": "+91 7974817571",
        "location": "Bhopal",
        "linkedin": "linkedin.com/in/ashishjain93",
    },
    "skills": ["Product Ownership", "ISO 20022", "Agile", "Data Governance"],
    "experience": [
        {
            "title": "Product Owner",
            "company": "CoreCard",
            "dates": "04/2023 - Present",
            "bullets": [
                "Led migration of 8M+ customer card accounts.",
                "Spearheaded ISO 20022 compliance adoption.",
            ],
        },
        {
            "title": "Senior Business Analyst",
            "company": "CoreCard",
            "dates": "04/2018 - 04/2023",
            "bullets": [
                "Redesigned dispute management processes.",
                "Optimized SQL queries reducing processing time by 30%.",
            ],
        },
    ],
    "projects": [],
    "education": [
        {"school": "IIM Kozhikode", "degree": "EPGP Finance", "dates": "2020-21"}
    ],
    "certifications": ["CSPO"],
    "awards": ["Best Innovation Award"],
    "languages": ["English", "Hindi"],
    "additional_sections": [{"title": "Domain", "items": ["Cards", "Payments"]}],
}


def test_resume_pdf_extract() -> None:
    assert RESUME_PDF.exists(), f"Missing resume: {RESUME_PDF}"
    reader = PdfReader(str(RESUME_PDF))
    text = "\n".join((p.extract_text() or "") for p in reader.pages)
    assert "ASHISH JAIN" in text.upper() or "Ashish" in text
    assert "Product Owner" in text or "PRODUCT OWNER" in text.upper()
    assert len(text.split()) > 200
    print("PASS resume_pdf_extract", len(text.split()), "words")


def test_templates_pdf() -> None:
    for t in TEMPLATES:
        pdf = build_resume_pdf(SAMPLE_UPDATED, t["id"])
        assert pdf[:4] == b"%PDF"
        assert len(pdf) > 1000
    cover = build_cover_letter_pdf(
        "Dear Hiring Manager,\n\nI am applying for the Product Owner role.\n\nRegards,\nAshish",
        "Ashish Jain",
    )
    assert cover[:4] == b"%PDF"
    print("PASS templates_pdf", len(TEMPLATES))


def test_ui_helpers() -> None:
    assert "auroraShift" in STYLE_HTML
    assert "punch-stage" in STYLE_HTML
    html = render_buffering_stage(set(), 1, title="Preparing")
    assert "forge-ring" in html and "punch-stage" in html
    done = render_receive_checklist({1, 2, 3, 4, 5, 6}, title="Delivered")
    assert "check-row done" in done
    salary = render_salary_block(
        {
            "role_level_assumption": "mid-senior",
            "tier1": {"cities": "BLR", "average_lpa": "28-40", "typical_range_lpa": "24-45"},
            "tier2": {"cities": "IND", "average_lpa": "18-28", "typical_range_lpa": "15-32"},
            "tier3": {"cities": "small", "average_lpa": "12-18", "typical_range_lpa": "10-20"},
            "disclaimer": "Indicative",
        },
        "Product Owner",
    )
    assert "Tier-1" in salary and "28-40" in salary
    preview = format_updated_resume_text(SAMPLE_UPDATED)
    assert "Ashish Jain" in preview and "CoreCard" in preview
    assert score_label(82) == "Strong ATS fit"
    assert score_color(40) == "#a84848"
    print("PASS ui_helpers")


def test_json_parse() -> None:
    data = parse_model_json('```json\n{"ats_score": 81, "missing_keywords": ["ISO 20022"]}\n```')
    assert data["ats_score"] == 81
    print("PASS json_parse")


def test_special_chars_pdf() -> None:
    messy = dict(SAMPLE_UPDATED)
    messy["summary"] = "Owned roadmap & delivery for cards <PCI> and payments > scale"
    pdf = build_resume_pdf(messy, "modern")
    assert pdf[:4] == b"%PDF"
    print("PASS special_chars_pdf")


if __name__ == "__main__":
    test_resume_pdf_extract()
    test_templates_pdf()
    test_ui_helpers()
    test_json_parse()
    test_special_chars_pdf()
    print("ALL OFFLINE SMOKE TESTS PASSED")
