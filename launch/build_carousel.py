"""Build a LinkedIn carousel PDF (1080x1350) for Resume Analyser launch."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import portrait
from reportlab.pdfgen import canvas

W, H = 1080, 1350
PAGE = portrait((W, H))
OUT = Path(__file__).with_name("ResumeAnalyser_Launch_Carousel.pdf")

INK = HexColor("#0f1419")
MUTED = HexColor("#5a6670")
ACCENT = HexColor("#2a6a66")
SOFT = HexColor("#e7eeef")
CARD = HexColor("#f4f8f7")
LINE = HexColor("#d5e3e0")

HANDLE = "@ashishjain93"
URL = "resumefit-analyser.streamlit.app"

SLIDES = [
    {
        "kicker": "01 / 10",
        "title": "Stop rewriting\nyour resume\nfrom scratch.",
        "body": "Paste the JD. Get a fitted pack.",
        "cover": True,
    },
    {
        "kicker": "02 / 10",
        "title": "The real problem",
        "body": "Most resumes fail ATS before a human ever opens them. Not because you are underqualified. Because the keywords never landed.",
    },
    {
        "kicker": "03 / 10",
        "title": "What I built",
        "body": "Resume Analyser: an AI pack that scores your resume against a real job description, then upgrades it without deleting your history.",
    },
    {
        "kicker": "04 / 10",
        "title": "Works with screenshots",
        "body": "Paste a Naukri or LinkedIn JD screenshot. Upload a resume PDF or image. No neat text file required.",
    },
    {
        "kicker": "05 / 10",
        "title": "You get 6 things",
        "body": "1 ATS score\n2 Missing keywords\n3 Updated full resume\n4 Five PDF templates\n5 Cover letter\n6 India Tier-1/2/3 salary bands",
    },
    {
        "kicker": "06 / 10",
        "title": "Nothing gets trimmed",
        "body": "Your roles stay. Your projects stay. Keywords are woven in. The PDF can span pages if it needs to.",
    },
    {
        "kicker": "07 / 10",
        "title": "Built for India",
        "body": "Salary bands by Tier-1, Tier-2 and Tier-3 cities, so you know what the role usually pays before you apply.",
    },
    {
        "kicker": "08 / 10",
        "title": "Stay while it builds",
        "body": "Live checklist. Rotating icons. Progress you can see. No guessing if it froze.",
    },
    {
        "kicker": "09 / 10",
        "title": "Recap",
        "body": "Screenshot JD\nUpload resume\nGet ATS + keywords\nDownload fitted resume\nSend cover letter\nCheck India salary",
    },
    {
        "kicker": "10 / 10",
        "title": "Try it free",
        "body": URL,
        "cta": True,
    },
]


def draw_bg(c: canvas.Canvas) -> None:
    c.setFillColor(SOFT)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(HexColor("#d7e8e5"))
    c.circle(180, 1180, 260, fill=1, stroke=0)
    c.setFillColor(HexColor("#cfe0e4"))
    c.circle(980, 180, 300, fill=1, stroke=0)


def draw_footer(c: canvas.Canvas, kicker: str) -> None:
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 22)
    c.drawString(72, 58, HANDLE)
    c.drawRightString(W - 72, 58, kicker)


def wrap(c: canvas.Canvas, text: str, x: float, y: float, font: str, size: int, leading: int, max_width: float, color=INK) -> float:
    c.setFillColor(color)
    c.setFont(font, size)
    for paragraph in text.split("\n"):
        words = paragraph.split() if paragraph.strip() else [""]
        line = ""
        for word in words:
            trial = word if not line else f"{line} {word}"
            if c.stringWidth(trial, font, size) <= max_width:
                line = trial
            else:
                c.drawString(x, y, line)
                y -= leading
                line = word
        c.drawString(x, y, line)
        y -= leading + 8
    return y


def build() -> Path:
    c = canvas.Canvas(str(OUT), pagesize=PAGE)
    for slide in SLIDES:
        draw_bg(c)
        draw_footer(c, slide["kicker"])

        c.setFillColor(ACCENT)
        c.setFont("Helvetica-Bold", 24)
        c.drawString(72, H - 90, "RESUME ANALYSER")

        if slide.get("cover"):
            y = wrap(c, slide["title"], 72, H - 280, "Helvetica-Bold", 64, 72, W - 150)
            wrap(c, slide["body"], 72, y - 20, "Helvetica", 30, 40, W - 160, MUTED)
            c.setFillColor(ACCENT)
            c.roundRect(72, 160, 360, 64, 18, fill=1, stroke=0)
            c.setFillColor(white)
            c.setFont("Helvetica-Bold", 24)
            c.drawCentredString(72 + 180, 182, "Swipe to see how →")
        elif slide.get("cta"):
            wrap(c, slide["title"], 72, H - 340, "Helvetica-Bold", 64, 72, W - 150)
            c.setFillColor(CARD)
            c.roundRect(72, 520, W - 144, 160, 28, fill=1, stroke=0)
            c.setStrokeColor(LINE)
            c.setLineWidth(2)
            c.roundRect(72, 520, W - 144, 160, 28, fill=0, stroke=1)
            c.setFillColor(ACCENT)
            c.setFont("Helvetica-Bold", 28)
            c.drawCentredString(W / 2, 595, slide["body"])
            wrap(
                c,
                "Comment RESUME and I will share the link.\nOr open the app and test it with your own JD.",
                72,
                430,
                "Helvetica",
                28,
                38,
                W - 160,
                MUTED,
            )
        else:
            wrap(c, slide["title"], 72, H - 300, "Helvetica-Bold", 54, 62, W - 150)
            # card body
            c.setFillColor(CARD)
            c.roundRect(72, 220, W - 144, 520, 28, fill=1, stroke=0)
            wrap(c, slide["body"], 110, 680, "Helvetica", 30, 42, W - 230, INK)

        c.showPage()
    c.save()
    return OUT


if __name__ == "__main__":
    path = build()
    print(path, path.stat().st_size)
