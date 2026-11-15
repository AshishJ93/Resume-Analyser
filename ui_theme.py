"""Cinematic visual system for Resume Analyser (Streamlit-safe CSS)."""

STYLE_HTML = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

:root {
  --ink: #0f1419;
  --muted: #5a6670;
  --line: #dde3e8;
  --accent: #0f6b4c;
  --accent-2: #c45c14;
  --accent-soft: #e7f3ee;
  --saffron: #e07a2f;
  --india-green: #0f6b4c;
  --india-navy: #0b3a5b;
  --warn: #9a7040;
  --bad: #a84848;
  --shadow: 0 24px 60px rgba(15, 20, 25, 0.08);
}

#MainMenu, footer,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] {
  visibility: hidden;
  height: 0;
}

/* —— Living aurora background (CSS-only, survives Streamlit reloads) —— */
html, body {
  background: #e7eeef !important;
}

[data-testid="stAppViewContainer"],
.stApp {
  background: #e7eeef !important;
  color: var(--ink);
  font-family: "Manrope", sans-serif;
}

/* Calm living backdrop only — always behind UI, never competing with upload path */
[data-testid="stAppViewContainer"]::before,
.stApp::before {
  content: "";
  position: fixed !important;
  inset: 0;
  z-index: 0;
  pointer-events: none !important;
  background:
    radial-gradient(ellipse 58% 46% at 8% 4%, rgba(224,122,47,0.16), transparent 58%),
    radial-gradient(ellipse 54% 44% at 92% 8%, rgba(15,107,76,0.22), transparent 58%),
    radial-gradient(ellipse 46% 36% at 78% 92%, rgba(11,58,91,0.10), transparent 60%),
    radial-gradient(ellipse 40% 32% at 16% 80%, rgba(15,20,25,0.04), transparent 65%),
    linear-gradient(165deg, #efe8e0 0%, #f5f7f5 48%, #e9efeb 100%);
  background-size: 135% 135%, 125% 125%, 140% 140%, 120% 120%, 100% 100%;
  animation: auroraShift 22s ease-in-out infinite alternate;
}

[data-testid="stAppViewContainer"]::after,
.stApp::after {
  content: "";
  position: fixed !important;
  inset: -10%;
  z-index: 0;
  pointer-events: none !important;
  opacity: 0.14;
  background:
    linear-gradient(115deg, transparent 0 38%, rgba(255,255,255,0.55) 38% 39%, transparent 39% 100%),
    linear-gradient(155deg, transparent 0 62%, rgba(42,106,102,0.07) 62% 63%, transparent 63% 100%),
    radial-gradient(circle at 30% 40%, rgba(255,255,255,0.35), transparent 28%),
    radial-gradient(circle at 78% 30%, rgba(255,255,255,0.25), transparent 22%);
  filter: blur(18px);
  animation: softVeil 28s ease-in-out infinite alternate;
}

[data-testid="stHeader"] {
  background: transparent !important;
}

[data-testid="stMain"],
section.main,
.main,
.block-container {
  position: relative;
  z-index: 3;
}

/* Hide any leftover paper-sky from older deploys */
#ra-paper-sky,
.paper-sky,
.fly-sheet,
.fly-chip {
  display: none !important;
}

.block-container {
  max-width: 1120px;
  padding-top: 1.75rem;
  padding-bottom: 4rem;
}

/* —— Cinematic hero —— */
.brand-hero {
  min-height: min(52vh, 420px);
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  margin: 0 0 1.6rem;
  padding: 1.2rem 0 1.5rem;
  animation: rise 0.8s cubic-bezier(.22,1,.36,1) both;
}

.usage-banner {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
  margin: 0.85rem 0 0.35rem;
  padding: 0;
  background: transparent;
  border: 0;
}

.usage-banner--step {
  margin-top: 0.95rem;
  padding-top: 0.85rem;
  border-top: 1px solid rgba(15, 20, 25, 0.08);
}

.usage-banner--download {
  margin: 0.75rem 0 0.9rem;
  padding: 0.7rem 0 0;
  border-top: 1px solid rgba(15, 20, 25, 0.08);
}

.usage-meters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem 1.1rem;
}

