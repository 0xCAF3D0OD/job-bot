"""La lettre tient sur une page A4 (demande de Kevin du 6.11.2026).

Le PDF est construit dans le modèle choisi et ses pages comptées : la mise en page se resserre sans
l'IA, puis l'IA raccourcit avec une cible chiffrée, deux fois au plus. Chaque test compte les pages
du PDF réellement téléchargé, pas un nombre de mots.
"""

import io
import json
import re
from datetime import date
from itertools import pairwise
from typing import Any

from docx import Document as read_docx
from docx.shared import Cm, Pt
from httpx import AsyncClient
from pypdf import PdfReader

from jobbot.api.routes.letters import version_name
from jobbot.letters import fit
from jobbot.letters.document import DEFAULT_LAYOUT, Identity, Recipient, assemble
from jobbot.letters.pdf import letter_to_pdf
from jobbot.llm.client import RawResult
from jobbot.llm.pricing import Usage
from jobbot.runtime import Runtime

from .test_letters import IDENTITY, FakeClient, api, fake, rt, setup_offer

__all__ = ["api", "fake", "rt"]  # les fixtures de test_letters.py

SENTENCE = (
    "J'administre un cluster Kubernetes et j'automatise son déploiement avec Terraform et "
    "Ansible, ce qui m'a appris à documenter chaque étape et à corriger vite les erreurs. "
)


def body(words: int, paragraphs: int = 4) -> list[str]:
    pool = SENTENCE.split() * 60
    per = words // paragraphs
    return [" ".join(pool[i * per : (i + 1) * per]) + "." for i in range(paragraphs)]


def reply(chunk_id: int, words: int, paragraphs: int = 4) -> RawResult:
    text = json.dumps(
        {
            "language": "fr",
            "subject": "Candidature au poste d'ingénieur DevOps junior",
            "salutation": "Madame, Monsieur,",
            "closing": "Je vous prie d'agréer, Madame, Monsieur, mes salutations distinguées.",
            "paragraphs": [{"text": t, "chunk_ids": [chunk_id]} for t in body(words, paragraphs)],
            "employer": {
                "address": "Avenue de l'Exemple 5\n1003 Lausanne",
                "contact_name": "Mme Dupont",
                "contact_phone": None,
            },
            "refusal": None,
        }
    )
    return RawResult(text, "claude-opus-5", Usage(3000, 0, 0, 1200), "end_turn")


async def pdf_pages(api: AsyncClient, letter_id: int, template: str) -> int:
    response = await api.get(f"/api/letters/{letter_id}/pdf", params={"modele": template})
    assert response.status_code == 200
    return len(PdfReader(io.BytesIO(response.content)).pages)


def target_in(params: dict[str, Any]) -> int:
    found = re.search(r"Raccourcis le corps à (\d+) mots", params["messages"][0]["content"])
    assert found, "la consigne envoyée à l'IA n'a pas de cible chiffrée"
    return int(found.group(1))


def letter_words(letter: dict[str, Any]) -> int:
    return sum(len(p["text"].split()) for p in letter["paragraphs"])


def document(words: int):  # type: ignore[no-untyped-def]
    return assemble(
        Identity(**IDENTITY),
        Recipient("Acme SA", "Avenue de l'Exemple 5\n1003 Lausanne", "Mme Dupont"),
        "fr",
        "Candidature au poste d'ingénieur DevOps junior",
        body(words),
        date(2026, 11, 6),
    )


def test_layout_steps_respect_the_limits() -> None:
    """Dans l'ordre : espacements, interligne (1,25 au moins), marges (2 cm), taille (10,5 pt)."""
    steps = fit.STEPS
    assert steps[0] == DEFAULT_LAYOUT
    for before, after in pairwise(steps):
        assert after.gap <= before.gap and after.side <= before.side
        assert after.size <= before.size
    assert all(s.leading / s.size >= fit.MIN_LEADING - 0.001 for s in steps)
    assert min(s.side for s in steps) == fit.MIN_SIDE == 2.0
    assert min(s.size for s in steps) == fit.MIN_SIZE == 10.5
    # L'espacement change avant l'interligne, l'interligne avant les marges, les marges avant
    # la taille.
    first_change = {
        name: next(i for i, s in enumerate(steps) if getattr(s, name) != getattr(steps[0], name))
        for name in ("gap", "leading", "side", "size")
    }
    assert first_change["gap"] < first_change["leading"] < first_change["side"]
    assert first_change["side"] < first_change["size"]


def test_original_layout_overflowed_where_the_word_count_said_it_fit() -> None:
    """Le constat : 350 mots passaient le contrôle des 400 mots et faisaient deux pages."""
    letter = document(350)
    assert len(PdfReader(io.BytesIO(letter_to_pdf(letter, template="bandeau"))).pages) == 2
    result = fit.fit(letter, "bandeau")
    assert result.fits and result.adjusted
    pdf = letter_to_pdf(letter, template="bandeau", layout=result.layout)
    assert len(PdfReader(io.BytesIO(pdf)).pages) == 1


