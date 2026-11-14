"""Professional resume PDF templates and cover-letter PDF export."""

from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


TEMPLATES = [
    {
        "id": "classic",
        "name": "Classic Serif",
        "blurb": "Traditional single-column layout with refined hierarchy.",
    },
    {
        "id": "modern",
        "name": "Modern Teal",
        "blurb": "Clean sans layout with a soft accent rule.",
    },
    {
        "id": "minimal",
        "name": "Minimal Light",
        "blurb": "Airy spacing and quiet typography.",
    },
    {
        "id": "executive",
        "name": "Executive",
        "blurb": "Bold header band for senior roles.",
    },
    {
        "id": "compact",
        "name": "Compact ATS",
        "blurb": "Dense, ATS-friendly single column.",
    },
]


def _c(hex_code: str) -> Color:
    return HexColor(hex_code)


def _safe(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text or fallback


def _join_contact(contact: dict | None) -> str:
    contact = contact or {}
    parts = [
        _safe(contact.get("email")),
        _safe(contact.get("phone")),
        _safe(contact.get("location")),
        _safe(contact.get("linkedin")),
    ]
    return "  ·  ".join(p for p in parts if p)


def _bullets(items: list | None, style: ParagraphStyle) -> list:
    flowables = []
    for item in items or []:
        text = _safe(item)
        if text:
            flowables.append(
                ListItem(Paragraph(text.replace("\n", "<br/>"), style), leftIndent=12)
            )
    if not flowables:
        return []
    return [
        ListFlowable(
            flowables,
            bulletType="bullet",
            start="•",
            leftIndent=8,
            bulletFontSize=8,
            spaceBefore=2,
            spaceAfter=4,
        )
    ]


def _section_title(text: str, style: ParagraphStyle) -> list:
    return [Spacer(1, 8), Paragraph(text.upper(), style), Spacer(1, 3)]


def _experience_blocks(experience: list | None, role_style, meta_style, body_style) -> list:
    blocks = []
    for job in experience or []:
        title = _safe(job.get("title"), "Role")
        company = _safe(job.get("company"))
        dates = _safe(job.get("dates"))
        header = title if not company else f"{title} — {company}"
        blocks.append(Paragraph(header, role_style))
        if dates:
            blocks.append(Paragraph(dates, meta_style))
        blocks.extend(_bullets(job.get("bullets"), body_style))
        blocks.append(Spacer(1, 4))
    return blocks


def _education_blocks(education: list | None, role_style, meta_style) -> list:
    blocks = []
    for edu in education or []:
        school = _safe(edu.get("school"), "Education")
        degree = _safe(edu.get("degree"))
        dates = _safe(edu.get("dates"))
        line = school if not degree else f"{degree} — {school}"
        blocks.append(Paragraph(line, role_style))
        if dates:
            blocks.append(Paragraph(dates, meta_style))
        blocks.append(Spacer(1, 3))
    return blocks


def _skills_line(skills: list | None) -> str:
    cleaned = [_safe(s) for s in (skills or []) if _safe(s)]
    return " · ".join(cleaned)


def _theme(template_id: str) -> dict:
    themes = {
        "classic": {
            "accent": "#3f4a56",
            "name_size": 20,
            "header_band": False,
            "rule": True,
            "margin": 0.7 * inch,
        },
        "modern": {
            "accent": "#2f6f6a",
            "name_size": 22,
            "header_band": False,
            "rule": True,
            "margin": 0.65 * inch,
        },
        "minimal": {
            "accent": "#6b7280",
            "name_size": 18,
            "header_band": False,
            "rule": False,
            "margin": 0.85 * inch,
        },
        "executive": {
            "accent": "#1f2a37",
            "name_size": 22,
            "header_band": True,
            "rule": False,
            "margin": 0.6 * inch,
        },
        "compact": {
            "accent": "#334155",
            "name_size": 16,
            "header_band": False,
            "rule": True,
            "margin": 0.5 * inch,
        },
    }
    return themes.get(template_id, themes["modern"])


def build_resume_pdf(resume: dict, template_id: str = "modern") -> bytes:
    theme = _theme(template_id)
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=theme["margin"],
        rightMargin=theme["margin"],
        topMargin=theme["margin"] - 0.1 * inch,
        bottomMargin=theme["margin"],
    )

    styles = getSampleStyleSheet()
    accent = _c(theme["accent"])
    ink = _c("#1a1d23")
    muted = _c("#5c6570")

    name_style = ParagraphStyle(
        "Name",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=theme["name_size"],
        textColor=white if theme["header_band"] else ink,
        spaceAfter=2,
        leading=theme["name_size"] + 4,
    )
    headline_style = ParagraphStyle(
        "Headline",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=white if theme["header_band"] else accent,
        spaceAfter=2,
    )
    contact_style = ParagraphStyle(
        "Contact",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        textColor=white if theme["header_band"] else muted,
        spaceAfter=6,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        textColor=accent,
        spaceBefore=4,
        spaceAfter=2,
        tracking=0.6,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=ink,
        leading=12,
        alignment=TA_LEFT,
    )
    role_style = ParagraphStyle(
        "Role",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        textColor=ink,
        spaceBefore=2,
    )
    meta_style = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        textColor=muted,
        spaceAfter=1,
    )

    story: list = []
    name = _safe(resume.get("full_name"), "Your Name")
    headline = _safe(resume.get("headline"))
    contact = _join_contact(resume.get("contact"))

    if theme["header_band"]:
        header_data = [
            [
                Paragraph(name, name_style),
            ],
            [Paragraph(headline, headline_style)] if headline else [],
            [Paragraph(contact, contact_style)] if contact else [],
        ]
        header_data = [row for row in header_data if row]
        table = Table([[row[0]] for row in header_data], colWidths=[doc.width])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), accent),
                    ("LEFTPADDING", (0, 0), (-1, -1), 14),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                    ("TOPPADDING", (0, 0), (-1, 0), 14),
                    ("BOTTOMPADDING", (0, -1), (-1, -1), 12),
                    ("TOPPADDING", (0, 1), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -2), 2),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 12))
    else:
        story.append(Paragraph(name, name_style))
        if headline:
            story.append(Paragraph(headline, headline_style))
        if contact:
            story.append(Paragraph(contact, contact_style))
        if theme["rule"]:
            story.append(
                HRFlowable(
                    width="100%",
                    thickness=1,
                    color=accent,
                    spaceBefore=2,
                    spaceAfter=8,
                )
            )

    summary = _safe(resume.get("summary"))
    if summary:
        story.extend(_section_title("Summary", section_style))
        story.append(Paragraph(summary, body_style))

    skills = _skills_line(resume.get("skills"))
    if skills:
        story.extend(_section_title("Skills", section_style))
        story.append(Paragraph(skills, body_style))

    if resume.get("experience"):
        story.extend(_section_title("Experience", section_style))
        story.extend(
            _experience_blocks(resume.get("experience"), role_style, meta_style, body_style)
        )

    if resume.get("projects"):
        story.extend(_section_title("Projects", section_style))
        for project in resume.get("projects") or []:
            title = _safe(project.get("name"), "Project")
            detail = _safe(project.get("description"))
            story.append(Paragraph(title, role_style))
            if detail:
                story.append(Paragraph(detail, body_style))
            story.extend(_bullets(project.get("bullets"), body_style))

    if resume.get("education"):
        story.extend(_section_title("Education", section_style))
        story.extend(_education_blocks(resume.get("education"), role_style, meta_style))

    doc.build(story)
    return buffer.getvalue()


def build_cover_letter_pdf(cover_letter: str, candidate_name: str = "") -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        topMargin=0.9 * inch,
        bottomMargin=0.9 * inch,
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "CLTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=_c("#1a1d23"),
        spaceAfter=12,
    )
    body = ParagraphStyle(
        "CLBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=15,
        textColor=_c("#1a1d23"),
        alignment=TA_JUSTIFY,
        spaceAfter=10,
    )

    story = []
    heading = f"Cover Letter — {_safe(candidate_name, 'Applicant')}"
    story.append(Paragraph(heading, title))
    story.append(
        HRFlowable(width="100%", thickness=1, color=_c("#2f6f6a"), spaceAfter=14)
    )
    for para in (cover_letter or "").split("\n"):
        text = para.strip()
        if text:
            story.append(Paragraph(text.replace("  ", " "), body))
        else:
            story.append(Spacer(1, 6))
    doc.build(story)
    return buffer.getvalue()
