"""CV adapté : sélection des blocs, retouches, mise en page, Word (docs/08 §4, 0.5.0-c)."""

import io
import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import pytest
from docx import Document as read_docx
from httpx import ASGITransport, AsyncClient
from pypdf import PdfReader
from sqlalchemy import select, text, update

from jobbot.api.app import create_app
from jobbot.db.models import LlmCall, Offer, OfferStatus, ProfileChunk, Setting
from jobbot.letters.cv_document import highlight
from jobbot.llm.client import RawResult
from jobbot.llm.pricing import Usage
from jobbot.runtime import Runtime
from jobbot.scoring import service

from .conftest import make_settings
from .test_letters import IDENTITY, FakeClient

NOW = datetime(2026, 10, 5, 8, 0, tzinfo=UTC)


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
        await conn.execute(text("DELETE FROM settings WHERE key LIKE 'identity_%'"))
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


async def setup(rt: Runtime) -> tuple[int, dict[str, int]]:
    async with rt.sessionmaker.begin() as session:
        chunks = {
            "stage": ProfileChunk(
                kind="experience",
                title="Stage DevOps — Acme (2024-2025)",
                content="Terraform sur AWS.",
            ),
            "web": ProfileChunk(kind="experience", title="Stage web", content="Vue.js et PHP."),
            "k8s": ProfileChunk(
                kind="competence", title="Kubernetes", content="K3s, Helm, kubernetes."
            ),
            "langues": ProfileChunk(
                kind="competence", title="Langues", content="Français, anglais B2."
            ),
            "ecole": ProfileChunk(kind="formation", title="École 42", content="Projets système."),
            "pref": ProfileChunk(
                kind="preference", title="Postes recherchés", content="DevOps junior"
            ),
        }
        offer = Offer(
            fingerprint="o1",
            title="Ingénieur DevOps junior",
            company="Acme SA",
            first_seen_at=NOW,
            last_seen_at=NOW,
            status=OfferStatus.TO_REVIEW,
        )
        session.add_all([*chunks.values(), offer])
        await session.flush()
        return offer.id, {k: c.id for k, c in chunks.items()}


def answer(ids: list[int], **extra: Any) -> RawResult:
    body = {
        "language": "fr",
        "headline": "Ingénieur DevOps junior — Kubernetes, Terraform",
        "summary": "Stage DevOps sur AWS avec Terraform ; Kubernetes au quotidien.",
        "chunk_ids": ids,
        "keywords": ["Terraform", "Kubernetes", "Ansible"],
        **extra,
    }
    return RawResult(json.dumps(body), "claude-opus-5", Usage(3000, 0, 0, 400), "end_turn")


async def test_write_cv(api: AsyncClient, rt: Runtime, fake: FakeClient) -> None:
    offer_id, ids = await setup(rt)
    await api.put("/api/identity", json=IDENTITY)
    # L'IA met la compétence avant le stage, cite une préférence et un bloc inconnu, oublie
    # la formation et les langues.
    fake.response = answer([ids["k8s"], ids["stage"], ids["pref"], 999999])

    response = await api.post(f"/api/offers/{offer_id}/cvs", json={"language": "fr"})
    assert response.status_code == 201
    cv = response.json()
    assert cv["chunk_ids"] == [ids["k8s"], ids["stage"], ids["langues"], ids["ecole"]]
    # « Ansible » n'est dans aucun bloc choisi : retiré.
    assert cv["keywords"] == ["Terraform", "Kubernetes"]
    assert [(b["id"], b["selected"]) for b in cv["blocks"]][-1] == (ids["web"], False)
    assert all(b["id"] != ids["pref"] for b in cv["blocks"])

    doc = cv["document"]
    assert doc["name"] == "Jean Exemple"
    assert doc["contacts"] == ["Rue du Test 1, 1020 Renens", "+41 79 000 00 00", "jean@example.org"]
    # Ordre fixe des rubriques, ordre de l'IA dans chaque rubrique.
    assert [s["key"] for s in doc["sections"]] == [
        "experience",
        "competence",
        "formation",
        "langues",
    ]
    competence = doc["sections"][1]["items"][0]
    assert [s["text"] for s in competence["content"] if s["strong"]] == ["kubernetes"]
    assert doc["sections"][3]["items"][0]["title"] is None

    sent = json.dumps(fake.params[0], ensure_ascii=False)
    for value in IDENTITY.values():
        assert value not in sent
    async with rt.sessionmaker() as session:
        assert list(await session.scalars(select(LlmCall.purpose))) == ["cv"]
        offer = await session.get(Offer, offer_id)
        assert offer is not None and offer.status == "preparing"


