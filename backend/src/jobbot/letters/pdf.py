"""Lettre et CV en PDF (docs/25 §3.4), même contenu que le Word.

Les recruteurs et leurs outils de candidature préfèrent le PDF. Police Helvetica (proche de
l'Arial du Word), sans fichier de police à embarquer : elle couvre le français et l'allemand.

Quatre modèles, les mêmes pour la lettre et le CV (maquette Preparer, 2026-11-05) : « sobre » (la
mise en page d'origine, celle du Word), « moderne » (une bande bleue à gauche, le nom en bleu),
« bandeau » (un bandeau pêche en haut, le nom dedans) et « classique » (Times, le nom centré sur
un filet).
"""

import io
import unicodedata
from typing import Literal
from xml.sax.saxutils import escape

from reportlab.lib.colors import Color
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Flowable, HRFlowable, Paragraph, SimpleDocTemplate, Spacer

from jobbot.letters.cv_document import CvDocument
from jobbot.letters.document import LetterDocument

ACCENT = Color(0x3A / 255, 0x33 / 255, 0xC9 / 255)
# Les couleurs des modèles, celles de la maquette (docs/mobile/tokens.css : primary, peach, ink).
PRIMARY = Color(0x24 / 255, 0x45 / 255, 0xC2 / 255)
PEACH = Color(0xF3 / 255, 0xB0 / 255, 0x8A / 255)
INK = Color(0x1B / 255, 0x1F / 255, 0x2A / 255)

Template = Literal["sobre", "moderne", "bandeau", "classique"]
TEMPLATES: tuple[Template, ...] = ("sobre", "moderne", "bandeau", "classique")
BAND = 0.5 * cm  # la bande du modèle moderne
HEADER = 2.6 * cm  # le bandeau du modèle bandeau
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


def _fonts(template: Template) -> tuple[str, str]:
    """La police du texte et celle du gras : Times pour le classique, Helvetica sinon."""
    return (
        ("Times-Roman", "Times-Bold")
        if template == "classique"
        else ("Helvetica", "Helvetica-Bold")
    )


def _decorate(template: Template):  # type: ignore[no-untyped-def]
    """Ce que le modèle dessine sur chaque page, sous le texte : la bande ou le bandeau."""

    def draw(canvas: Canvas, _doc: SimpleDocTemplate) -> None:
        width, height = A4
        canvas.saveState()
        if template == "moderne":
            canvas.setFillColor(PRIMARY)
            canvas.rect(0, 0, BAND, height, stroke=0, fill=1)
        elif template == "bandeau" and canvas.getPageNumber() == 1:
            canvas.setFillColor(PEACH)
            canvas.rect(0, height - HEADER, width, HEADER, stroke=0, fill=1)
        canvas.restoreState()

    return draw


def _build(
    story: list[Flowable], *, title: str, margins: tuple[float, float], template: Template = "sobre"
) -> bytes:
    buffer = io.BytesIO()
    side, top = margins
    draw = _decorate(template)
    SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=side + (BAND if template == "moderne" else 0),
        rightMargin=side,
        topMargin=top,
        bottomMargin=top,
        title=title,
        author="",
        creator="jobA1",
    ).build(story, onFirstPage=draw, onLaterPages=draw)
    return buffer.getvalue()


def _name_block(name: str, sub: str | None, template: Template, size: float) -> list[Flowable]:
    """Le nom en tête, à la manière du modèle (le sobre garde le nom dans l'expéditeur)."""
    regular, bold = _fonts(template)
    color = PRIMARY if template == "moderne" else INK
    align = TA_CENTER if template == "classique" else TA_LEFT
    style = ParagraphStyle(
        "name", fontName=bold, fontSize=size, leading=size * 1.2, textColor=color, alignment=align
    )
    small = ParagraphStyle(
        "sub",
        fontName=regular,
        fontSize=10,
        leading=13,
        textColor=color if template == "moderne" else MUTED,
        alignment=align,
    )
    blocks: list[Flowable] = [Paragraph(_text(name), style)]
    if sub:
        blocks.append(Paragraph(_text(sub), small))
    if template == "classique":
        blocks.append(Spacer(1, 4))
        blocks.append(HRFlowable(width="100%", thickness=0.8, color=INK))
    # Le bandeau : le texte reprend sous la bande pêche.
    blocks.append(Spacer(1, 1.0 * cm if template == "bandeau" else 14))
    return blocks


def letter_to_pdf(
    letter: LetterDocument, title: str = "Lettre", template: Template = "sobre"
) -> bytes:
    """Lettre A4, mise en page suisse : destinataire à droite."""
    regular, _bold = _fonts(template)
    base = ParagraphStyle("base", fontName=regular, fontSize=11, leading=14.5)
    right = ParagraphStyle("right", parent=base, leftIndent=9 * cm)
    # Jamais justifiée (WCAG 1.4.8) : les espaces inégaux gênent la lecture.
    body = ParagraphStyle("body", parent=base, alignment=TA_LEFT, spaceAfter=10)
    story: list[Flowable] = []
    if template != "sobre" and letter.sender:
        story += _name_block(letter.sender[0], None, template, 16)

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
    top = 0.9 * cm if template == "bandeau" else 2 * cm
    return _build(story, title=title, margins=(2.5 * cm, top), template=template)


def cv_to_pdf(cv: CvDocument, title: str = "CV", template: Template = "sobre") -> bytes:
    regular, bold = _fonts(template)
    accent = ACCENT if template == "sobre" else PRIMARY if template == "moderne" else INK
    base = ParagraphStyle("base", fontName=regular, fontSize=10, leading=13)
    name = ParagraphStyle("name", parent=base, fontName=bold, fontSize=20, leading=24)
    headline = ParagraphStyle("headline", parent=base, fontSize=12, leading=16, textColor=accent)
    contacts = ParagraphStyle(
        "contacts", parent=base, fontSize=9, leading=12, textColor=MUTED, spaceAfter=8
    )
    heading = ParagraphStyle(
        "heading",
        parent=base,
        fontName=bold,
        fontSize=10.5,
        textColor=accent,
        spaceBefore=10,
        spaceAfter=3,
    )
    item_title = ParagraphStyle("item", parent=base, fontName=bold, spaceBefore=3)
    item = ParagraphStyle("content", parent=base, spaceAfter=3)
    story: list[Flowable]
    if template == "sobre":
        story = [Paragraph(_text(cv.name), name)]
        if cv.headline:
            story.append(Paragraph(_text(cv.headline), headline))
    else:
        story = [*_name_block(cv.name, cv.headline, template, 20)[:-1], Spacer(1, 6)]
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
    top = 0.7 * cm if template == "bandeau" else 1.6 * cm
    return _build(story, title=title, margins=(2 * cm, top), template=template)