.usage-meter {
  display: inline-flex;
  align-items: center;
  gap: 0.65rem;
  min-width: 0;
}

.usage-ring {
  --usage-pct: 100;
  position: relative;
  flex: 0 0 auto;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: conic-gradient(
    var(--india-green) 0% calc(var(--usage-pct) * 1%),
    rgba(15, 20, 25, 0.08) calc(var(--usage-pct) * 1%) 100%
  );
  box-shadow: 0 6px 16px rgba(15, 107, 76, 0.10);
  transition: background 0.35s ease, box-shadow 0.35s ease, opacity 0.35s ease;
}

.usage-ring-core {
  position: absolute;
  inset: 5px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: #f7faf8;
  color: var(--india-navy);
  font-family: "Space Grotesk", sans-serif;
  line-height: 1;
}

.usage-count {
  display: block;
  font-size: 1.2rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  text-align: center;
  transform: translateY(0.5px);
}

.usage-spent {
  display: block;
  font-size: 1.15rem;
  font-weight: 600;
  color: rgba(15, 20, 25, 0.28);
  letter-spacing: 0;
}

.usage-meta {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  min-width: 0;
}

.usage-label {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--india-navy);
}

.usage-status {
  font-size: 0.78rem;
  color: var(--muted);
}

.usage-slots {
  display: flex;
  gap: 4px;
  margin-top: 0.18rem;
}

.usage-slot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 1.5px solid rgba(15, 107, 76, 0.35);
  background: transparent;
  transition: background 0.25s ease, border-color 0.25s ease, transform 0.25s ease;
}

.usage-slot.is-on {
  background: var(--india-green);
  border-color: var(--india-green);
}

.usage-slot.is-off {
  background: transparent;
  border-color: rgba(15, 20, 25, 0.18);
  border-style: dashed;
}

.usage-note {
  margin: 0;
  color: var(--muted);
  font-size: 0.76rem;
  line-height: 1.4;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Exhausted: punched ticket — dashed ghost ring + empty marks, not a red disc */
.usage-meter.is-empty .usage-ring {
  background: transparent;
  border: 1.5px dashed rgba(15, 20, 25, 0.22);
  box-shadow: none;
  opacity: 0.92;
}

.usage-meter.is-empty .usage-ring-core {
  background: rgba(255, 255, 255, 0.55);
  box-shadow: inset 0 0 0 1px rgba(15, 20, 25, 0.04);
}

.usage-meter.is-empty .usage-label {
  color: var(--muted);
  text-decoration: line-through;
  text-decoration-thickness: 1px;
  text-decoration-color: rgba(15, 20, 25, 0.28);
}

.usage-meter.is-empty .usage-status {
  color: var(--saffron);
  font-weight: 650;
}

.usage-meter.is-empty .usage-slot.is-off {
  border-color: rgba(224, 122, 47, 0.45);
}

.usage-note.is-done {
  color: #9a5a22;
  font-weight: 600;
}

.india-badge-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  margin: 0 0 1rem;
}

