import html
import json
import os
import re
from io import BytesIO

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader

load_dotenv()

ANALYSIS_SCHEMA_HINT = {
    "score": 0,
    "verdict": "one sentence",
    "strengths": ["...", "...", "..."],
    "improvements": ["...", "...", "..."],
    "missing_keywords": ["..."],
    "rewrites": [{"before": "...", "after": "..."}],
}


def extract_pdf_text(uploaded_file) -> str:
    reader = PdfReader(BytesIO(uploaded_file.getvalue()))
    parts = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            parts.append(text)
    return "\n".join(parts).strip()


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def parse_model_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


def get_xai_api_key() -> str | None:
    key = os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")
    if key:
        return key
    try:
        return st.secrets.get("XAI_API_KEY") or st.secrets.get("GROK_API_KEY")
    except Exception:
        return None


def analyze_resume(resume_text: str, target_role: str, job_description: str) -> dict:
    api_key = get_xai_api_key()
    if not api_key:
        raise ValueError(
            "XAI_API_KEY is not set. Add it to your local .env or Streamlit Secrets."
        )

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1",
    )
    system_prompt = (
        "You are an expert resume coach and recruiter. "
        "Return ONLY valid JSON. No markdown, no commentary. "
        f"Use exactly this shape: {json.dumps(ANALYSIS_SCHEMA_HINT)}. "
        "score must be an integer from 0 to 100. "
        "verdict must be one sentence. "
        "strengths and improvements must each contain exactly 3 items. "
        "missing_keywords is a list of important keywords missing from the resume. "
        "rewrites is a list of objects with before/after bullet or phrase rewrites."
    )
    user_prompt = (
        f"Target role:\n{target_role.strip()}\n\n"
        f"Job description:\n{(job_description or '').strip() or '(not provided)'}\n\n"
        f"Resume:\n{resume_text.strip()}"
    )

    response = client.chat.completions.create(
        model=os.getenv("XAI_MODEL", "grok-4.3"),
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    content = response.choices[0].message.content or "{}"
    return parse_model_json(content)


def score_color(score: int) -> str:
    if score < 50:
        return "#ef4444"
    if score < 75:
        return "#f59e0b"
    return "#22c55e"


def score_label(score: int) -> str:
    if score < 50:
        return "Needs work"
    if score < 75:
        return "Solid match"
    return "Strong fit"


def render_list_rows(items: list, kind: str) -> str:
    icon = "✓" if kind == "strength" else "!"
    rows = []
    for item in items or []:
        text = html.escape(str(item))
        rows.append(
            f'<div class="insight-row {kind}">'
            f'<span class="insight-icon">{icon}</span>'
            f"<span>{text}</span>"
            f"</div>"
        )
    if not rows:
        rows.append('<p class="empty-note">No items returned.</p>')
    return "".join(rows)


def render_keyword_chips(keywords: list) -> str:
    if not keywords:
        return '<p class="empty-note">No missing keywords flagged.</p>'
    chips = "".join(
        f'<span class="chip">{html.escape(str(keyword))}</span>'
        for keyword in keywords
    )
    return f'<div class="chip-row">{chips}</div>'


def render_rewrites(rewrites: list) -> str:
    if not rewrites:
        return '<p class="empty-note">No rewrite suggestions returned.</p>'

    blocks = []
    for item in rewrites:
        if isinstance(item, dict):
            before = html.escape(str(item.get("before", "")))
            after = html.escape(str(item.get("after", "")))
        else:
            before = html.escape(str(item))
            after = ""
        blocks.append(
            '<div class="rewrite-pair">'
            f'<div class="rewrite before"><span class="rewrite-label">Before</span><p>{before}</p></div>'
            f'<div class="rewrite after"><span class="rewrite-label">After</span><p>{after}</p></div>'
            "</div>"
        )
    return "".join(blocks)


def render_dashboard(analysis: dict) -> str:
    try:
        score = int(analysis.get("score", 0))
    except (TypeError, ValueError):
        score = 0
    score = max(0, min(100, score))
    color = score_color(score)
    verdict = html.escape(str(analysis.get("verdict", "No verdict provided.")))

    strengths = render_list_rows(analysis.get("strengths") or [], "strength")
    improvements = render_list_rows(analysis.get("improvements") or [], "improvement")
    keywords = render_keyword_chips(analysis.get("missing_keywords") or [])
    rewrites = render_rewrites(analysis.get("rewrites") or [])

    return f"""
    <div class="dashboard">
      <div class="score-panel">
        <div class="gauge" style="background: conic-gradient({color} 0% {score}%, #e5e7eb {score}% 100%);">
          <div class="gauge-inner">
            <div class="gauge-score" style="color: {color};">{score}</div>
            <div class="gauge-caption">Fit score</div>
          </div>
        </div>
        <div class="score-meta">
          <div class="score-pill" style="color: {color}; background: {color}1a;">{score_label(score)}</div>
          <p>Out of 100 based on role fit, clarity, and keyword coverage.</p>
        </div>
      </div>

      <div class="panel-card">
        <div class="panel-title">Overall Assessment</div>
        <p class="verdict">{verdict}</p>
      </div>

      <div class="split-grid">
        <div class="panel-card strengths-card">
          <div class="panel-title success">Strengths</div>
          {strengths}
        </div>
        <div class="panel-card improvements-card">
          <div class="panel-title warning">Improvements</div>
          {improvements}
        </div>
      </div>

      <div class="panel-card">
        <div class="panel-title">Keywords to Add</div>
        {keywords}
      </div>

      <div class="panel-card">
        <div class="panel-title">Suggested Rewrites</div>
        {rewrites}
      </div>
    </div>
    """


st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "pending_analysis" not in st.session_state:
    st.session_state.pending_analysis = None
if "analysis_error" not in st.session_state:
    st.session_state.analysis_error = None

st.markdown(
    """
    <style>
        #MainMenu, footer, header,
        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"] {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
        }

        .stApp {
            background: #f3f4f6;
        }

        .block-container {
            max-width: 1180px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        .hero {
            background: linear-gradient(120deg, #4c1d95 0%, #6d28d9 48%, #8b5cf6 100%);
            border-radius: 20px;
            padding: 2rem 2.25rem 1.9rem;
            color: #ffffff;
            box-shadow: 0 16px 36px rgba(76, 29, 149, 0.22);
            margin-bottom: 1.35rem;
        }

        .hero-badge {
            display: inline-block;
            background: rgba(255, 255, 255, 0.16);
            border: 1px solid rgba(255, 255, 255, 0.32);
            color: #ffffff;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.03em;
            padding: 0.28rem 0.72rem;
            border-radius: 999px;
            margin-bottom: 0.85rem;
        }

        .hero h1 {
            margin: 0;
            padding: 0;
            color: #ffffff;
            font-size: 2.15rem;
            font-weight: 700;
            letter-spacing: -0.025em;
            line-height: 1.15;
        }

        .hero p {
            margin: 0.55rem 0 0;
            color: rgba(255, 255, 255, 0.9);
            font-size: 1.02rem;
            line-height: 1.5;
            max-width: 38rem;
        }

        .st-key-input-card,
        .st-key-result-card {
            background: #ffffff;
            border: 1px solid #e7e5eb;
            border-radius: 16px;
            padding: 1.35rem 1.4rem 1.45rem;
            box-shadow: 0 8px 24px rgba(17, 24, 39, 0.05);
        }

        [data-testid="stColumn"]:has(.st-key-result-card) [data-testid="stLayoutWrapper"] {
            height: 100%;
            flex: 1 1 auto;
        }

        .st-key-result-card {
            min-height: 100%;
            height: 100%;
        }

        [data-testid="stRadioOption"][data-selected="true"] > div > div:first-child {
            background: #7c3aed !important;
            border-color: #7c3aed !important;
        }

        .card-kicker {
            margin: 0 0 0.85rem;
            color: #6d28d9;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }

        .placeholder {
            text-align: center;
            color: #6b7280;
            padding: 4.5rem 1rem;
        }

        .placeholder-mark {
            width: 52px;
            height: 52px;
            margin: 0 auto 0.85rem;
            border-radius: 14px;
            background: #f5f3ff;
            color: #7c3aed;
            font-size: 1.35rem;
            line-height: 52px;
        }

        .placeholder p {
            margin: 0;
            font-size: 1.02rem;
            color: #6b7280;
        }

        .loading-box {
            text-align: center;
            padding: 3.5rem 1rem 3rem;
            color: #6b7280;
        }

        .loading-spinner {
            width: 42px;
            height: 42px;
            margin: 0 auto 1rem;
            border-radius: 50%;
            border: 3px solid #ede9fe;
            border-top-color: #7c3aed;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .dashboard {
            display: flex;
            flex-direction: column;
            gap: 0.9rem;
        }

        .score-panel {
            display: flex;
            align-items: center;
            gap: 1.1rem;
            padding: 0.85rem 0.95rem;
            border: 1px solid #eceaf1;
            border-radius: 14px;
            background: linear-gradient(180deg, #faf9ff 0%, #ffffff 100%);
        }

        .gauge {
            width: 118px;
            height: 118px;
            border-radius: 50%;
            display: grid;
            place-items: center;
            flex-shrink: 0;
        }

        .gauge-inner {
            width: 88px;
            height: 88px;
            border-radius: 50%;
            background: #ffffff;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            box-shadow: inset 0 0 0 1px #f3f4f6;
        }

        .gauge-score {
            font-size: 1.85rem;
            font-weight: 750;
            line-height: 1;
            letter-spacing: -0.03em;
        }

        .gauge-caption {
            margin-top: 0.2rem;
            font-size: 0.68rem;
            font-weight: 650;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            color: #9ca3af;
        }

        .score-meta p {
            margin: 0.45rem 0 0;
            color: #6b7280;
            font-size: 0.92rem;
            line-height: 1.45;
        }

        .score-pill {
            display: inline-block;
            font-size: 0.78rem;
            font-weight: 700;
            padding: 0.28rem 0.65rem;
            border-radius: 999px;
        }

        .panel-card {
            border: 1px solid #eceaf1;
            border-radius: 14px;
            padding: 0.9rem 0.95rem;
            background: #ffffff;
        }

        .panel-title {
            margin: 0 0 0.7rem;
            color: #111827;
            font-size: 0.84rem;
            font-weight: 700;
            letter-spacing: 0.02em;
        }

        .panel-title.success { color: #15803d; }
        .panel-title.warning { color: #b45309; }

        .verdict {
            margin: 0;
            color: #374151;
            font-size: 0.98rem;
            line-height: 1.55;
        }

        .split-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.8rem;
        }

        .insight-row {
            display: flex;
            gap: 0.65rem;
            align-items: flex-start;
            padding: 0.62rem 0.7rem;
            border-radius: 10px;
            margin-bottom: 0.45rem;
            font-size: 0.9rem;
            line-height: 1.4;
            color: #1f2937;
            background: #fafafa;
            border-left: 3px solid transparent;
        }

        .insight-row:last-child {
            margin-bottom: 0;
        }

        .insight-row.strength {
            background: #f0fdf4;
            border-left-color: #22c55e;
        }

        .insight-row.improvement {
            background: #fffbeb;
            border-left-color: #f59e0b;
        }

        .insight-icon {
            width: 1.2rem;
            flex-shrink: 0;
            font-weight: 700;
            text-align: center;
        }

        .insight-row.strength .insight-icon { color: #16a34a; }
        .insight-row.improvement .insight-icon { color: #d97706; }

        .chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
        }

        .chip {
            display: inline-flex;
            align-items: center;
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            background: #f5f3ff;
            color: #5b21b6;
            border: 1px solid #ddd6fe;
            font-size: 0.82rem;
            font-weight: 600;
        }

        .rewrite-pair {
            border: 1px solid #eceaf1;
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 0.55rem;
        }

        .rewrite-pair:last-child {
            margin-bottom: 0;
        }

        .rewrite {
            padding: 0.7rem 0.8rem;
        }

        .rewrite.before {
            background: #fef2f2;
            border-bottom: 1px solid #fecaca;
        }

        .rewrite.after {
            background: #f0fdf4;
        }

        .rewrite-label {
            display: inline-block;
            margin-bottom: 0.25rem;
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }

        .rewrite.before .rewrite-label { color: #dc2626; }
        .rewrite.after .rewrite-label { color: #16a34a; }

        .rewrite p {
            margin: 0;
            color: #1f2937;
            font-size: 0.9rem;
            line-height: 1.45;
        }

        .rewrite.before p { color: #991b1b; }
        .rewrite.after p { color: #166534; }

        .empty-note {
            margin: 0;
            color: #9ca3af;
            font-size: 0.9rem;
        }

        div[data-testid="stRadio"] label p {
            font-weight: 500;
        }

        .stTextInput label, .stTextArea label, .stFileUploader label {
            font-weight: 600 !important;
            color: #111827 !important;
        }

        .stTextInput input, .stTextArea textarea {
            border-radius: 10px !important;
            border-color: #e5e7eb !important;
            background: #fafafa !important;
        }

        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: #8b5cf6 !important;
            box-shadow: 0 0 0 1px #8b5cf6 !important;
        }

        div[data-testid="stFileUploader"] section {
            border-radius: 12px;
            border-color: #ddd6fe;
            background: #fafafa;
        }

        .st-key-input-card button[kind="primary"],
        .st-key-input-card button[data-testid="stBaseButton-primary"] {
            background: linear-gradient(120deg, #6d28d9, #7c3aed) !important;
            border: none !important;
            border-radius: 10px !important;
            color: #ffffff !important;
            font-weight: 600 !important;
            padding: 0.55rem 1rem !important;
        }

        .st-key-input-card button[kind="primary"]:hover,
        .st-key-input-card button[data-testid="stBaseButton-primary"]:hover {
            background: linear-gradient(120deg, #5b21b6, #6d28d9) !important;
        }

        @media (max-width: 900px) {
            .split-grid {
                grid-template-columns: 1fr;
            }

            .score-panel {
                flex-direction: column;
                text-align: center;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <section class="hero">
        <div class="hero-badge">Powered by AI</div>
        <h1>AI Resume Analyzer</h1>
        <p>See how your resume lines up with the role you want, and what to tighten before you apply.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns(2, gap="large")

with left:
    with st.container(key="input-card"):
        st.markdown('<p class="card-kicker">Your resume</p>', unsafe_allow_html=True)
        source = st.radio(
            "Resume source",
            ["Upload PDF", "Paste text"],
            horizontal=True,
            label_visibility="collapsed",
        )

        resume_text = ""
        if source == "Upload PDF":
            resume_file = st.file_uploader("Upload PDF", type=["pdf"])
            if resume_file is not None:
                try:
                    resume_text = extract_pdf_text(resume_file)
                except Exception as exc:
                    st.error(f"Could not read that PDF: {exc}")
                else:
                    if resume_text:
                        st.success(
                            f"Extracted text from **{resume_file.name}** "
                            f"({word_count(resume_text)} words)."
                        )
                    else:
                        st.warning(
                            f"Uploaded **{resume_file.name}**, but no readable text was found."
                        )
        else:
            resume_text = st.text_area(
                "Paste text",
                height=180,
                placeholder="Paste your resume here…",
            )

        target_role = st.text_input(
            "Target role",
            placeholder="e.g. Product Manager",
        )
        job_description = st.text_area(
            "Job description (optional)",
            height=140,
            placeholder="Paste the job description for a closer match.",
        )

        analyze = st.button("Analyze Resume", type="primary", use_container_width=True)
        if analyze:
            if not resume_text.strip() or not target_role.strip():
                st.warning("Add your resume and a target role, then analyze again.")
            else:
                st.session_state.pending_analysis = {
                    "resume_text": resume_text,
                    "target_role": target_role,
                    "job_description": job_description,
                }
                st.session_state.analysis = None
                st.session_state.analysis_error = None

with right:
    with st.container(key="result-card"):
        st.markdown('<p class="card-kicker">Analysis</p>', unsafe_allow_html=True)

        pending = st.session_state.pending_analysis
        if pending:
            st.markdown(
                """
                <div class="loading-box">
                    <div class="loading-spinner"></div>
                    <p>Analyzing your resume…</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.spinner("Analyzing your resume…"):
                try:
                    st.session_state.analysis = analyze_resume(
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

        if st.session_state.analysis:
            st.markdown(
                render_dashboard(st.session_state.analysis),
                unsafe_allow_html=True,
            )
        elif st.session_state.analysis_error:
            st.error(f"Analysis failed: {st.session_state.analysis_error}")
        else:
            st.markdown(
                """
                <div class="placeholder">
                    <div class="placeholder-mark">✦</div>
                    <p>Your analysis will appear here.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
