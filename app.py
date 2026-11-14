import base64
import html
import json
import os
import re
from io import BytesIO

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader

from pdf_templates import TEMPLATES, build_cover_letter_pdf, build_resume_pdf
from ui_theme import inject_styles as inject_theme_styles

load_dotenv()

try:
    from paste_image import paste_image as _paste_image_component

    def paste_image(label: str = "Paste a screenshot", key: str | None = None):
        try:
            return _paste_image_component(label=label, key=key)
        except Exception:
            return None

except Exception:

    def paste_image(label: str = "Paste a screenshot", key: str | None = None):
        return None


FIT_SCHEMA_HINT = {
    "ats_score": 0,
    "verdict": "one sentence",
    "strengths": ["...", "...", "..."],
    "improvements": ["...", "...", "..."],
    "missing_keywords": ["keyword1", "keyword2"],
    "india_salary": {
        "currency": "INR LPA",
        "role_level_assumption": "e.g. mid-level 4-7 YOE",
        "tier1": {
            "cities": "Bengaluru, Mumbai, Delhi-NCR, Hyderabad, Pune, Chennai",
            "average_lpa": "18-28",
            "typical_range_lpa": "15-35",
        },
        "tier2": {
            "cities": "Ahmedabad, Jaipur, Kochi, Chandigarh, Indore, Coimbatore",
            "average_lpa": "12-20",
            "typical_range_lpa": "10-24",
        },
        "tier3": {
            "cities": "smaller metros / emerging cities",
            "average_lpa": "8-14",
            "typical_range_lpa": "6-16",
        },
        "disclaimer": "Indicative India market ranges; actual offers vary by company, skills, and negotiation.",
    },
}

RESUME_SCHEMA_HINT = {
    "updated_resume": {
        "full_name": "Full Name",
        "headline": "Target role headline",
        "summary": "3-5 sentence summary weaving missing keywords naturally",
        "contact": {
            "email": "",
            "phone": "",
            "location": "",
            "linkedin": "",
        },
        "skills": ["include original skills plus missing keywords where truthful"],
        "experience": [
            {
                "title": "Job title",
                "company": "Company",
                "dates": "YYYY – YYYY",
                "bullets": [
                    "Keep every original role. Improve wording; do not drop jobs or bullets casually.",
                    "Weave missing keywords only where truthful.",
                ],
            }
        ],
        "projects": [
            {
                "name": "Project",
                "description": "keep original projects",
                "bullets": ["outcome"],
            }
        ],
        "education": [
            {
                "school": "University",
                "degree": "Degree",
                "dates": "YYYY – YYYY",
            }
        ],
        "certifications": ["keep all"],
        "awards": ["keep all"],
        "languages": ["keep all"],
        "additional_sections": [
            {"title": "Any other original section", "items": ["keep content"]}
        ],
    }
}

COVER_SCHEMA_HINT = {
    "cover_letter": "Full cover letter text with paragraphs separated by newlines",
}


def render_html(content: str) -> None:
    """Inject HTML safely on Streamlit Cloud (st.html avoids CSS-as-text bugs)."""
    if hasattr(st, "html"):
        st.html(content)
    else:
        st.markdown(content, unsafe_allow_html=True)


def get_xai_api_key() -> str | None:
    key = os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")
    if key:
        return key
    try:
        return st.secrets.get("XAI_API_KEY") or st.secrets.get("GROK_API_KEY")
    except Exception:
        return None


def get_client() -> OpenAI:
    api_key = get_xai_api_key()
    if not api_key:
        raise ValueError(
            "XAI_API_KEY is not set. Add it to your local .env or Streamlit Secrets."
        )
    return OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")


def extract_pdf_text(uploaded_file) -> str:
    reader = PdfReader(BytesIO(uploaded_file.getvalue()))
    parts = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            parts.append(text)
    return "\n".join(parts).strip()


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text or ""))


def parse_model_json(raw: str) -> dict:
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


def data_url_to_bytes(data_url: str) -> tuple[bytes, str]:
    match = re.match(r"data:(image/[^;]+);base64,(.+)", data_url, re.DOTALL)
    if not match:
        raise ValueError("Invalid image data.")
    mime, b64 = match.group(1), match.group(2)
    return base64.b64decode(b64), mime


def extract_text_from_image_bytes(image_bytes: bytes, mime: str = "image/png") -> str:
    client = get_client()
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    model = os.getenv("XAI_VISION_MODEL", "grok-2-vision-1212")
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Extract ALL readable text from this screenshot or document image. "
                            "Preserve reading order. Return plain text only — no markdown, "
                            "no commentary, no labels like 'extracted text'."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{b64}"},
                    },
                ],
            }
        ],
    )
    return (response.choices[0].message.content or "").strip()