async def test_long_letter_with_bandeau_fits_after_adjustment(
    api: AsyncClient, rt: Runtime, fake: FakeClient
) -> None:
    """Une lettre longue dans le Bandeau tient après ajustement, sans appel de plus à l'IA."""
    offer_id, chunk_id = await setup_offer(rt)
    await api.put("/api/identity", json=IDENTITY)
    fake.response = [reply(chunk_id, 380)]

    response = await api.post(f"/api/offers/{offer_id}/letters", json={"modele": "bandeau"})
    assert response.status_code == 201
    letter = response.json()
    assert len(fake.params) == 1 and letter_words(letter) >= 370
    assert letter["name"] == "Version 1"

    page = (await api.get(f"/api/letters/{letter['id']}/page", params={"modele": "bandeau"})).json()
    assert page["fits"] and page["adjusted"] and page["overflow_lines"] == 0
    assert page["font_size"] >= 10.5 and page["side_margin_cm"] >= 2.0
    assert page["line_height"] / page["font_size"] >= 1.249
    assert await pdf_pages(api, letter["id"], "bandeau") == 1

    # Le Word reprend les réglages du PDF.
    docx = await api.get(f"/api/letters/{letter['id']}/docx", params={"modele": "bandeau"})
    word = read_docx(io.BytesIO(docx.content))
    normal = word.styles["Normal"]
    assert normal.font.size == Pt(page["font_size"])
    assert normal.paragraph_format.line_spacing == Pt(page["line_height"])
    # Word arrondit les marges au vingtième de point.
    margin = word.sections[0].left_margin
    assert margin is not None and abs(margin - Cm(page["side_margin_cm"])) < Pt(0.1)


async def test_very_long_letter_is_shortened_by_the_ai_with_a_target(
    api: AsyncClient, rt: Runtime, fake: FakeClient
) -> None:
    """Trop longue même resserrée : l'IA raccourcit à un nombre de mots calculé, puis on vérifie."""
    offer_id, chunk_id = await setup_offer(rt)
    await api.put("/api/identity", json=IDENTITY)
    fake.response = [reply(chunk_id, 700, 5), reply(chunk_id, 300)]

    letter = (await api.post(f"/api/offers/{offer_id}/letters", json={"modele": "moderne"})).json()
    assert len(fake.params) == 2
    target = target_in(fake.params[1])
    # La cible vient du débordement mesuré : nettement sous 700, assez pour tenir.
    assert 250 <= target <= 520
    content = fake.params[1]["messages"][0]["content"]
    assert "garde les 2 exigences principales et la conclusion" in content
    assert "<version_precedente>" in content
    assert letter_words(letter) <= 310
    assert await pdf_pages(api, letter["id"], "moderne") == 1


async def test_two_tries_at_most_then_the_shortest_is_kept(
    api: AsyncClient, rt: Runtime, fake: FakeClient
) -> None:
    offer_id, chunk_id = await setup_offer(rt)
    await api.put("/api/identity", json=IDENTITY)
    fake.response = [reply(chunk_id, 760, 5), reply(chunk_id, 640, 5), reply(chunk_id, 700, 5)]

    letter = (await api.post(f"/api/offers/{offer_id}/letters", json={"modele": "sobre"})).json()
    assert len(fake.params) == 3  # la rédaction, puis deux raccourcissements, pas un de plus
    assert 630 <= letter_words(letter) <= 640
    page = (await api.get(f"/api/letters/{letter['id']}/page", params={"modele": "sobre"})).json()
    assert not page["fits"] and page["overflow_lines"] > 0
    assert page["break_paragraph"] is not None and page["break_word"] is not None
    assert await pdf_pages(api, letter["id"], "sobre") == 2


async def test_one_page_instruction_sends_a_numbered_target(
    api: AsyncClient, rt: Runtime, fake: FakeClient
) -> None:
    """« Ça ne tient pas sur une page » : la même vérification, avec une cible chiffrée."""
    offer_id, chunk_id = await setup_offer(rt)
    await api.put("/api/identity", json=IDENTITY)
    fake.response = [reply(chunk_id, 380)]
    first = (await api.post(f"/api/offers/{offer_id}/letters", json={"modele": "classique"})).json()

    fake.response = [reply(chunk_id, 280)]
    response = await api.post(
        f"/api/offers/{offer_id}/letters",
        json={
            "instruction": "Ça ne tient pas sur une page",
            "base_draft_id": first["id"],
            "modele": "classique",
        },
    )
    assert response.status_code == 201
    second = response.json()
    target = target_in(fake.params[1])
    # Au moins 15 % de moins que la version d'avant.
    assert target <= int(letter_words(first) * 0.85)
    assert "Ça ne tient pas sur une page" in fake.params[1]["messages"][0]["content"]
    # La consigne de la personne reste celle de la version ; le nom est court.
    assert second["instruction"] == "Ça ne tient pas sur une page"
    assert second["name"] == "Plus courte"
    assert await pdf_pages(api, second["id"], "classique") == 1


def test_version_names() -> None:
    assert version_name(3, None) == "Version 3"
    assert version_name(4, "Insiste sur Kubernetes et sur le travail en équipe") == "Version 4"
    for instruction in ("plus court", "Une page", "ça ne tient pas sur une page", "Shorter"):
        assert version_name(2, instruction) == "Plus courte", instruction