.brand-kicker,
.made-in-india {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  width: fit-content;
  padding: 0.35rem 0.85rem;
  border-radius: 999px;
  background: rgba(255,255,255,0.62);
  backdrop-filter: blur(10px);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.brand-kicker {
  border: 1px solid rgba(15,107,76,0.22);
  color: var(--india-green);
}

.made-in-india {
  border: 1px solid rgba(224,122,47,0.28);
  color: #9a4d12;
}

.tricolor-dot {
  display: inline-flex;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  overflow: hidden;
  box-shadow: inset 0 0 0 1px rgba(15,20,25,0.08);
  background:
    linear-gradient(#ff9933 0 33%, #ffffff 33% 66%, #138808 66% 100%);
  flex-shrink: 0;
}

.brand-mark {
  font-family: "Space Grotesk", sans-serif;
  font-size: clamp(3rem, 7vw, 5.2rem);
  font-weight: 700;
  letter-spacing: -0.055em;
  line-height: 0.98;
  color: var(--ink);
  margin: 0;
  max-width: 12ch;
}

.brand-mark span {
  background: linear-gradient(120deg, #0f6b4c, #c45c14 55%, #0b3a5b);
  background-size: 200% 100%;
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  animation: sheen 8s ease-in-out infinite;
}

.brand-sub {
  margin: 1.1rem 0 0;
  max-width: 32rem;
  color: var(--muted);
  font-size: 1.12rem;
  line-height: 1.55;
  animation: rise 1s cubic-bezier(.22,1,.36,1) both;
}

.tricolor-rule {
  width: min(220px, 55%);
  height: 4px;
  margin: 1rem 0 0;
  border-radius: 999px;
  background: linear-gradient(90deg, #ff9933 0 33%, #ffffff 33% 66%, #138808 66% 100%);
  box-shadow: 0 0 0 1px rgba(15,20,25,0.06);
}

.india-footer {
  margin-top: 2rem;
  padding: 1rem 1.15rem;
  border-radius: 18px;
  background: rgba(255,255,255,0.7);
  border: 1px solid rgba(15,20,25,0.06);
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: var(--muted);
  font-size: 0.92rem;
  line-height: 1.45;
}

.india-footer strong {
  color: var(--ink);
  font-family: "Space Grotesk", sans-serif;
  letter-spacing: -0.02em;
}

.story-strip {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0;
  margin: 0 0 1.75rem;
  border-top: 1px solid rgba(15,20,25,0.08);
  border-bottom: 1px solid rgba(15,20,25,0.08);
  animation: rise 1.05s cubic-bezier(.22,1,.36,1) both;
}

.story-beat {
  padding: 1.25rem 1.1rem 1.35rem;
  border-right: 1px solid rgba(15,20,25,0.08);
}

.story-beat:last-child { border-right: none; }

.story-beat strong {
  display: block;
  font-family: "Space Grotesk", sans-serif;
  font-size: 1.35rem;
  letter-spacing: -0.03em;
  margin-bottom: 0.35rem;
}

.story-beat span {
  color: var(--muted);
  font-size: 0.9rem;
  line-height: 1.45;
}

.section-label {
  margin: 0 0 0.35rem;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--accent);
}

.panel-title {
  margin: 0 0 0.25rem;
  font-family: "Space Grotesk", sans-serif;
  font-size: 1.25rem;
  letter-spacing: -0.025em;
  color: var(--ink);
}

.hint-line {
  margin: 0 0 0.85rem;
  color: var(--muted);
  font-size: 0.9rem;
  line-height: 1.45;
}

.st-key-resume-panel,
.st-key-jd-panel,
.st-key-target-panel,
.st-key-resume-result-panel,
.st-key-templates-panel,
.st-key-cover-panel,
.st-key-score-panel,
.st-key-keywords-panel,
.st-key-salary-panel,
.st-key-empty-panel {
  background: rgba(255,255,255,0.72);
  border: 1px solid rgba(255,255,255,0.65);
  border-radius: 24px;
  padding: 1.35rem 1.4rem 1.45rem;
  box-shadow: var(--shadow);
  backdrop-filter: blur(16px);
  animation: rise 0.75s cubic-bezier(.22,1,.36,1) both;
}

/* —— Buffering forge stage —— */
.buffer-stage {
  margin: 0 0 1.2rem;
  padding: 1.5rem 1.5rem 1.55rem;
  border-radius: 28px;
  background: rgba(255,255,255,0.78);
  border: 1px solid rgba(255,255,255,0.7);
  box-shadow: var(--shadow);
  backdrop-filter: blur(18px);
  animation: rise 0.55s cubic-bezier(.22,1,.36,1) both;
}

.buffer-stage.is-done {
  background: linear-gradient(145deg, rgba(255,255,255,0.88), rgba(230,241,240,0.9));
}

.buffer-layout {
  display: grid;
  grid-template-columns: 1.05fr 1.2fr;
  gap: 1.4rem;
  align-items: center;
  margin-bottom: 1.15rem;
}

.forge-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.forge-ring {
  position: relative;
  width: 168px;
  height: 168px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background:
    conic-gradient(from 210deg, rgba(42,106,102,0.15), rgba(42,106,102,0.75), rgba(58,125,140,0.35), rgba(42,106,102,0.15));
  animation: ringSpin 10s linear infinite;
}

.buffer-stage.is-done .forge-ring { animation: none; }

.forge-core {
  position: relative;
  width: 128px;
  height: 128px;
  border-radius: 50%;
  background: #f7faf9;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: inset 0 0 0 1px #d7e4e1;
}

.forge-halo {
  position: absolute;
  inset: 10px;
  border-radius: 50%;
  border: 1px dashed rgba(42,106,102,0.35);
  animation: ringSpin 14s linear infinite reverse;
}

.forge-core span {
  font-size: 1.6rem;
  color: var(--accent);
  animation: iconFloat 2.6s ease-in-out infinite;
}

.forge-core em {
  margin-top: 0.2rem;
  font-style: normal;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #5f726d;
}

.icon-orbit {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
  width: 100%;
}

.spin-icon {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  padding: 0.65rem 0.3rem 0.55rem;
  border-radius: 14px;
  background: rgba(238,243,241,0.95);
  border: 1px solid #d5e3e0;
}

.spin-icon span {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: #fff;
  color: var(--accent);
  font-size: 0.95rem;
  font-weight: 700;
  animation: iconSpin 5.5s linear infinite, iconFloat 2.8s ease-in-out infinite;
  animation-delay: calc(var(--i) * -0.55s), calc(var(--i) * 0.15s);
}

.spin-icon em {
  font-style: normal;
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #5f726d;
}

.buffer-stage.is-done .spin-icon span {
  animation: iconFloat 3s ease-in-out infinite;
  background: var(--accent-soft);
}

.buffer-title {
  margin: 0;
  font-family: "Space Grotesk", sans-serif;
  font-size: clamp(1.45rem, 2.5vw, 1.9rem);
  letter-spacing: -0.035em;
  line-height: 1.15;
}

.buffer-support {
  margin: 0.45rem 0 0.95rem;
  color: var(--muted);
  font-size: 0.98rem;
  line-height: 1.5;
  max-width: 34rem;
}

.punch-stage {
  display: grid;
  place-items: center;
  min-height: 7rem;
  margin: 0 0 0.95rem;
  padding: 1.15rem 1.25rem;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(42,106,102,0.10), rgba(58,125,140,0.07));
  border: 1px solid #c9ddd9;
  overflow: hidden;
}

.punch {
  grid-area: 1 / 1;
  width: 100%;
  margin: 0;
  text-align: center;
  font-family: "Space Grotesk", sans-serif;
  font-size: clamp(1.05rem, 2.1vw, 1.28rem);
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1.35;
  color: #152422;
  opacity: 0;
  animation: punchCycle 32s infinite;
}

.punch:nth-child(1) { animation-delay: 0s; }
.punch:nth-child(2) { animation-delay: 4s; }
.punch:nth-child(3) { animation-delay: 8s; }
.punch:nth-child(4) { animation-delay: 12s; }
.punch:nth-child(5) { animation-delay: 16s; }
.punch:nth-child(6) { animation-delay: 20s; }
.punch:nth-child(7) { animation-delay: 24s; }
.punch:nth-child(8) { animation-delay: 28s; }

.buffer-stage.is-done .punch { animation: none; opacity: 0; }
.buffer-stage.is-done .punch:first-child {
  opacity: 1;
}

.forge-meter {
  height: 6px;
  border-radius: 999px;
  background: #e1eae8;
  overflow: hidden;
}

.forge-meter-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #2a6a66, #3a7d8c);
  transition: width 0.6s ease;
}

.forge-meter-label {
  margin: 0.45rem 0 0;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #6a7a76;
}

.check-board { margin-top: 0.2rem; }
.check-sub {
  margin: 0 0 0.75rem;
  color: var(--muted);
  font-size: 0.86rem;
  line-height: 1.45;
}
.check-list { display: grid; gap: 0.48rem; }
.check-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.82rem 0.95rem;
  border-radius: 14px;
  background: #eef3f1;
  color: #1c2422;
  font-size: 0.95rem;
  font-weight: 600;
  box-shadow: inset 3px 0 0 #c5d5d0;
  transition: background 0.25s ease, transform 0.25s ease;
}
.check-row.pending { opacity: 0.72; }
.check-row.active {
  background: #e4efec;
  box-shadow: inset 3px 0 0 var(--accent);
  transform: translateX(2px);
}
.check-row.done {
  background: #e7f2f0;
  box-shadow: inset 3px 0 0 var(--accent);
}
.check-mark {
  width: 1.35rem;
  flex-shrink: 0;
  text-align: center;
  font-family: "Space Grotesk", sans-serif;
  font-weight: 700;
  color: #334843;
}
.check-row.done .check-mark,
.check-row.active .check-mark { color: var(--accent); }
.check-row.active .check-mark { animation: pulse 1.2s ease-in-out infinite; }

