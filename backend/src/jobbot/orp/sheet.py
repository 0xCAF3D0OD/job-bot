"""La feuille du rendez-vous ORP en PDF (docs/83 §4) : une page A4, à imprimer ou à envoyer.

Même police et mêmes précautions que les lettres (letters/pdf.py). Ton nom n'y figure que si tu
le demandes : c'est toi qui la remets.
"""

from datetime import datetime

from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Flowable, Paragraph, Spacer

from jobbot.core.orp import LOCAL_TZ
from jobbot.letters.document import MONTHS
from jobbot.letters.pdf import ACCENT, MUTED, _build, _text
from jobbot.orp.meeting import Preparation


def sheet_pdf(prep: Preparation, *, starts_at: datetime | None, name: str | None) -> bytes:
    base = ParagraphStyle("base", fontName="Helvetica", fontSize=10.5, leading=14)
    title = ParagraphStyle("title", parent=base, fontSize=16, leading=20, textColor=ACCENT)
    head = ParagraphStyle(
        "head", parent=base, fontName="Helvetica-Bold", fontSize=11.5, spaceBefore=10, spaceAfter=4
    )
    item = ParagraphStyle("item", parent=base, leftIndent=12, bulletIndent=0, spaceAfter=2)
    muted = ParagraphStyle("muted", parent=base, textColor=MUTED, fontSize=9.5)
    story: list[Flowable] = []
    heading = "Rendez-vous ORP"
    if starts_at is not None:
        when = starts_at.astimezone(LOCAL_TZ)
        heading += f" du {when.day} {MONTHS['fr'][when.month - 1]} {when.year}"
    story.append(Paragraph(_text(heading), title))
    if name:
        story.append(Paragraph(_text(name), muted))
    story.append(Spacer(1, 8))

    def section(label: str, lines: list[str]) -> None:
        if not lines:
            return
        story.append(Paragraph(_text(label), head))
        for line in lines:
            story.append(Paragraph(_text(line), item, bulletText="•"))

    section("Mon mois en bref", prep.summaries)
    section("Ce qui bloque", prep.blockers)
    section("Ce qui marche", [prep.works] if prep.works else [])
    section(
        f"Ce qui revient dans les offres et me manque ({prep.offers} offres bien notées, 3 mois)",
        [
            f"{m.skill} : demandé dans {m.count} offres"
            + (f" ; formation possible : {m.training_title}" if m.training_title else "")
            for m in prep.missing
        ],
    )
    section("Mes questions", [q.text for q in prep.questions if q.checked])
    section(
        "Mes obligations",
        [("Fait : " if o.done else "") + o.text for o in prep.obligations],
    )
    story.append(Spacer(1, 14))
    story.append(Paragraph(_text("Préparé avec jobA1, à partir de mes données."), muted))
    return _build(story, title=heading, margins=(2 * cm, 1.8 * cm))
