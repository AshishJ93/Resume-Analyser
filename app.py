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

from paste_image import paste_image
from pdf_templates import TEMPLATES, build_cover_letter_pdf, build_resume_pdf

load_dotenv()

ANALYSIS_SCHEMA_HINT = {
    "ats_score": 0,
    "verdict": "one sentence",
    "strengths": ["...", "...", "..."],
    "improvements": ["...", "...", "..."],
    "missing_keywords": ["keyword1", "keyword2"],
    "updated_resume": {
        "full_name": "Full Name",
        "headline": "Target role headline",
        "summary": "3-4 sentence professional summary including missing keywords naturally",
        "contact": {
            "email": "",
            "phone": "",
            "location": "",
            "linkedin": "",
        },
        "skills": ["skill1", "skill2"],
        "experience": [
            {
                "title": "Job title",
                "company": "Company",
                "dates": "YYYY – YYYY",
                "bullets": ["impact bullet with metrics", "another bullet"],
            }
        ],
        "projects": [
            {
                "name": "Project",
                "description": "short description",
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
    },
    "cover_letter": "Full cover letter text with paragraphs separated by newlines",
}


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


def analyze_and_upgrade(
    resume_text: str, target_role: str, job_description: str
) -> dict:
    client = get_client()
    system_prompt = (
        "You are an expert ATS resume strategist, recruiter, and career writer. "
        "Return ONLY valid JSON. No markdown fences, no commentary. "
        f"Use exactly this shape: {json.dumps(ANALYSIS_SCHEMA_HINT)}. "
        "ats_score must be an integer from 0 to 100 estimating ATS / role match. "
        "verdict must be one sentence. "
        "strengths and improvements must each contain exactly 3 concise items. "
        "missing_keywords must list important role/JD keywords missing or weak in the resume. "
        "updated_resume must be a complete, professional resume rewrite that naturally "
        "weaves in the missing keywords without stuffing, keeps truthful experience from the "
        "source resume, improves bullets with clarity and metrics where reasonable, and "
        "targets the role. Preserve contact details found in the resume; use empty strings "
        "if unknown. "
        "cover_letter must be a polished 3–5 paragraph cover letter tailored to the role "
        "and JD, written in first person, ready to send."
    )
    user_prompt = (
        f"Target role:\n{target_role.strip()}\n\n"
        f"Job description:\n{(job_description or '').strip() or '(not provided)'}\n\n"
        f"Resume:\n{resume_text.strip()}"
    )
    response = client.chat.completions.create(
        model=os.getenv("XAI_MODEL", "grok-4.3"),
        temperature=0.35,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    content = response.choices[0].message.content or "{}"
    data = parse_model_json(content)
    if "ats_score" not in data and "score" in data:
        data["ats_score"] = data["score"]
    return data


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
    label: str,
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
    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
        <style>
          :root {
            --ink: #1a1d23;
            --muted: #5c6570;
            --line: #e2e6eb;
            --soft: #f3f5f7;
            --surface: #ffffff;
            --accent: #2f6f6a;
            --accent-2: #3d7f8f;
            --accent-soft: #e8f2f1;
            --warn: #9a7040;
            --bad: #a84848;
          }

          #MainMenu, footer, header,
          [data-testid="stHeader"],
          [data-testid="stToolbar"],
          [data-testid="stDecoration"],
          [data-testid="stStatusWidget"] {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
          }

          html, body, [class*="css"] {
            font-family: "Manrope", sans-serif;
          }

          .stApp {
            background:
              radial-gradient(1200px 520px at 8% -10%, rgba(47, 111, 106, 0.10), transparent 55%),
              radial-gradient(900px 480px at 100% 0%, rgba(61, 127, 143, 0.10), transparent 50%),
              linear-gradient(180deg, #eef2f4 0%, #f7f8fa 42%, #f3f5f7 100%);
            color: var(--ink);
          }

          .block-container {
            max-width: 1120px;
            padding-top: 1.6rem;
            padding-bottom: 3.5rem;
          }

          .brand-hero {
            margin: 0 0 1.5rem;
            animation: rise 0.7s ease both;
          }

          .brand-mark {
            font-family: "Space Grotesk", sans-serif;
            font-size: clamp(2.2rem, 4vw, 3.1rem);
            font-weight: 700;
            letter-spacing: -0.045em;
            line-height: 1.05;
            color: var(--ink);
            margin: 0;
          }

          .brand-mark span {
            color: var(--accent);
          }

          .brand-sub {
            margin: 0.7rem 0 0;
            max-width: 34rem;
            color: var(--muted);
            font-size: 1.02rem;
            line-height: 1.55;
            animation: rise 0.85s ease both;
          }

          .section-label {
            margin: 0 0 0.75rem;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: var(--accent);
          }

          .panel,
          .st-key-resume-panel,
          .st-key-jd-panel,
          .st-key-target-panel,
          .st-key-resume-result-panel,
          .st-key-templates-panel,
          .st-key-cover-panel {
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid rgba(226, 230, 235, 0.95);
            border-radius: 18px;
            padding: 1.15rem 1.2rem 1.25rem;
            backdrop-filter: blur(8px);
            box-shadow: 0 10px 30px rgba(26, 29, 35, 0.04);
            animation: rise 0.75s ease both;
          }

          .hint-line {
            margin: 0.15rem 0 0.85rem;
            color: var(--muted);
            font-size: 0.86rem;
          }

          .score-wrap {
            display: grid;
            grid-template-columns: 140px 1fr;
            gap: 1.1rem;
            align-items: center;
            padding: 0.35rem 0.1rem 0.5rem;
          }

          .gauge {
            width: 124px;
            height: 124px;
            border-radius: 50%;
            display: grid;
            place-items: center;
          }

          .gauge-inner {
            width: 94px;
            height: 94px;
            border-radius: 50%;
            background: #fff;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            box-shadow: inset 0 0 0 1px #eef1f4;
          }

          .gauge-score {
            font-family: "Space Grotesk", sans-serif;
            font-size: 2rem;
            font-weight: 700;
            line-height: 1;
            letter-spacing: -0.04em;
          }

          .gauge-caption {
            margin-top: 0.25rem;
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #9aa3ad;
          }

          .score-meta h3 {
            margin: 0;
            font-family: "Space Grotesk", sans-serif;
            font-size: 1.2rem;
            letter-spacing: -0.02em;
          }

          .score-meta p {
            margin: 0.45rem 0 0;
            color: var(--muted);
            line-height: 1.5;
            font-size: 0.95rem;
          }

          .pill {
            display: inline-flex;
            align-items: center;
            margin-top: 0.55rem;
            padding: 0.28rem 0.7rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 700;
          }

          .chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
          }

          .chip {
            display: inline-flex;
            align-items: center;
            padding: 0.38rem 0.75rem;
            border-radius: 999px;
            background: var(--accent-soft);
            color: #215652;
            border: 1px solid #cfe3e1;
            font-size: 0.82rem;
            font-weight: 650;
          }

          .insight-row {
            display: flex;
            gap: 0.65rem;
            padding: 0.7rem 0.8rem;
            border-radius: 12px;
            margin-bottom: 0.45rem;
            background: #f7f8fa;
            border-left: 3px solid transparent;
            color: var(--ink);
            font-size: 0.92rem;
            line-height: 1.45;
          }

          .insight-row.strength {
            background: #eef7f3;
            border-left-color: #2f6f6a;
          }

          .insight-row.improvement {
            background: #f8f3eb;
            border-left-color: #9a7040;
          }

          .template-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 0.75rem;
          }

          .template-card {
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 0.95rem 1rem;
            background: linear-gradient(180deg, #ffffff 0%, #f7f9fa 100%);
            min-height: 118px;
            transition: transform 0.25s ease, border-color 0.25s ease;
          }

          .template-card:hover {
            transform: translateY(-2px);
            border-color: #b7d4d1;
          }

          .template-card h4 {
            margin: 0;
            font-family: "Space Grotesk", sans-serif;
            font-size: 1rem;
            letter-spacing: -0.02em;
          }

          .template-card p {
            margin: 0.4rem 0 0;
            color: var(--muted);
            font-size: 0.84rem;
            line-height: 1.4;
          }

          .cover-box {
            white-space: pre-wrap;
            background: #f7f8fa;
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 1rem 1.1rem;
            color: var(--ink);
            line-height: 1.6;
            font-size: 0.95rem;
          }

          .resume-preview {
            white-space: pre-wrap;
            background: #f7f8fa;
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 1rem 1.1rem;
            color: var(--ink);
            line-height: 1.55;
            font-size: 0.9rem;
            max-height: 420px;
            overflow: auto;
          }

          .empty-note {
            color: #9aa3ad;
            font-size: 0.92rem;
          }

          .placeholder {
            text-align: center;
            padding: 3.2rem 1rem;
            color: var(--muted);
          }

          .placeholder-mark {
            width: 48px;
            height: 48px;
            margin: 0 auto 0.8rem;
            border-radius: 14px;
            display: grid;
            place-items: center;
            background: var(--accent-soft);
            color: var(--accent);
            font-family: "Space Grotesk", sans-serif;
            font-weight: 700;
          }

          .loading-box {
            text-align: center;
            padding: 2.8rem 1rem;
            color: var(--muted);
          }

          .loading-spinner {
            width: 40px;
            height: 40px;
            margin: 0 auto 0.9rem;
            border-radius: 50%;
            border: 3px solid #dce8e7;
            border-top-color: var(--accent);
            animation: spin 0.8s linear infinite;
          }

          @keyframes spin { to { transform: rotate(360deg); } }
          @keyframes rise {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
          }

          div[data-testid="stRadio"] label p { font-weight: 560; }
          .stTextInput label, .stTextArea label, .stFileUploader label, .stRadio label {
            font-weight: 650 !important;
            color: var(--ink) !important;
          }
          .stTextInput input, .stTextArea textarea {
            border-radius: 12px !important;
            border-color: var(--line) !important;
            background: #fafbfc !important;
          }
          .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: var(--accent) !important;
            box-shadow: 0 0 0 1px var(--accent) !important;
          }
          div[data-testid="stFileUploader"] section {
            border-radius: 12px;
            border-color: #d5e3e1;
            background: #fafbfc;
          }
          button[kind="primary"],
          button[data-testid="stBaseButton-primary"] {
            background: linear-gradient(120deg, #2f6f6a, #3d7f8f) !important;
            border: none !important;
            border-radius: 12px !important;
            color: #fff !important;
            font-weight: 650 !important;
            padding: 0.6rem 1rem !important;
            transition: transform 0.2s ease, filter 0.2s ease !important;
          }
          button[kind="primary"]:hover,
          button[data-testid="stBaseButton-primary"]:hover {
            filter: brightness(1.05) !important;
            transform: translateY(-1px) !important;
          }

          [data-testid="stTabs"] button[aria-selected="true"] {
            color: var(--accent) !important;
          }

          @media (max-width: 800px) {
            .score-wrap { grid-template-columns: 1fr; justify-items: center; text-align: center; }
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


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
    return "\n".join(lines).strip()


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
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

inject_styles()

st.markdown(
    """
    <section class="brand-hero">
      <h1 class="brand-mark">Resume <span>Analyser</span></h1>
      <p class="brand-sub">
        Paste a job screenshot or resume image, get your ATS score, fill keyword gaps,
        and download a polished resume with a matching cover letter.
      </p>
    </section>
    """,
    unsafe_allow_html=True,
)

input_col, meta_col = st.columns([1.35, 1], gap="large")

with input_col:
    with st.container(key="resume-panel"):
        st.markdown('<p class="section-label">Resume</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="hint-line">Upload a PDF, drop an image, or paste a screenshot from your clipboard.</p>',
            unsafe_allow_html=True,
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
                label="Paste resume screenshot",
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
                height=200,
                placeholder="Paste your full resume text…",
                label_visibility="collapsed",
                key="resume_text_input",
            )

    st.markdown("<div style='height:0.85rem'></div>", unsafe_allow_html=True)

    with st.container(key="jd-panel"):
        st.markdown('<p class="section-label">Job description</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="hint-line">Paste a screenshot from LinkedIn, Naukri, Indeed, or upload the image.</p>',
            unsafe_allow_html=True,
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
                label="Paste JD screenshot",
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
                height=180,
                placeholder="Paste the job description…",
                label_visibility="collapsed",
                key="jd_text_input",
            )
        else:
            st.caption("You can still analyze against the target role alone.")

with meta_col:
    with st.container(key="target-panel"):
        st.markdown('<p class="section-label">Target</p>', unsafe_allow_html=True)
        target_role = st.text_input(
            "Target role",
            placeholder="e.g. Senior Product Manager",
            label_visibility="collapsed",
        )
        st.caption("Required. Used for ATS scoring and the rewritten resume.")
        analyze = st.button("Analyse resume", type="primary", use_container_width=True)

        st.markdown(
            """
            <div style="margin-top:1.1rem;">
              <p class="section-label">What you get</p>
              <div class="insight-row strength"><span>1</span><span>ATS score with a clear verdict</span></div>
              <div class="insight-row strength"><span>2</span><span>Missing keywords from the JD</span></div>
              <div class="insight-row strength"><span>3</span><span>Updated resume that weaves them in</span></div>
              <div class="insight-row strength"><span>4</span><span>5 downloadable resume templates</span></div>
              <div class="insight-row strength"><span>5</span><span>Tailored cover letter</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

if analyze:
    if not target_role.strip():
        st.warning("Add a target role to continue.")
    else:
        try:
            with st.spinner("Reading your documents…"):
                resume_text = resolve_source_text(
                    resume_mode,
                    resume_file,
                    resume_paste,
                    resume_typed,
                    "resume",
                )
                if jd_mode == "Skip":
                    job_description = ""
                else:
                    job_description = resolve_source_text(
                        "Image" if jd_mode == "Image" else "Text",
                        jd_file,
                        jd_paste,
                        jd_typed,
                        "job description",
                    )
            if not resume_text.strip():
                st.warning("Add a resume via PDF, image, or text first.")
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

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
st.markdown('<p class="section-label">Results</p>', unsafe_allow_html=True)
results = st.container()

with results:
    pending = st.session_state.pending_analysis
    if pending:
        st.markdown(
            """
            <div class="panel">
              <div class="loading-box">
                <div class="loading-spinner"></div>
                <p>Scoring ATS fit, finding gaps, and drafting your updated pack…</p>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        try:
            st.session_state.analysis = analyze_and_upgrade(
                resume_text=pending["resume_text"],
                target_role=pending["target_role"],
                job_description=pending["job_description"],
            )
            st.session_state.analysis_error = None
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

        tab_score, tab_keywords, tab_resume, tab_templates, tab_cover = st.tabs(
            [
                "ATS score",
                "Missing keywords",
                "Updated resume",
                "Templates",
                "Cover letter",
            ]
        )

        with tab_score:
            st.markdown(
                f"""
                <div class="panel">
                  <div class="score-wrap">
                    <div class="gauge" style="background: conic-gradient({color} 0% {score}%, #e6eaee {score}% 100%);">
                      <div class="gauge-inner">
                        <div class="gauge-score" style="color:{color};">{score}</div>
                        <div class="gauge-caption">ATS</div>
                      </div>
                    </div>
                    <div class="score-meta">
                      <h3>Role match overview</h3>
                      <div class="pill" style="color:{color};background:{color}1a;">{score_label(score)}</div>
                      <p>{verdict}</p>
                    </div>
                  </div>
                  <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;margin-top:0.9rem;">
                    <div>
                      <p class="section-label">Strengths</p>
                      {render_insight_rows(analysis.get("strengths") or [], "strength")}
                    </div>
                    <div>
                      <p class="section-label">Improve</p>
                      {render_insight_rows(analysis.get("improvements") or [], "improvement")}
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with tab_keywords:
            st.markdown(
                f"""
                <div class="panel">
                  <p class="section-label">Keywords to add</p>
                  <p class="hint-line">These terms were weak or missing versus the role / JD. They are woven into the updated resume.</p>
                  {render_keywords(missing)}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with tab_resume:
            preview = format_updated_resume_text(updated)
            with st.container(key="resume-result-panel"):
                st.markdown(
                    '<p class="section-label">Keyword-optimized resume</p>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="resume-preview">{html.escape(preview)}</div>',
                    unsafe_allow_html=True,
                )
                st.download_button(
                    "Download updated resume (.txt)",
                    data=preview.encode("utf-8"),
                    file_name="updated_resume.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

        with tab_templates:
            with st.container(key="templates-panel"):
                st.markdown(
                    '<p class="section-label">Choose a template</p>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<p class="hint-line">Five professional layouts. Pick one and download a PDF of your updated resume.</p>',
                    unsafe_allow_html=True,
                )

                cards = "".join(
                    f'<div class="template-card"><h4>{html.escape(t["name"])}</h4>'
                    f'<p>{html.escape(t["blurb"])}</p></div>'
                    for t in TEMPLATES
                )
                st.markdown(
                    f'<div class="template-grid">{cards}</div>',
                    unsafe_allow_html=True,
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

        with tab_cover:
            with st.container(key="cover-panel"):
                st.markdown(
                    '<p class="section-label">Cover letter</p>',
                    unsafe_allow_html=True,
                )
                if cover_letter:
                    st.markdown(
                        f'<div class="cover-box">{html.escape(cover_letter)}</div>',
                        unsafe_allow_html=True,
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
                    st.markdown(
                        '<p class="empty-note">No cover letter was returned.</p>',
                        unsafe_allow_html=True,
                    )

    elif st.session_state.analysis_error:
        st.error(f"Analysis failed: {st.session_state.analysis_error}")
    else:
        st.markdown(
            """
            <div class="panel">
              <div class="placeholder">
                <div class="placeholder-mark">◈</div>
                <p>Your ATS score, keyword gaps, updated resume, templates, and cover letter will land here.</p>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