.results-hero {
  display: grid;
  grid-template-columns: 150px 1fr;
  gap: 1.2rem;
  align-items: center;
  padding: 1.3rem 1.4rem;
  border-radius: 26px;
  background: rgba(255,255,255,0.8);
  border: 1px solid rgba(255,255,255,0.7);
  box-shadow: var(--shadow);
  backdrop-filter: blur(14px);
  margin-bottom: 1rem;
  animation: rise 0.6s cubic-bezier(.22,1,.36,1) both;
}
.results-hero h2 {
  margin: 0;
  font-family: "Space Grotesk", sans-serif;
  font-size: clamp(1.4rem, 2.5vw, 1.75rem);
  letter-spacing: -0.03em;
}
.results-hero p {
  margin: 0.45rem 0 0;
  color: var(--muted);
  line-height: 1.5;
}

.pack-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
  margin: 0 0 1rem;
}
.pack-card {
  border-radius: 18px;
  padding: 1.05rem 1.05rem;
  background: rgba(255,255,255,0.78);
  border: 1px solid rgba(255,255,255,0.7);
  box-shadow: 0 12px 30px rgba(15,20,25,0.05);
  min-height: 108px;
  transition: transform 0.25s ease, border-color 0.25s ease;
}
.pack-card:hover {
  transform: translateY(-3px);
  border-color: #b7d4d1;
}
.pack-card .idx {
  font-family: "Space Grotesk", sans-serif;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--accent);
  margin-bottom: 0.4rem;
}
.pack-card h4 {
  margin: 0;
  font-family: "Space Grotesk", sans-serif;
  font-size: 1.08rem;
  letter-spacing: -0.02em;
}
.pack-card p {
  margin: 0.3rem 0 0;
  color: var(--muted);
  font-size: 0.82rem;
  line-height: 1.35;
}

