"""Lettre de motivation : rédaction, versions, assemblage, Word (docs/08 §3, 0.5.0-b)."""

import io
import json
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from typing import Any

import anthropic
import httpx2
import pytest
from docx import Document as read_docx
from httpx import ASGITransport, AsyncClient
from pypdf import PdfReader
from sqlalchemy import select, text, update

from jobbot.api.app import create_app
from jobbot.db.models import (
    Evaluation,
    LlmCall,
    Offer,
    OfferStatus,
    ProfileChunk,
    Setting,
)
from jobbot.letters.document import Identity, Recipient, assemble, format_date
from jobbot.llm.client import RawResult
from jobbot.llm.pricing import Usage
from jobbot.runtime import Runtime
from jobbot.scoring import service

from .conftest import make_settings

NOW = datetime(2026, 10, 5, 8, 0, tzinfo=UTC)
IDENTITY = {
    "name": "Jean Exemple",
    "street": "Rue du Test 1",
    "postcode": "1020",
    "city": "Renens",
    "phone": "+41 79 000 00 00",
    "email": "jean@example.org",
}


def letter_json(chunk_ids: list[int], **extra: Any) -> str:
    return json.dumps(
        {
            "language": "fr",
            "subject": "Objet : Candidature au poste d'ingénieur DevOps junior",
            "paragraphs": [
                {"text": "Votre annonce a retenu mon attention.", "chunk_ids": []},
                {"text": "J'administre un cluster K3s.", "chunk_ids": [*chunk_ids, 999999]},
                {"text": "  ", "chunk_ids": []},
            ],
            "employer": {
                "address": "Avenue de l'Exemple 5\n1003 Lausanne",
                "contact_name": "Mme Dupont",
                "contact_phone": None,
            },
            **extra,
        }
    )


class FakeClient:
    def __init__(self) -> None:
        self.response: RawResult | Exception | None = None
        self.params: list[dict[str, Any]] = []

    async def score(self, params: dict[str, Any]) -> RawResult:
        self.params.append(params)
        assert self.response is not None
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch) -> FakeClient:
    client = FakeClient()
    monkeypatch.setattr(service, "make_client", lambda _settings: client)
    return client


@pytest.fixture
async def rt() -> AsyncIterator[Runtime]:
    runtime = Runtime.create(make_settings(anthropic_api_key="sk-test"))
    async with runtime.engine.begin() as conn:
        await conn.execute(text("TRUNCATE offers, profile_chunks, llm_calls, applications CASCADE"))
        await conn.execute(
            text("DELETE FROM settings WHERE key LIKE 'identity_%' OR key LIKE 'apply_%'")
        )
    yield runtime
    async with runtime.sessionmaker.begin() as session:
        await session.execute(
            update(Setting).where(Setting.key == "llm_monthly_budget_chf").values(value=10)
        )
    await runtime.dispose()


@pytest.fixture
async def api(rt: Runtime) -> AsyncIterator[AsyncClient]:
    app = create_app(rt.settings, rt)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


async def setup_offer(rt: Runtime) -> tuple[int, int]:
    async with rt.sessionmaker.begin() as session:
        chunk = ProfileChunk(kind="competence", title="Kubernetes", content="K3s, Helm")
        offer = Offer(
            fingerprint="o1",
            title="Ingénieur DevOps junior",
            company="Acme SA",
            location="Lausanne, VD",
            description="Nous cherchons un ingénieur DevOps. Contact : Mme Dupont.",
            first_seen_at=NOW,
            last_seen_at=NOW,
            status=OfferStatus.TO_REVIEW,
        )
        session.add_all([chunk, offer])
        await session.flush()
        session.add(
            Evaluation(
                offer_id=offer.id,
                filter_passed=True,
                filter_reasons=[],
                criteria_hash="x",
                score=72,
                strengths=[{"text": "Kubernetes pratiqué", "chunk_ids": [chunk.id]}],
                gaps=[{"text": "Pas de VMware", "chunk_ids": []}],
            )
        )
        return offer.id, chunk.id


def answer(chunk_id: int, **extra: Any) -> RawResult:
    return RawResult(
        letter_json([chunk_id], **extra), "claude-opus-5", Usage(3000, 0, 0, 1200), "end_turn"
    )


