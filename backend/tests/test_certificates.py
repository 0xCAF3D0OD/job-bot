"""Les certificats de travail, décodés (docs/87) : les formules connues, sans IA ; les noms
retirés avant l'IA ; la lecture détaillée sur demande."""

from collections.abc import AsyncIterator
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from jobbot.certificates import service
from jobbot.db.models import Document
from jobbot.llm.client import RawResult
from jobbot.llm.pricing import Usage
from jobbot.runtime import Runtime

from .conftest import admin_engine

VERY_GOOD = """Certificat de travail

Monsieur Camille Exemple, né le 3 mars 1990, a travaillé chez Acme SA du 1er mars 2021 au
30 juin 2025 en qualité d'ingénieur DevOps.

Il a accompli ses tâches toujours à notre plus grande satisfaction. Son comportement envers
ses supérieurs et ses collègues a toujours été irréprochable.

Monsieur Exemple nous quitte à sa demande. Nous regrettons vivement son départ, le remercions
pour son engagement et lui souhaitons plein succès pour la suite de sa carrière.

Lausanne, le 30 juin 2025

Anne Dupont
Directrice des ressources humaines
"""

WEAK = """Certificat de travail

Madame Camille Exemple a travaillé chez Démo SA comme assistante de 2022 à 2024.
Elle s'est efforcée de mener à bien les tâches confiées, dans l'ensemble à notre satisfaction.
Son comportement envers ses collègues et ses supérieurs était correct.
Nous nous sommes séparés le 31 mars 2024.
"""

GERMAN = """Arbeitszeugnis

Herr Camille Exemple war vom 1. Mai 2019 bis 31. Dezember 2020 bei der Beispiel AG tätig.
Er erledigte seine Aufgaben zu unserer vollen Zufriedenheit. Sein Verhalten gegenüber
Vorgesetzten und Kollegen war stets einwandfrei. Er verlässt uns auf eigenen Wunsch. Wir danken
ihm und wünschen ihm für die Zukunft alles Gute und viel Erfolg.
"""


def test_the_known_formulas_without_ai() -> None:
    good = service.read(VERY_GOOD)
    assert (good.language, good.grade, good.advice) == ("fr", 4, "attach")
    assert [p.category for p in good.passages] == ["performance", "departure"]
    assert good.notes == []
    assert service.explain(good) == (
        "Formule clé : « toujours à notre plus grande satisfaction ». "
        "Très bon : la meilleure formule."
    )

    weak = service.read(WEAK)
    assert (weak.grade, weak.advice) == (1, "correct")
    # « dans l'ensemble à notre satisfaction » n'est pas lu aussi comme « à notre satisfaction ».
    assert sorted(p.text for p in weak.passages) == [
        "Nous nous sommes séparés",
        "dans l'ensemble à notre satisfaction",
        "s'est efforcée de",
    ]
    notes = " ".join(n.text for n in weak.notes)
    assert "collègues sont cités avant les supérieurs" in notes
    assert "Pas de formule de fin" in notes

    german = service.read(GERMAN)
    assert (german.language, german.grade, german.advice) == ("de", 2, "on_request")
    assert any(
        n.text.startswith("La formule de fin ne contient pas les regrets") for n in german.notes
    )

    unknown = service.read("Madame X a travaillé chez nous de 2020 à 2021.")
    assert unknown.grade is None and unknown.advice == "on_request"


def test_no_names_go_to_the_ai() -> None:
    sent = service.without_names(
        VERY_GOOD + "\nContact : anne.dupont@acme.example, 021 555 12 34",
        ["Camille Exemple", "Camille", "Exemple"],
    )
    for secret in ("Camille", "Exemple", "Dupont", "anne.dupont", "555 12 34"):
        assert secret not in sent
    assert "Acme SA" in sent and "toujours à notre plus grande satisfaction" in sent
    assert "Directrice des ressources humaines" in sent


@pytest.fixture
async def documents(runtime: Runtime) -> AsyncIterator[list[int]]:
    async def reset() -> None:
        async with admin_engine().begin() as conn:
            await conn.execute(text("DELETE FROM documents WHERE sha256 LIKE 'certif-%'"))
            await conn.execute(text("DELETE FROM llm_calls WHERE purpose = 'certificate'"))

    await reset()
    ids = []
    async with runtime.sessionmaker.begin() as session:
        for n, (name, body) in enumerate(
            (("Acme SA.pdf", VERY_GOOD), ("Démo SA.pdf", WEAK), ("Beispiel AG.pdf", GERMAN))
        ):
            document = Document(
                filename=name,
                doc_type="pdf",
                size=len(body),
                sha256=f"certif-{n}",
                storage_key=f"certif-{n}",
                text_status="ok",
                extracted_text=body,
            )
            session.add(document)
            await session.flush()
            ids.append(document.id)
    yield ids
    await reset()