.score-wrap {
  display: grid;
  grid-template-columns: 132px 1fr;
  gap: 1.15rem;
  align-items: center;
}
.gauge {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  display: grid;
  place-items: center;
}
.gauge-inner {
  width: 90px;
  height: 90px;
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
  font-size: 1.95rem;
  font-weight: 700;
  line-height: 1;
  letter-spacing: -0.04em;
}
.gauge-caption {
  margin-top: 0.22rem;
  font-size: 0.66rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #95a0ab;
}
.score-meta h3 {
  margin: 0;
  font-family: "Space Grotesk", sans-serif;
  font-size: 1.25rem;
  letter-spacing: -0.025em;
}
.score-meta p {
  margin: 0.5rem 0 0;
  color: var(--muted);
  line-height: 1.55;
}
.pill {
  display: inline-flex;
  margin-top: 0.55rem;
  padding: 0.28rem 0.72rem;
  border-radius: 999px;
  font-size: 0.74rem;
  font-weight: 700;
}
.chip-row { display: flex; flex-wrap: wrap; gap: 0.45rem; }
.chip {
  display: inline-flex;
  padding: 0.4rem 0.78rem;
  border-radius: 999px;
  background: var(--accent-soft);
  color: #215652;
  border: 1px solid #cfe3e1;
  font-size: 0.82rem;
  font-weight: 600;
}
.insight-row {
  display: flex;
  gap: 0.65rem;
  padding: 0.72rem 0.82rem;
  border-radius: 12px;
  margin-bottom: 0.45rem;
  background: #f7f8fa;
  border-left: 3px solid transparent;
  font-size: 0.92rem;
  line-height: 1.45;
}
.insight-row.strength { background: #eef7f3; border-left-color: #2a6a66; }
.insight-row.improvement { background: #f8f3eb; border-left-color: #9a7040; }
.split-two {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.8rem;
  margin-top: 1rem;
}
.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(168px, 1fr));
  gap: 0.7rem;
  margin: 0.2rem 0 0.9rem;
}
.template-card {
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 0.9rem 0.95rem;
  background: linear-gradient(180deg, #ffffff 0%, #f6f8f9 100%);
  min-height: 108px;
  transition: transform 0.22s ease, border-color 0.22s ease;
}
.template-card:hover {
  transform: translateY(-2px);
  border-color: #b7d4d1;
}
.template-card h4 {
  margin: 0;
  font-family: "Space Grotesk", sans-serif;
  font-size: 0.98rem;
}
.template-card p {
  margin: 0.38rem 0 0;
  color: var(--muted);
  font-size: 0.82rem;
  line-height: 1.4;
}
.cover-box, .resume-preview {
  white-space: pre-wrap;
  background: #f6f8f9;
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 1rem 1.1rem;
  line-height: 1.6;
  font-size: 0.92rem;
}
.resume-preview {
  max-height: 420px;
  overflow: auto;
  font-size: 0.88rem;
}
.empty-note { color: #95a0ab; font-size: 0.92rem; }
.placeholder {
  text-align: center;
  padding: 2.4rem 1rem 1.6rem;
  color: var(--muted);
}
.placeholder-mark {
  width: 56px;
  height: 56px;
  margin: 0 auto 0.85rem;
  border-radius: 18px;
  display: grid;
  place-items: center;
  background: var(--accent-soft);
  color: var(--accent);
  font-family: "Space Grotesk", sans-serif;
  font-weight: 700;
  font-size: 1.2rem;
  animation: pulse 2.4s ease-in-out infinite;
}
.salary-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
  margin-top: 0.75rem;
}
.salary-card {
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 0.95rem 1rem;
  background: linear-gradient(180deg, #ffffff 0%, #f6f8f9 100%);
}
.salary-card h4 {
  margin: 0;
  font-family: "Space Grotesk", sans-serif;
}
.salary-card .band {
  margin: 0.45rem 0 0.25rem;
  font-family: "Space Grotesk", sans-serif;
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--accent);
}
.salary-card p {
  margin: 0;
  color: var(--muted);
  font-size: 0.82rem;
  line-height: 1.4;
}

div.st-key-result-nav div[data-testid="stRadio"] label {
  background: rgba(255,255,255,0.85) !important;
  border: 1px solid var(--line) !important;
  border-radius: 999px !important;
  padding: 0.5rem 0.9rem !important;
  margin-right: 0.35rem !important;
  margin-bottom: 0.35rem !important;
}
div.st-key-result-nav div[data-testid="stRadio"] label p {
  font-size: 0.98rem !important;
  font-weight: 700 !important;
}

div[data-testid="stRadio"] label p { font-weight: 600; }
.stTextInput label, .stTextArea label, .stFileUploader label, .stRadio label {
  font-weight: 600 !important;
  color: var(--ink) !important;
}
.stTextInput input, .stTextArea textarea {
  border-radius: 14px !important;
  border-color: var(--line) !important;
  background: rgba(250,251,252,0.9) !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 1px var(--accent) !important;
}
div[data-testid="stFileUploader"] section {
  border-radius: 14px;
  border-color: #d5e3e1;
  background: rgba(250,251,252,0.9);
}
button[kind="primary"],
button[data-testid="stBaseButton-primary"] {
  background: linear-gradient(120deg, #0f6b4c, #c45c14) !important;
  border: none !important;
  border-radius: 14px !important;
  color: #fff !important;
  font-weight: 700 !important;
  padding: 0.72rem 1.05rem !important;
  transition: transform 0.18s ease, filter 0.18s ease !important;
}
button[kind="primary"]:hover,
button[data-testid="stBaseButton-primary"]:hover {
  filter: brightness(1.05) !important;
  transform: translateY(-1px) !important;
}

@keyframes auroraShift {
  0% { background-position: 0% 0%, 100% 0%, 80% 100%, 10% 80%, 0% 0%; transform: scale(1); }
  100% { background-position: 18% 12%, 78% 18%, 60% 86%, 24% 70%, 0% 0%; transform: scale(1.05); }
}
@keyframes softVeil {
  0% { transform: translate3d(0, 0, 0) scale(1); opacity: 0.12; }
  100% { transform: translate3d(-2%, 1.5%, 0) scale(1.04); opacity: 0.18; }
}
@keyframes sheen {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}
@keyframes rise {
  from { opacity: 0; transform: translateY(18px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.04); }
}
@keyframes ringSpin { to { transform: rotate(360deg); } }
@keyframes iconSpin { to { transform: rotate(360deg); } }
@keyframes iconFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}
@keyframes punchCycle {
  0%, 2% { opacity: 0; transform: translateY(12px); }
  6%, 11% { opacity: 1; transform: translateY(0); }
  15%, 100% { opacity: 0; transform: translateY(-10px); }
}

@media (max-width: 900px) {
  .brand-hero { min-height: auto; }
  .story-strip, .buffer-layout, .pack-grid, .salary-grid, .split-two,
  .score-wrap, .results-hero { grid-template-columns: 1fr; }
  .story-beat { border-right: none; border-bottom: 1px solid rgba(15,20,25,0.08); }
  .story-beat:last-child { border-bottom: none; }
  .punch-stage { min-height: 8rem; }
}
</style>
"""

# One-time cleanup for older deploys that mounted papers onto document.body
CLEANUP_OLD_PAPER_SKY = r"""
<script>
(function () {
  try {
    var doc = window.parent && window.parent.document ? window.parent.document : document;
    var win = window.parent && window.parent.document ? window.parent : window;
    var el = doc.getElementById("ra-paper-sky");
    if (el && el.parentNode) el.parentNode.removeChild(el);
    win.__raPaperSkyMounted = false;
  } catch (e) {}
})();
</script>
"""


def inject_styles(render_html) -> None:
    import streamlit.components.v1 as components

    render_html(STYLE_HTML)
    components.html(CLEANUP_OLD_PAPER_SKY, height=0, scrolling=False)