async def test_write_letter(api: AsyncClient, rt: Runtime, fake: FakeClient) -> None:
    offer_id, chunk_id = await setup_offer(rt)
    await api.put("/api/identity", json=IDENTITY)
    fake.response = answer(chunk_id)

    response = await api.post(f"/api/offers/{offer_id}/letters", json={})
    assert response.status_code == 201
    letter = response.json()
    assert letter["version"] == 1 and letter["language"] == "fr"
    assert letter["subject"] == "Candidature au poste d'ingénieur DevOps junior"
    # Paragraphe vide retiré, bloc inconnu retiré.
    assert [p["chunk_ids"] for p in letter["paragraphs"]] == [[], [chunk_id]]
    doc = letter["document"]
    assert doc["sender"] == [
        "Jean Exemple",
        "Rue du Test 1",
        "1020 Renens",
        "+41 79 000 00 00",
        "jean@example.org",
    ]
    assert doc["recipient"] == [
        "Acme SA",
        "À l'attention de Mme Dupont",
        "Avenue de l'Exemple 5",
        "1003 Lausanne",
    ]
    assert doc["place_date"].startswith("Renens, le ")
    assert doc["salutation"] == "Madame, Monsieur,"
    assert doc["missing_identity"] == []

    # Les coordonnées ne partent jamais vers l'IA ; la note et la langue, si.
    sent = json.dumps(fake.params[0], ensure_ascii=False)
    for value in IDENTITY.values():
        assert value not in sent
    assert "Pas de VMware" in sent and "<langue>auto</langue>" in sent
    assert fake.params[0]["output_config"]["effort"] == "medium"

    assert await offer_status(rt, offer_id) == "preparing"
    # Aucune adresse connue : celle relevée par l'IA devient celle de l'offre (« letter »).
    offer = (await api.get(f"/api/offers/{offer_id}")).json()
    assert offer["company_address"] == "Avenue de l'Exemple 5\n1003 Lausanne"
    assert offer["company_address_source"] == "letter"
    async with rt.sessionmaker() as session:
        assert list(await session.scalars(select(LlmCall.purpose))) == ["letter"]


async def offer_status(rt: Runtime, offer_id: int) -> str:
    async with rt.sessionmaker() as session:
        offer = await session.get(Offer, offer_id)
        assert offer is not None
        return offer.status


async def test_new_version_with_instruction(
    api: AsyncClient, rt: Runtime, fake: FakeClient
) -> None:
    offer_id, chunk_id = await setup_offer(rt)
    fake.response = answer(chunk_id)
    first = (await api.post(f"/api/offers/{offer_id}/letters", json={})).json()
    fake.response = answer(chunk_id, language="en")
    second = (
        await api.post(
            f"/api/offers/{offer_id}/letters",
            json={"instruction": "en anglais", "language": "en", "base_draft_id": first["id"]},
        )
    ).json()
    assert second["version"] == 2 and second["instruction"] == "en anglais"
    assert second["document"]["salutation"] == "Dear Sir or Madam,"
    user = fake.params[1]["messages"][0]["content"]
    assert "<version_precedente>" in user and "en anglais" in user and "<langue>en</langue>" in user
    # Sans coordonnées : l'en-tête signale ce qui manque.
    assert second["document"]["missing_identity"] == ["nom", "rue", "NPA", "localité"]
    versions = (await api.get(f"/api/offers/{offer_id}/letters")).json()
    assert [v["version"] for v in versions] == [2, 1]