async def test_mark_read_and_summarise(client: AsyncClient, documents: list[int]) -> None:
    assert (await client.get("/api/certificates")).json() == {"certificates": [], "summary": None}
    for document_id in documents:
        page = (
            await client.put(f"/api/documents/{document_id}/kind", json={"kind": "certificate"})
        ).json()
    by_name = {c["filename"]: c for c in page["certificates"]}
    assert by_name["Acme SA.pdf"]["grade_label"] == "très bon"
    assert by_name["Démo SA.pdf"]["advice_label"] == "à faire corriger d'abord"
    assert page["summary"] == (
        "Joins « Acme SA ». Pour « Démo SA », demande d'abord une correction. "
        "« Beispiel AG » : seulement si on te le demande."
    )
    listed = (await client.get("/api/documents")).json()
    assert {d["kind"] for d in listed if d["id"] in documents} == {"certificate"}
    # Ce n'est plus un certificat : sa lecture part avec.
    page = (await client.put(f"/api/documents/{documents[2]}/kind", json={"kind": None})).json()
    assert len(page["certificates"]) == 2
    assert (await client.put("/api/documents/999999/kind", json={"kind": None})).status_code == 404


async def test_the_detailed_reading(
    client: AsyncClient, runtime: Runtime, documents: list[int], monkeypatch: pytest.MonkeyPatch
) -> None:
    from jobbot.scoring import service as scoring

    weak = documents[1]
    # Pas encore marqué, puis sans IA : refusé.
    assert (await client.post(f"/api/certificates/{weak}/lecture")).status_code == 409
    await client.put(f"/api/documents/{weak}/kind", json={"kind": "certificate"})
    assert (await client.post(f"/api/certificates/{weak}/lecture")).status_code == 409
    calls: list[dict[str, Any]] = []

    class Fake:
        async def score(self, params: dict[str, Any]) -> RawResult:
            calls.append(params)
            answer = (
                '<reponse>{"note": 1, "explication": "Le certificat dit que le travail était '
                'insuffisant.", "manques": ["Les tâches ne sont pas décrites."], "ordre": '
                '"Les collègues avant les supérieurs.", "conseil": "corriger", "conseil_texte": '
                '"Demande une reformulation avant de le joindre."}</reponse>'
            )
            return RawResult(answer, service.MODEL, Usage(2500, 0, 0, 500), "end_turn")

    monkeypatch.setattr(scoring, "make_client", lambda _settings: Fake())
    monkeypatch.setattr(type(runtime.settings), "llm_configured", property(lambda _self: True))
    page = (await client.post(f"/api/certificates/{weak}/lecture")).json()
    [read] = page["certificates"]
    assert read["ai"]["advice"] == "correct" and read["ai"]["missing"] == [
        "Les tâches ne sont pas décrites."
    ]
    assert read["explanation"].startswith("Le certificat dit") and read["ai_at"]
    content = calls[0]["messages"][0]["content"]
    assert "Camille" not in content and "s'est efforcée de" in content
    assert "<reperes>" in content


async def test_the_letters(
    client: AsyncClient, runtime: Runtime, documents: list[int], monkeypatch: pytest.MonkeyPatch
) -> None:
    """0.69.1 : la lettre de correction (modèle, puis IA) et le certificat intermédiaire."""
    from jobbot.certificates import letters
    from jobbot.scoring import service as scoring

    good, weak, german = documents
    for document_id in documents:
        await client.put(f"/api/documents/{document_id}/kind", json={"kind": "certificate"})
    page = (await client.get("/api/certificates")).json()
    assert [c["end_year"] for c in page["certificates"]] == [2025, 2024, 2020]
    template = (await client.get(f"/api/certificates/{weak}/correction")).json()
    assert template["ai"] is False and template["subject"].startswith("Demande de correction")
    assert (
        "- « dans l'ensemble à notre satisfaction » : je vous propose « toujours à notre "
        in (template["text"])
    )
    assert "- « Nous nous sommes séparés » : je vous propose ne pas mentionner" in template["text"]
    assert "art." not in template["text"].lower()
    assert (await client.get(f"/api/certificates/{german}/correction")).json()["subject"] == (
        "Bitte um Berichtigung meines Arbeitszeugnisses"
    )
    # Avec l'IA, sans clé : le modèle simple, et pourquoi.
    fallback = (await client.post(f"/api/certificates/{weak}/correction")).json()
    assert fallback["ai"] is False and "pas encore activée" in fallback["reason"]
    calls: list[dict[str, Any]] = []

    class Fake:
        async def score(self, params: dict[str, Any]) -> RawResult:
            calls.append(params)
            return RawResult(
                "Madame, Monsieur,\n\nMerci pour le certificat.",
                letters.MODEL,
                Usage(1800, 0, 0, 300),
                "end_turn",
            )

    monkeypatch.setattr(scoring, "make_client", lambda _settings: Fake())
    monkeypatch.setattr(type(runtime.settings), "llm_configured", property(lambda _self: True))
    written = (await client.post(f"/api/certificates/{weak}/correction")).json()
    assert written["ai"] is True and written["text"].startswith("Madame, Monsieur,")
    content = calls[0]["messages"][0]["content"]
    assert "Camille" not in content and "<points>" in content
    assert (await client.get(f"/api/certificates/{good}/correction")).status_code == 200
    assert (await client.get("/api/certificates/999999/correction")).status_code == 409
    interim = (await client.get("/api/certificates/intermediaire")).json()
    assert interim["subject"] == "Demande de certificat de travail intermédiaire"
    assert "intermédiaire" in interim["text"]
    async with admin_engine().begin() as conn:
        await conn.execute(text("DELETE FROM llm_calls WHERE purpose = 'certificate_letter'"))