async def test_edit_application_and_docx(api: AsyncClient, rt: Runtime, fake: FakeClient) -> None:
    offer_id, ids = await setup(rt)
    await api.put("/api/identity", json=IDENTITY)
    fake.response = answer([ids["stage"], ids["k8s"]])
    cv = (await api.post(f"/api/offers/{offer_id}/cvs", json={})).json()

    edited = await api.put(
        f"/api/cvs/{cv['id']}",
        json={
            "headline": "Ingénieur DevOps junior",
            "summary": "Résumé corrigé.",
            "chunk_ids": [ids["web"], ids["stage"], ids["pref"]],
        },
    )
    assert edited.status_code == 200
    body = edited.json()
    assert body["chunk_ids"] == [ids["web"], ids["stage"]] and body["edited_at"]
    assert body["keywords"] == ["Terraform", "Kubernetes"]
    rejected = await api.put(
        f"/api/cvs/{cv['id']}", json={"headline": "", "summary": "", "chunk_ids": [ids["pref"]]}
    )
    assert rejected.status_code == 422

    prefill = (await api.get(f"/api/offers/{offer_id}/application-prefill")).json()
    created = (await api.post("/api/applications", json=prefill)).json()
    assert created["cv_draft_id"] == cv["id"] and created["letter_draft_id"] is None

    response = await api.get(f"/api/cvs/{cv['id']}/docx")
    assert (
        response.status_code == 200 and "CV%20-%20Acme" in response.headers["content-disposition"]
    )
    paragraphs = [p.text for p in read_docx(io.BytesIO(response.content)).paragraphs]
    assert paragraphs[0] == "Jean Exemple" and "Résumé corrigé." in paragraphs
    assert paragraphs.index("Stage web") < paragraphs.index("Stage DevOps — Acme (2024-2025)")
    assert "EXPÉRIENCES" in paragraphs

    pdf = await api.get(f"/api/cvs/{cv['id']}/pdf")
    assert pdf.status_code == 200 and "CV%20-%20Acme%20SA.pdf" in pdf.headers["content-disposition"]
    text_ = " ".join(page.extract_text() for page in PdfReader(io.BytesIO(pdf.content)).pages)
    assert "Jean Exemple" in text_ and "Résumé corrigé." in text_ and "EXPÉRIENCES" in text_
    assert text_.index("Stage web") < text_.index("Stage DevOps")


async def test_new_version_and_errors(api: AsyncClient, rt: Runtime, fake: FakeClient) -> None:
    offer_id, ids = await setup(rt)
    fake.response = answer([ids["stage"]])
    first = (await api.post(f"/api/offers/{offer_id}/cvs", json={})).json()
    fake.response = answer([ids["k8s"]], language="en")
    second = (
        await api.post(
            f"/api/offers/{offer_id}/cvs",
            json={"instruction": "en anglais", "base_draft_id": first["id"]},
        )
    ).json()
    assert second["version"] == 2 and second["document"]["sections"][0]["heading"] == "Skills"
    assert "<version_precedente>" in fake.params[1]["messages"][0]["content"]
    assert second["document"]["missing_identity"] == ["nom", "rue", "NPA", "localité"]
    assert [c["version"] for c in (await api.get(f"/api/offers/{offer_id}/cvs")).json()] == [2, 1]

    fake.response = answer([ids["pref"]])  # aucun bloc de CV
    assert (await api.post(f"/api/offers/{offer_id}/cvs", json={})).status_code == 502
    assert (await api.get("/api/cvs/999999/docx")).status_code == 404
    assert (await api.get("/api/offers/999999/cvs")).status_code == 404


def test_highlight() -> None:
    segments = highlight("Terraform, terraformé et AWS.", ["terraform", "AWS"])
    assert [(s.text, s.strong) for s in segments] == [
        ("Terraform", True),
        (", terraformé et ", False),
        ("AWS", True),
        (".", False),
    ]
