"""PDF de la lettre (docs/25 §3.4) : texte échappé, caractères hors police remplacés."""

import io
from datetime import date

from pypdf import PdfReader

from jobbot.letters.document import Identity, Recipient, assemble
from jobbot.letters.pdf import TEMPLATES, letter_to_pdf


def test_letter_pdf_escapes_markup_and_odd_characters() -> None:
    letter = assemble(
        Identity(name="Jean Exemple", street="Rue 1", postcode="1020", city="Renens"),
        Recipient("A&B <SA>"),
        "fr",
        "Candidature — DevOps",
        ["Kubernetes & Terraform <b>pas du gras</b>, très motivé\u2011e 🚀."],
        date(2026, 10, 7),
    )
    pdf = letter_to_pdf(letter)
    reader = PdfReader(io.BytesIO(pdf))
    text = reader.pages[0].extract_text()
    assert "A&B <SA>" in text and "<b>pas du gras</b>" in text
    assert "motivé-e" in text and "Renens, le 7 octobre 2026" in text
    assert reader.metadata is not None and reader.metadata.title == "Lettre"


def test_letter_pdf_in_each_template() -> None:
    """Les quatre modèles (maquette Preparer) : le même texte, le nom en tête hors du sobre."""
    letter = assemble(
        Identity(name="Jean Exemple", street="Rue 1", postcode="1020", city="Renens"),
        Recipient("Acme SA"),
        "fr",
        "Candidature",
        ["Kubernetes et Terraform."],
        date(2026, 10, 7),
    )
    pages = {t: letter_to_pdf(letter, template=t) for t in TEMPLATES}
    for template, pdf in pages.items():
        text = PdfReader(io.BytesIO(pdf)).pages[0].extract_text()
        assert "Kubernetes et Terraform." in text, template
        # Le nom une fois dans l'expéditeur ; deux fois quand le modèle le met en tête.
        assert text.count("Jean Exemple") >= (2 if template == "sobre" else 3), template
    assert len(set(pages.values())) == 4
    # Times pour le classique.
    assert b"Times-Roman" in pages["classique"] and b"Times-Roman" not in pages["sobre"]