def _chat_json(system_prompt: str, user_prompt: str, temperature: float = 0.3) -> dict:
    client = get_client()
    response = client.chat.completions.create(
        model=os.getenv("XAI_MODEL", "grok-4.3"),
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    content = response.choices[0].message.content or "{}"
    return parse_model_json(content)


def analyze_fit_and_market(
    resume_text: str, target_role: str, job_description: str
) -> dict:
    system_prompt = (
        "You are an expert ATS strategist and India compensation researcher. "
        "Return ONLY valid JSON. No markdown fences. "
        f"Use exactly this shape: {json.dumps(FIT_SCHEMA_HINT)}. "
        "ats_score is 0-100. verdict is one sentence. "
        "strengths and improvements: exactly 3 items each. "
        "missing_keywords: important role/JD terms missing or weak in the resume. "
        "india_salary: realistic current India CTC bands in LPA for this target role, "
        "split by Tier-1 / Tier-2 / Tier-3 cities. Infer seniority from the resume. "
        "Be practical and market-aware; ranges may be strings like '18-28'."
    )
    user_prompt = (
        f"Target role:\n{target_role.strip()}\n\n"
        f"Job description:\n{(job_description or '').strip() or '(not provided)'}\n\n"
        f"Resume:\n{resume_text.strip()}"
    )
    data = _chat_json(system_prompt, user_prompt, temperature=0.25)
    if not isinstance(data, dict):
        data = {}
    if "ats_score" not in data and "score" in data:
        data["ats_score"] = data["score"]
    try:
        data["ats_score"] = max(0, min(100, int(data.get("ats_score", 0))))
    except (TypeError, ValueError):
        data["ats_score"] = 0
    if not isinstance(data.get("missing_keywords"), list):
        data["missing_keywords"] = []
    if not isinstance(data.get("strengths"), list):
        data["strengths"] = []
    if not isinstance(data.get("improvements"), list):
        data["improvements"] = []
    if not isinstance(data.get("india_salary"), dict):
        data["india_salary"] = {}
    data.setdefault("verdict", "Analysis complete.")
    return data


def rewrite_full_resume(
    resume_text: str,
    target_role: str,
    job_description: str,
    missing_keywords: list,
) -> dict:
    system_prompt = (
        "You are an expert resume writer. Return ONLY valid JSON. No markdown fences. "
        f"Use exactly this shape: {json.dumps(RESUME_SCHEMA_HINT)}. "
        "CRITICAL RULES — DO NOT TRUNCATE:\n"
        "1) Preserve ALL original experience roles, projects, education entries, "
        "certifications, awards, languages, and other sections from the source resume.\n"
        "2) Do NOT drop jobs, merge away history, or shorten the resume into a summary. "
        "The updated resume must be at least as complete as the source.\n"
        "3) Keep original facts truthful. You may polish wording and add clarity/metrics "
        "only when reasonably implied; never invent employers or degrees.\n"
        "4) Weave missing_keywords naturally into summary, skills, and relevant bullets "
        "without keyword stuffing.\n"
        "5) Preserve contact details found in the source; use empty strings if unknown.\n"
        "6) If the source has extra sections, put them in additional_sections.\n"
        "7) Prefer more complete bullets over fewer polished ones."
    )
    keywords = ", ".join(str(k) for k in (missing_keywords or []) if str(k).strip())
    user_prompt = (
        f"Target role:\n{target_role.strip()}\n\n"
        f"Job description:\n{(job_description or '').strip() or '(not provided)'}\n\n"
        f"Missing keywords to weave in:\n{keywords or '(none)'}\n\n"
        f"SOURCE RESUME (preserve all content; update and enrich, do not trim):\n"
        f"{resume_text.strip()}"
    )
    data = _chat_json(system_prompt, user_prompt, temperature=0.3)
    updated = data.get("updated_resume") if isinstance(data, dict) else None
    if not isinstance(updated, dict):
        updated = data if isinstance(data, dict) else {}
    # Defensive defaults so PDF/templates never crash on partial model output.
    updated.setdefault("full_name", "")
    updated.setdefault("headline", "")
    updated.setdefault("summary", "")
    updated.setdefault("contact", {})
    updated.setdefault("skills", [])
    updated.setdefault("experience", [])
    updated.setdefault("projects", [])
    updated.setdefault("education", [])
    updated.setdefault("certifications", [])
    updated.setdefault("awards", [])
    updated.setdefault("languages", [])
    updated.setdefault("additional_sections", [])
    if not isinstance(updated.get("experience"), list):
        updated["experience"] = []
    if not isinstance(updated.get("skills"), list):
        updated["skills"] = []
    return updated


def write_cover_letter(
    resume_text: str,
    target_role: str,
    job_description: str,
    updated_resume: dict,
) -> str:
    system_prompt = (
        "You are an expert career writer. Return ONLY valid JSON. No markdown fences. "
        f"Use exactly this shape: {json.dumps(COVER_SCHEMA_HINT)}. "
        "cover_letter must be a polished 3–5 paragraph letter tailored to the role and JD, "
        "first person, ready to send. Reference real experience from the resume."
    )
    user_prompt = (
        f"Target role:\n{target_role.strip()}\n\n"
        f"Job description:\n{(job_description or '').strip() or '(not provided)'}\n\n"
        f"Updated resume JSON:\n{json.dumps(updated_resume)[:12000]}\n\n"
        f"Original resume excerpt:\n{resume_text.strip()[:8000]}"
    )
    data = _chat_json(system_prompt, user_prompt, temperature=0.4)
    return str(data.get("cover_letter") or "").strip()


PACK_CHECKLIST = [
    (1, "ATS score and clear verdict"),
    (2, "Missing keywords from the JD"),
    (3, "Updated resume with those keywords"),
    (4, "Five professional PDF templates"),
    (5, "Tailored cover letter"),
    (6, "India Tier-1/2/3 salary bands"),
]

RESULT_NAV = [
    ("ats", "ATS score", "Match score & verdict"),
    ("keywords", "Keywords", "Gaps woven into resume"),
    ("resume", "Updated resume", "Full content kept"),
    ("templates", "Templates", "5 PDF layouts"),
    ("cover", "Cover letter", "Ready to send"),
    ("salary", "India salary", "Tier-1 / 2 / 3 LPA"),
]

BUFFER_ICONS = [
    ("◈", "Score"),
    ("⌘", "Keywords"),
    ("▣", "Resume"),
    ("▤", "Templates"),
    ("✉", "Letter"),
    ("₹", "Salary"),
]

BUFFER_PUNCHLINES = [
    "Your next interview starts with a clearer resume.",
    "Keywords aren’t fluff — they’re how ATS finds you.",
    "Keeping your full story. Making it land harder.",
    "The right city. The right role. The right fit.",
    "This pack is being built around your role.",
    "Confidence isn’t luck. It’s a matching resume.",
    "Stay here — your application pack is taking shape.",
    "Every line is yours. Every keyword earns its place.",
]


def render_receive_checklist(
    done_ids: set[int] | None = None,
    active_id: int | None = None,
    *,
    title: str = "You will receive",
    subtitle: str | None = None,
) -> str:
    done_ids = done_ids or set()
    rows = []
    for num, label in PACK_CHECKLIST:
        state = "pending"
        mark = str(num)
        if num in done_ids:
            state = "done"
            mark = "✓"
        elif active_id == num:
            state = "active"
            mark = "…"
        rows.append(
            f'<div class="check-row {state}">'
            f'<span class="check-mark">{mark}</span>'
            f"<span>{html.escape(label)}</span>"
            f"</div>"
        )
    sub = (
        f'<p class="check-sub">{html.escape(subtitle)}</p>'
        if subtitle
        else ""
    )
    return (
        f'<div class="check-board">'
        f'<p class="section-label">{html.escape(title)}</p>'
        f"{sub}"
        f'<div class="check-list">{"".join(rows)}</div>'
        f"</div>"
    )


def render_buffering_stage(
    done_ids: set[int],
    active_id: int | None = None,
    *,
    title: str,
    subtitle: str | None = None,
    finished: bool = False,
) -> str:
    """Premium buffer UI: forge ring, fitted punchlines, live checklist."""
    stage_class = "buffer-stage is-done" if finished else "buffer-stage"
    icons = "".join(
        f'<div class="spin-icon" style="--i:{idx}">'
        f"<span>{icon}</span>"
        f"<em>{html.escape(label)}</em>"
        f"</div>"
        for idx, (icon, label) in enumerate(BUFFER_ICONS)
    )
    punches = "".join(
        f'<p class="punch">{html.escape(line)}</p>' for line in BUFFER_PUNCHLINES
    )
    done_count = len(done_ids or set())
    progress = int((done_count / max(len(PACK_CHECKLIST), 1)) * 100)
    headline = "Your pack is ready." if finished else "Forging your application pack."
    support = (
        "Open the deliverables below — built around your role, not a generic template."
        if finished
        else "Don’t switch tabs. The best version of your resume is coming together."
    )
    core_label = "Ready" if finished else "Forging"
    return f"""
    <div class="{stage_class}">
      <div class="buffer-layout">
        <div class="forge-panel">
          <div class="forge-ring">
            <div class="forge-core">
              <div class="forge-halo"></div>
              <span>◈</span>
              <em>{core_label}</em>
            </div>
          </div>
          <div class="icon-orbit" aria-hidden="true">{icons}</div>
        </div>
        <div class="buffer-copy">
          <p class="section-label">{'Complete' if finished else 'Live preparation'}</p>
          <h3 class="buffer-title">{html.escape(headline)}</h3>
          <p class="buffer-support">{html.escape(support)}</p>
          <div class="punch-stage" aria-live="polite">{punches}</div>
          <div class="forge-meter"><div class="forge-meter-fill" style="width:{100 if finished else max(progress, 10)}%"></div></div>
          <p class="forge-meter-label">{done_count}/6 deliverables ready</p>
        </div>
      </div>
      {render_receive_checklist(done_ids, active_id, title=title, subtitle=subtitle)}
    </div>
    """


def paint_buffering_stage(
    slot,
    done_ids: set[int],
    active_id: int | None = None,
    *,
    title: str,
    subtitle: str | None = None,
    finished: bool = False,
) -> None:
    with slot.container():
        render_html(
            render_buffering_stage(
                done_ids,
                active_id,
                title=title,
                subtitle=subtitle,
                finished=finished,
            )
        )


def run_analysis_pipeline(
    resume_text: str, target_role: str, job_description: str
) -> dict:
    """Multi-step analysis with live checklist, icons, and punchlines."""
    result: dict = {}
    done: set[int] = set()
    slot = st.empty()

    paint_buffering_stage(
        slot,
        done,
        active_id=1,
        title="Preparing your pack",
        subtitle="Watch each deliverable check off as it finishes.",
    )

    fit = analyze_fit_and_market(resume_text, target_role, job_description)
    result.update(fit)
    done.update({1, 2, 6})
    paint_buffering_stage(
        slot,
        done,
        active_id=3,
        title="Preparing your pack",
        subtitle=(
            f"ATS {fit.get('ats_score', '—')} ready · "
            f"{len(fit.get('missing_keywords') or [])} keyword gaps · salary bands ready"
        ),
    )

    updated = rewrite_full_resume(
        resume_text,
        target_role,
        job_description,
        fit.get("missing_keywords") or [],
    )
    result["updated_resume"] = updated
    done.update({3, 4})
    roles = len((updated or {}).get("experience") or [])
    paint_buffering_stage(
        slot,
        done,
        active_id=5,
        title="Preparing your pack",
        subtitle=f"Full resume updated ({roles} roles kept) · templates unlocked",
    )

    result["cover_letter"] = write_cover_letter(
        resume_text, target_role, job_description, updated
    )
    done.add(5)
    paint_buffering_stage(
        slot,
        done,
        title="Pack ready",
        subtitle="All 6 deliverables are ready — open them in Results below.",
        finished=True,
    )
    return result


def score_color(score: int) -> str:
    if score < 50:
        return "#a84848"
    if score < 75:
        return "#9a7040"
    return "#2f6f6a"


def score_label(score: int) -> str:
    if score < 50:
        return "Needs work"
    if score < 75:
        return "Promising"
    return "Strong ATS fit"


def resolve_source_text(
    mode: str,
    uploaded_file,
    pasted_payload,
    typed_text: str,
) -> str:
    if mode == "PDF":
        if uploaded_file is None:
            return ""
        return extract_pdf_text(uploaded_file)
    if mode == "Image":
        if pasted_payload and isinstance(pasted_payload, dict) and pasted_payload.get("data"):
            image_bytes, mime = data_url_to_bytes(pasted_payload["data"])
            return extract_text_from_image_bytes(image_bytes, mime)
        if uploaded_file is not None:
            mime = uploaded_file.type or "image/png"
            return extract_text_from_image_bytes(uploaded_file.getvalue(), mime)
        return ""
    return (typed_text or "").strip()


def inject_styles() -> None:
    inject_theme_styles(render_html)


def format_updated_resume_text(resume: dict) -> str:
    if not isinstance(resume, dict):
        return str(resume or "")
    lines = []
    name = resume.get("full_name") or ""
    headline = resume.get("headline") or ""
    contact = resume.get("contact") or {}
    if name:
        lines.append(name)
    if headline:
        lines.append(headline)
    contact_bits = [
        contact.get("email"),
        contact.get("phone"),
        contact.get("location"),
        contact.get("linkedin"),
    ]
    contact_line = " · ".join(x for x in contact_bits if x)
    if contact_line:
        lines.append(contact_line)
    lines.append("")
    if resume.get("summary"):
        lines.extend(["SUMMARY", resume["summary"], ""])
    skills = resume.get("skills") or []
    if skills:
        lines.extend(["SKILLS", " · ".join(str(s) for s in skills), ""])
    if resume.get("experience"):
        lines.append("EXPERIENCE")
        for job in resume["experience"]:
            title = job.get("title") or ""
            company = job.get("company") or ""
            dates = job.get("dates") or ""
            lines.append(f"{title} — {company}".strip(" —"))
            if dates:
                lines.append(dates)
            for bullet in job.get("bullets") or []:
                lines.append(f"• {bullet}")
            lines.append("")
    if resume.get("projects"):
        lines.append("PROJECTS")
        for project in resume["projects"]:
            lines.append(project.get("name") or "Project")
            if project.get("description"):
                lines.append(project["description"])
            for bullet in project.get("bullets") or []:
                lines.append(f"• {bullet}")
            lines.append("")
    if resume.get("education"):
        lines.append("EDUCATION")
        for edu in resume["education"]:
            degree = edu.get("degree") or ""
            school = edu.get("school") or ""
            dates = edu.get("dates") or ""
            lines.append(f"{degree} — {school}".strip(" —"))
            if dates:
                lines.append(dates)
        lines.append("")
    if resume.get("certifications"):
        lines.extend(
            [
                "CERTIFICATIONS",
                " · ".join(str(c) for c in resume["certifications"]),
                "",
            ]
        )
    if resume.get("awards"):
        lines.append("AWARDS")
        for award in resume["awards"]:
            lines.append(f"• {award}")
        lines.append("")
    if resume.get("languages"):
        lines.extend(
            ["LANGUAGES", " · ".join(str(lang) for lang in resume["languages"]), ""]
        )
    for section in resume.get("additional_sections") or []:
        title = section.get("title") or "ADDITIONAL"
        lines.append(str(title).upper())
        if section.get("content"):
            lines.append(str(section["content"]))
        for item in section.get("items") or []:
            lines.append(f"• {item}")
        lines.append("")
    return "\n".join(lines).strip()


def render_salary_block(salary: dict | None, target_role: str) -> str:
    salary = salary or {}
    assumption = html.escape(str(salary.get("role_level_assumption") or "Based on resume seniority"))
    disclaimer = html.escape(
        str(
            salary.get("disclaimer")
            or "Indicative India market ranges in INR LPA; actual offers vary."
        )
    )
    role = html.escape(target_role or "this role")

    def card(tier_key: str, label: str) -> str:
        tier = salary.get(tier_key) or {}
        cities = html.escape(str(tier.get("cities") or "—"))
        avg = html.escape(str(tier.get("average_lpa") or "—"))
        rng = html.escape(str(tier.get("typical_range_lpa") or avg))
        return (
            f'<div class="salary-card">'
            f"<h4>{label}</h4>"
            f'<div class="band">{avg} LPA</div>'
            f"<p>Typical range: {rng} LPA</p>"
            f"<p>{cities}</p>"
            f"</div>"
        )

    return f"""
    <p class="section-label">Compensation</p>
    <p class="panel-title">Average package in India · {role}</p>
    <p class="hint-line">{assumption}. Figures are indicative CTC in Lakh per annum.</p>
    <div class="salary-grid">
      {card("tier1", "Tier-1 cities")}
      {card("tier2", "Tier-2 cities")}
      {card("tier3", "Tier-3 cities")}
    </div>
    <p class="hint-line" style="margin-top:0.85rem;">{disclaimer}</p>
    """


def render_insight_rows(items: list, kind: str) -> str:
    icon = "✓" if kind == "strength" else "→"
    rows = []
    for item in items or []:
        rows.append(
            f'<div class="insight-row {kind}">'
            f"<span>{icon}</span><span>{html.escape(str(item))}</span>"
            f"</div>"
        )
    return "".join(rows) or '<p class="empty-note">No items returned.</p>'


def render_keywords(keywords: list) -> str:
    if not keywords:
        return '<p class="empty-note">No missing keywords flagged.</p>'
    chips = "".join(
        f'<span class="chip">{html.escape(str(k))}</span>' for k in keywords
    )
    return f'<div class="chip-row">{chips}</div>'


st.set_page_config(
    page_title="Resume Analyser",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

for key, default in {
    "analysis": None,
    "pending_analysis": None,
    "analysis_error": None,
    "selected_template": "modern",
    "show_done_guide": False,
    "analyzed_role": "",
    "result_view": "ats",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

inject_styles()

render_html(
    """
<section class="brand-hero">
  <div class="brand-kicker">Made for your next offer</div>
  <h1 class="brand-mark">Resume <span>Analyser</span></h1>
  <p class="brand-sub">
    Paste a Naukri or LinkedIn screenshot. Leave with a fitted resume, cover letter,
    and the confidence that ATS will finally see you.
  </p>
</section>
<div class="story-strip">
  <div class="story-beat"><strong>See</strong><span>Your resume against the real JD — including screenshots.</span></div>
  <div class="story-beat"><strong>Fit</strong><span>Keywords woven in. Full history kept. Never truncated.</span></div>
  <div class="story-beat"><strong>Send</strong><span>Templates, cover letter, and India salary bands — ready.</span></div>
</div>
"""
)

input_col, meta_col = st.columns([1.4, 1], gap="large")

with input_col:
    with st.container(key="resume-panel"):
        render_html(
            '<p class="section-label">Step 1a</p>'
            '<p class="panel-title">Your resume</p>'
            '<p class="hint-line">PDF, image, pasted screenshot, or plain text — whatever you have.</p>'
        )
        resume_mode = st.radio(
            "Resume input",
            ["PDF", "Image", "Text"],
            horizontal=True,
            key="resume_mode",
            label_visibility="collapsed",
        )

        resume_file = None
        resume_paste = None
        resume_typed = ""

        if resume_mode == "PDF":
            resume_file = st.file_uploader(
                "Resume PDF",
                type=["pdf"],
                key="resume_pdf",
                label_visibility="collapsed",
            )
        elif resume_mode == "Image":
            resume_paste = paste_image(
                label="Click here, then Ctrl+V / Cmd+V to paste resume screenshot",
                key="resume_paste",
            )
            resume_file = st.file_uploader(
                "Or upload resume image",
                type=["png", "jpg", "jpeg", "webp"],
                key="resume_image",
            )
        else:
            resume_typed = st.text_area(
                "Paste resume text",
                height=190,
                placeholder="Paste your full resume text…",
                label_visibility="collapsed",
                key="resume_text_input",
            )

    st.write("")

    with st.container(key="jd-panel"):
        render_html(
            '<p class="section-label">Step 1b</p>'
            '<p class="panel-title">Job description</p>'
            '<p class="hint-line">Paste a screenshot from LinkedIn, Naukri, or Indeed — or skip and score by role alone.</p>'
        )
        jd_mode = st.radio(
            "JD input",
            ["Image", "Text", "Skip"],
            horizontal=True,
            key="jd_mode",
            label_visibility="collapsed",
        )

        jd_file = None
        jd_paste = None
        jd_typed = ""

        if jd_mode == "Image":
            jd_paste = paste_image(
                label="Click here, then Ctrl+V / Cmd+V to paste JD screenshot",
                key="jd_paste",
            )
            jd_file = st.file_uploader(
                "Or upload JD image",
                type=["png", "jpg", "jpeg", "webp"],
                key="jd_image",
            )
        elif jd_mode == "Text":
            jd_typed = st.text_area(
                "Paste job description",
                height=170,
                placeholder="Paste the job description…",
                label_visibility="collapsed",
                key="jd_text_input",
            )
        else:
            st.caption("We’ll still score against your target role.")

with meta_col:
    with st.container(key="target-panel"):
        render_html(
            '<p class="section-label">Step 2</p>'
            '<p class="panel-title">Target role</p>'
            '<p class="hint-line">Be specific — this steers ATS scoring and the rewrite.</p>'
        )
        target_role = st.text_input(
            "Target role",
            placeholder="e.g. Senior Product Manager",
            label_visibility="collapsed",
        )
        analyze = st.button("Analyse resume", type="primary", use_container_width=True)
        render_html(render_receive_checklist(title="You will receive"))

if analyze:
    if not target_role.strip():
        st.warning("Add a target role to continue.")
    elif not get_xai_api_key():
        st.error(
            "XAI_API_KEY is missing. Add it in Streamlit App settings → Secrets "
            '(XAI_API_KEY = "xai-...") or in your local .env before analysing.'
        )
    else:
        try:
            with st.spinner("Reading your documents…"):
                resume_text = resolve_source_text(
                    resume_mode,
                    resume_file,
                    resume_paste,
                    resume_typed,
                )
                if jd_mode == "Skip":
                    job_description = ""
                else:
                    job_description = resolve_source_text(
                        "Image" if jd_mode == "Image" else "Text",
                        jd_file,
                        jd_paste,
                        jd_typed,
                    )
            if not resume_text.strip():
                st.warning("Add a resume via PDF, image, or text first.")
            elif len(resume_text.split()) < 40:
                st.warning(
                    "That resume looks too short to analyse well. "
                    "Try a fuller PDF, clearer screenshot, or paste more text."
                )
            else:
                st.session_state.pending_analysis = {
                    "resume_text": resume_text,
                    "target_role": target_role,
                    "job_description": job_description,
                }
                st.session_state.analysis = None
                st.session_state.analysis_error = None
                st.rerun()
        except Exception as exc:
            st.error(f"Could not read input: {exc}")

st.write("")
render_html(
    '<p class="section-label">Step 3 · Results</p>'
    '<p class="panel-title" style="margin-bottom:0.85rem;">Your application pack</p>'
)

pending = st.session_state.pending_analysis
if pending:
    try:
        st.session_state.analysis = run_analysis_pipeline(
            resume_text=pending["resume_text"],
            target_role=pending["target_role"],
            job_description=pending["job_description"],
        )
        st.session_state.analysis_error = None
        st.session_state.show_done_guide = True
        st.session_state.analyzed_role = pending["target_role"]
        st.session_state.result_view = "ats"
    except Exception as exc:
        st.session_state.analysis = None
        st.session_state.analysis_error = str(exc)
    finally:
        st.session_state.pending_analysis = None
    st.rerun()

analysis = st.session_state.analysis
if analysis:
    try:
        score = int(analysis.get("ats_score", analysis.get("score", 0)))
    except (TypeError, ValueError):
        score = 0
    score = max(0, min(100, score))
    color = score_color(score)
    verdict = html.escape(str(analysis.get("verdict", "No verdict provided.")))
    updated = analysis.get("updated_resume") or {}
    cover_letter = str(analysis.get("cover_letter") or "").strip()
    missing = analysis.get("missing_keywords") or []
    target_for_salary = st.session_state.get("analyzed_role") or ""
    tier1_avg = html.escape(
        str(((analysis.get("india_salary") or {}).get("tier1") or {}).get("average_lpa") or "—")
    )

    render_html(
        f"""
        <div class="results-hero">
          <div class="gauge" style="background: conic-gradient({color} 0% {score}%, #e6eaee {score}% 100%);">
            <div class="gauge-inner">
              <div class="gauge-score" style="color:{color};">{score}</div>
              <div class="gauge-caption">ATS</div>
            </div>
          </div>
          <div>
            <h2>Pack ready · {score_label(score)}</h2>
            <p>{verdict}</p>
            <div class="pill" style="color:{color};background:{color}1a;margin-top:0.65rem;">
              {len(missing)} keywords woven · Tier-1 ~ {tier1_avg} LPA
            </div>
          </div>
        </div>
        <div class="pack-grid">
          <div class="pack-card"><div class="idx">01</div><h4>ATS score</h4><p>Verdict, strengths, improvements</p></div>
          <div class="pack-card"><div class="idx">02</div><h4>Keywords</h4><p>{len(missing)} gaps filled into the rewrite</p></div>
          <div class="pack-card"><div class="idx">03</div><h4>Updated resume</h4><p>Full history kept, not trimmed</p></div>
          <div class="pack-card"><div class="idx">04</div><h4>Templates</h4><p>Five professional PDF layouts</p></div>
          <div class="pack-card"><div class="idx">05</div><h4>Cover letter</h4><p>Tailored and download-ready</p></div>
          <div class="pack-card"><div class="idx">06</div><h4>India salary</h4><p>Tier-1 / 2 / 3 city bands</p></div>
        </div>
        """
    )

    render_html(render_receive_checklist(done_ids={1, 2, 3, 4, 5, 6}, title="Delivered"))

    with st.container(key="result-nav"):
        render_html(
            '<p class="section-label" style="margin-top:1rem;">Open a deliverable</p>'
        )
        view_ids = [item[0] for item in RESULT_NAV]
        labels = {item[0]: item[1] for item in RESULT_NAV}
        view = st.radio(
            "Open deliverable",
            options=view_ids,
            format_func=lambda key: labels[key],
            horizontal=True,
            key="result_view",
            label_visibility="collapsed",
        )

    if view == "ats":
        with st.container(key="score-panel"):
            render_html(
                f"""
                <p class="section-label">Deliverable 01</p>
                <p class="panel-title">ATS score and clear verdict</p>
                <div class="score-wrap" style="margin-top:0.8rem;">
                  <div class="gauge" style="background: conic-gradient({color} 0% {score}%, #e6eaee {score}% 100%);">
                    <div class="gauge-inner">
                      <div class="gauge-score" style="color:{color};">{score}</div>
                      <div class="gauge-caption">ATS</div>
                    </div>
                  </div>
                  <div class="score-meta">
                    <h3>{score_label(score)}</h3>
                    <p>{verdict}</p>
                  </div>
                </div>
                <div class="split-two">
                  <div>
                    <p class="section-label">Strengths</p>
                    {render_insight_rows(analysis.get("strengths") or [], "strength")}
                  </div>
                  <div>
                    <p class="section-label">Improve</p>
                    {render_insight_rows(analysis.get("improvements") or [], "improvement")}
                  </div>
                </div>
                """
            )

    elif view == "keywords":
        with st.container(key="keywords-panel"):
            render_html(
                f"""
                <p class="section-label">Deliverable 02</p>
                <p class="panel-title">Missing keywords from the JD</p>
                <p class="hint-line">These terms were woven into your updated resume without cutting existing content.</p>
                {render_keywords(missing)}
                """
            )

    elif view == "resume":
        preview = format_updated_resume_text(updated)
        with st.container(key="resume-result-panel"):
            render_html(
                f"""
                <p class="section-label">Deliverable 03</p>
                <p class="panel-title">Updated resume with those keywords</p>
                <p class="hint-line">Full original history preserved and enriched — not truncated.</p>
                <div class="resume-preview">{html.escape(preview)}</div>
                """
            )
            st.download_button(
                "Download updated resume (.txt)",
                data=preview.encode("utf-8"),
                file_name="updated_resume.txt",
                mime="text/plain",
                use_container_width=True,
            )

    elif view == "templates":
        with st.container(key="templates-panel"):
            cards = "".join(
                f'<div class="template-card"><h4>{html.escape(t["name"])}</h4>'
                f'<p>{html.escape(t["blurb"])}</p></div>'
                for t in TEMPLATES
            )
            render_html(
                f"""
                <p class="section-label">Deliverable 04</p>
                <p class="panel-title">Five professional PDF templates</p>
                <p class="hint-line">Pick a layout. PDFs can span multiple pages so nothing is cut for length.</p>
                <div class="template-grid">{cards}</div>
                """
            )
            template_names = {t["name"]: t["id"] for t in TEMPLATES}
            choice = st.selectbox(
                "Template",
                options=list(template_names.keys()),
                index=1,
                label_visibility="collapsed",
            )
            template_id = template_names[choice]
            st.session_state.selected_template = template_id
            try:
                pdf_bytes = build_resume_pdf(updated, template_id)
                st.download_button(
                    f"Download {choice} PDF",
                    data=pdf_bytes,
                    file_name=f"resume_{template_id}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True,
                )
            except Exception as exc:
                st.error(f"Could not build PDF: {exc}")

    elif view == "cover":
        with st.container(key="cover-panel"):
            if cover_letter:
                render_html(
                    f"""
                    <p class="section-label">Deliverable 05</p>
                    <p class="panel-title">Tailored cover letter</p>
                    <p class="hint-line">Send this with your updated resume.</p>
                    <div class="cover-box">{html.escape(cover_letter)}</div>
                    """
                )
                c1, c2 = st.columns(2)
                with c1:
                    st.download_button(
                        "Download .txt",
                        data=cover_letter.encode("utf-8"),
                        file_name="cover_letter.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )
                with c2:
                    try:
                        cover_pdf = build_cover_letter_pdf(
                            cover_letter,
                            candidate_name=str(updated.get("full_name") or ""),
                        )
                        st.download_button(
                            "Download PDF",
                            data=cover_pdf,
                            file_name="cover_letter.pdf",
                            mime="application/pdf",
                            type="primary",
                            use_container_width=True,
                        )
                    except Exception as exc:
                        st.error(f"Could not build cover letter PDF: {exc}")
            else:
                render_html('<p class="empty-note">No cover letter was returned.</p>')

    else:
        with st.container(key="salary-panel"):
            render_html(
                '<p class="section-label">Deliverable 06</p>'
                + render_salary_block(analysis.get("india_salary"), target_for_salary)
            )

elif st.session_state.analysis_error:
    st.error(f"Analysis failed: {st.session_state.analysis_error}")
else:
    with st.container(key="empty-panel"):
        render_html(
            """
            <div class="placeholder">
              <div class="placeholder-mark">◈</div>
              <p>Run Analyse to build your pack. During buffering, each item on the checklist will tick off live.</p>
            </div>
            """
            + render_receive_checklist(
                title="You will receive",
                subtitle="Same list checks off while we prepare your pack.",
            )
        )