async def test_edit_then_application_and_docx(
    api: AsyncClient, rt: Runtime, fake: FakeClient
) -> None:
    offer_id, chunk_id = await setup_offer(rt)
    await api.put("/api/identity", json=IDENTITY)
    fake.response = answer(chunk_id)
    first = (await api.post(f"/api/offers/{offer_id}/letters", json={})).json()
    await api.post(f"/api/offers/{offer_id}/letters", json={})

    # La version 1 modifiée devient celle qui compte.
    edited = await api.put(
        f"/api/letters/{first['id']}",
        json={
            "subject": "Candidature",
            "paragraphs": [{"text": "Texte corrigé.", "chunk_ids": []}],
        },
    )
    assert edited.status_code == 200 and edited.json()["edited_at"]

    prefill = (await api.get(f"/api/offers/{offer_id}/application-prefill")).json()
    assert prefill["company_address"] == "Avenue de l'Exemple 5, 1003 Lausanne"
    assert prefill["contact_name"] == "Mme Dupont"
    created = (
        await api.post(
            "/api/applications",
            json={k: v for k, v in prefill.items()},
        )
    ).json()
    assert created["letter_draft_id"] == first["id"]

    response = await api.get(f"/api/letters/{first['id']}/docx")
    assert response.status_code == 200
    assert "Acme" in response.headers["content-disposition"]
    paragraphs = [p.text for p in read_docx(io.BytesIO(response.content)).paragraphs]
    assert "Objet : Candidature" in paragraphs and "Texte corrigé." in paragraphs
    assert any("Jean Exemple" in p for p in paragraphs)

    pdf = await api.get(f"/api/letters/{first['id']}/pdf")
    assert pdf.status_code == 200 and pdf.headers["content-type"] == "application/pdf"
    assert "Lettre%20-%20Acme%20SA.pdf" in pdf.headers["content-disposition"]
    text_ = " ".join(page.extract_text() for page in PdfReader(io.BytesIO(pdf.content)).pages)
    assert "Objet : Candidature" in text_ and "Texte corrigé." in text_
    assert "Jean Exemple" in text_
    assert (await api.get("/api/letters/999999/pdf")).status_code == 404


async def test_errors(api: AsyncClient, rt: Runtime, fake: FakeClient) -> None:
    assert (await api.post("/api/offers/999999/letters", json={})).status_code == 404
    offer_id, chunk_id = await setup_offer(rt)

    fake.response = RawResult("pas du json", "claude-opus-5", Usage(10, 0, 0, 10), "end_turn")
    assert (await api.post(f"/api/offers/{offer_id}/letters", json={})).status_code == 502

    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    fake.response = anthropic.BadRequestError(
        "Your credit balance is too low",
        response=httpx2.Response(400, request=request),
        body={"error": {"message": "Your credit balance is too low"}},
    )
    response = await api.post(f"/api/offers/{offer_id}/letters", json={})
    assert response.status_code == 409

    async with rt.sessionmaker.begin() as session:
        await session.execute(
            update(Setting).where(Setting.key == "llm_monthly_budget_chf").values(value=0)
        )
    fake.response = answer(chunk_id)
    response = await api.post(f"/api/offers/{offer_id}/letters", json={})
    assert response.status_code == 409 and "plafond" in response.json()["detail"]
    assert (
        await api.put("/api/letters/999999", json={"subject": "x", "paragraphs": [{"text": "y"}]})
    ).status_code == 404


async def test_letter_needs_profile(api: AsyncClient, rt: Runtime, fake: FakeClient) -> None:
    async with rt.sessionmaker.begin() as session:
        offer = Offer(fingerprint="o2", title="x", first_seen_at=NOW, last_seen_at=NOW)
        session.add(offer)
        await session.flush()
        offer_id = offer.id
    response = await api.post(f"/api/offers/{offer_id}/letters", json={})
    assert response.status_code == 409 and "bloc de profil" in response.json()["detail"]
    assert fake.params == []


def test_assemble_languages() -> None:
    assert format_date(date(2026, 10, 1), "fr") == "1er octobre 2026"
    assert format_date(date(2026, 3, 5), "de") == "5. März 2026"
    identity = Identity(name="Jean Exemple", city="Renens", postcode="1020", street="Rue 1")
    letter = assemble(
        identity, Recipient("Beta AG"), "de", "Bewerbung", ["Text."], date(2026, 10, 5)
    )
    assert letter.place_date == "Renens, 5. Oktober 2026"
    assert letter.closing == "Freundliche Grüsse" and letter.subject_line == "Bewerbung"
    assert letter.recipient == ["Beta AG"]


async def test_get_offer(api: AsyncClient, rt: Runtime) -> None:
    offer_id, _ = await setup_offer(rt)
    offer = (await api.get(f"/api/offers/{offer_id}")).json()
    assert offer["id"] == offer_id and offer["title"] == "Ingénieur DevOps junior"
    assert (await api.get("/api/offers/999999")).status_code == 404
