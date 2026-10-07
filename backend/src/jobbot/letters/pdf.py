"""Lettre et CV en PDF (docs/25 §3.4), même contenu et même mise en page que le Word.

Les recruteurs et leurs outils de candidature préfèrent le PDF. Police Helvetica (proche de
l'Arial du Word), sans fichier de police à embarquer : elle couvre le français et l'allemand.
"""

import io
import unicodedata
from xml.sax.saxutils import escape

from reportlab.lib.colors import Color
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate, Spacer

from jobbot.letters.cv_document import CvDocument
from jobbot.letters.document import LetterDocument

ACCENT = Color(0x3A / 255, 0x33 / 255, 0xC9 / 255)
MUTED = Color(0x55 / 255, 0x55 / 255, 0x66 / 255)
# Caractères hors de la police standard, remplacés par leur équivalent le plus proche.
REPLACEMENTS = {"\u2011": "-", "\u2012": "-", "\u2212": "-", "\u00a0": " ", "\u202f": " "}


def _text(value: str) -> str:
    """Texte sûr pour un paragraphe : balises échappées, caractères hors police remplacés."""
    value = "".join(REPLACEMENTS.get(c, c) for c in value)
    kept = []
    for char in value:
        try:
            char.encode("cp1252")
            kept.append(char)
        except UnicodeEncodeError:
            kept.append(
                unicodedata.normalize("NFKD", char).encode("cp1252", "ignore").decode("cp1252")
            )
    return escape("".join(kept))


def _lines(lines: list[str]) -> str:
    return "<br/>".join(_text(line) for line in lines)


def _build(story: list[Flowable], *, title: str, margins: tuple[float, float]) -> bytes:
    buffer = io.BytesIO()
    side, top = margins
    SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=side,
        rightMargin=side,
        topMargin=top,
        bottomMargin=top,
        title=title,
        author="",
        creator="job-bot",
    ).build(story)
    return buffer.getvalue()


def letter_to_pdf(letter: LetterDocument, title: str = "Lettre") -> bytes:
    """Lettre A4, mise en page suisse : destinataire à droite."""
    base = ParagraphStyle("base", fontName="Helvetica", fontSize=11, leading=14.5)
    right = ParagraphStyle("right", parent=base, leftIndent=9 * cm)
    body = ParagraphStyle("body", parent=base, alignment=TA_JUSTIFY, spaceAfter=10)
    story: list[Flowable] = []

    def block(lines: list[str], style: ParagraphStyle = base, after: float = 18) -> None:
        if lines:
            story.append(Paragraph(_lines(lines), style))
            story.append(Spacer(1, after))

    block(letter.sender)
    block(letter.recipient, right)
    block([letter.place_date], right, after=24)
    story.append(Paragraph(f"<b>{_text(letter.subject_line)}</b>", base))
    story.append(Spacer(1, 18))
    block([letter.salutation], after=12)
    for text in letter.paragraphs:
        story.append(Paragraph(_text(text), body))
    story.append(Spacer(1, 8))
    block([letter.closing], after=36)
    block([letter.signature], after=30)
    block([letter.enclosure], after=0)
    return _build(story, title=title, margins=(2.5 * cm, 2 * cm))


def cv_to_pdf(cv: CvDocument, title: str = "CV") -> bytes:
    base = ParagraphStyle("base", fontName="Helvetica", fontSize=10, leading=13)
    name = ParagraphStyle("name", parent=base, fontName="Helvetica-Bold", fontSize=20, leading=24)
    headline = ParagraphStyle("headline", parent=base, fontSize=12, leading=16, textColor=ACCENT)
    contacts = ParagraphStyle(
        "contacts", parent=base, fontSize=9, leading=12, textColor=MUTED, spaceAfter=8
    )
    heading = ParagraphStyle(
        "heading",
        parent=base,
        fontName="Helvetica-Bold",
        fontSize=10.5,
        textColor=ACCENT,
        spaceBefore=10,
        spaceAfter=3,
    )
    item_title = ParagraphStyle("item", parent=base, fontName="Helvetica-Bold", spaceBefore=3)
    item = ParagraphStyle("content", parent=base, spaceAfter=3)
    story: list[Flowable] = [Paragraph(_text(cv.name), name)]
    if cv.headline:
        story.append(Paragraph(_text(cv.headline), headline))
    story.append(Paragraph(_text(" · ".join(cv.contacts)), contacts))
    if cv.summary:
        story.append(Paragraph(_text(cv.summary_heading.upper()), heading))
        story.append(Paragraph(_text(cv.summary), base))
    for section in cv.sections:
        story.append(Paragraph(_text(section.heading.upper()), heading))
        for entry in section.items:
            if entry.title:
                story.append(Paragraph(_text(entry.title), item_title))
            content = "".join(
                f"<b>{_text(s.text)}</b>" if s.strong else _text(s.text) for s in entry.content
            )
            story.append(Paragraph(content.replace("\n", "<br/>"), item))
    return _build(story, title=title, margins=(2 * cm, 1.6 * cm))
