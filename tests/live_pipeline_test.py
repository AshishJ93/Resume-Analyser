"""Live API pipeline test. Skips cleanly if XAI_API_KEY is missing."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
from pypdf import PdfReader

load_dotenv(ROOT / ".env")

# Avoid Streamlit script side effects where possible by importing helpers after
# setting a minimal environment.
os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")


RESUME_PDF = Path(
    r"c:\Users\ashis\.cursor\projects\c-Users-ashis-OneDrive-Documents-AI-BootCamp-Resume-Analyser\attachments\3a8f09e9-25ee-4cb4-a377-f22143060b7e\AshishJain_POResume_04022026.pdf"
)

JD_PRODUCT_OWNER = """
Product Owner - Cards & Payments (Bengaluru / Hybrid)

We are hiring a Product Owner for our card issuing and dispute operations platform.

Responsibilities:
- Own the roadmap for dispute lifecycle, chargebacks, and settlement workflows
- Drive ISO 20022 / ISO 8583 compliance initiatives with risk and compliance teams
- Partner with engineering on data quality controls, reconciliation, and migration programmes
- Define acceptance criteria, prioritise backlog, and run Agile ceremonies
- Work with stakeholders across banking ops, customer experience, and technology

Requirements:
- 8+ years in product ownership / business analysis in cards, payments, or fintech
- Hands-on experience with dispute management, PCI DSS awareness, and regulatory delivery
- Strong SQL and analytics literacy; comfortable with API-based integrations
- CSPO or equivalent Agile certification preferred
- Excellent stakeholder management across business and technology

Nice to have: experience migrating large card portfolios, AI/automation in ops, Power BI.
"""

JD_AI_PM = """
AI Product Manager - Enterprise Workflow Automation (Pune / Remote-friendly)

Looking for an AI Product Manager to build agentic workflows for enterprise operations teams.

Must-have:
- 5+ years product experience, at least 1 year shipping AI/ML or GenAI features
- Prompt evaluation mindset, success metrics, and human-in-the-loop design
- Ability to translate ambiguous business problems into MVP scopes
- Experience with BAs/POs or ops stakeholders in regulated industries is a plus

You will define problem statements, run discovery, prioritise AI use cases, and partner with ML engineers.
"""


def main() -> int:
    key = os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")
    if not key:
        print("SKIP live_pipeline_test: XAI_API_KEY not set in local .env")
        print("Cloud launch still OK if Streamlit Secrets has XAI_API_KEY.")
        return 0

    from app import analyze_fit_and_market, rewrite_full_resume, write_cover_letter
    from pdf_templates import build_cover_letter_pdf as cover_pdf
    from pdf_templates import build_resume_pdf as resume_pdf

    reader = PdfReader(str(RESUME_PDF))
    resume_text = "\n".join((p.extract_text() or "") for p in reader.pages)
    assert len(resume_text) > 500

    print("Running fit analysis for Product Owner JD...")
    fit = analyze_fit_and_market(resume_text, "Product Owner - Cards & Payments", JD_PRODUCT_OWNER)
    assert "ats_score" in fit or "score" in fit
    score = int(fit.get("ats_score", fit.get("score", -1)))
    assert 0 <= score <= 100
    assert isinstance(fit.get("missing_keywords"), list)
    assert isinstance(fit.get("india_salary"), dict)
    print("  ATS", score, "keywords", len(fit.get("missing_keywords") or []))

    print("Rewriting full resume...")
    updated = rewrite_full_resume(
        resume_text,
        "Product Owner - Cards & Payments",
        JD_PRODUCT_OWNER,
        fit.get("missing_keywords") or [],
    )
    assert isinstance(updated, dict)
    assert updated.get("full_name") or updated.get("experience")
    roles = len(updated.get("experience") or [])
    assert roles >= 2, f"Expected multiple roles preserved, got {roles}"
    print("  roles preserved/updated:", roles)

    pdf = resume_pdf(updated, "modern")
    assert pdf[:4] == b"%PDF"
    out = ROOT / "tests" / "_sample_updated_resume.pdf"
    out.write_bytes(pdf)
    print("  wrote", out)

    print("Cover letter...")
    letter = write_cover_letter(
        resume_text,
        "Product Owner - Cards & Payments",
        JD_PRODUCT_OWNER,
        updated,
    )
    assert len(letter) > 120
    cpdf = cover_pdf(letter, str(updated.get("full_name") or "Ashish Jain"))
    assert cpdf[:4] == b"%PDF"

    print("Secondary JD smoke (AI PM) fit only...")
    fit2 = analyze_fit_and_market(resume_text, "AI Product Manager", JD_AI_PM)
    score2 = int(fit2.get("ats_score", fit2.get("score", -1)))
    assert 0 <= score2 <= 100
    print("  AI PM ATS", score2)

    print("ALL LIVE PIPELINE TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
