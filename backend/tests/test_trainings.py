"""Formations (docs/16 §5) : catalogue, filtre « Mon domaine », suivi, suggestions de l'IA."""

import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from jobbot.api.app import create_app
from jobbot.api.routes import trainings as routes
from jobbot.db.models import (
    Evaluation,
    LlmCall,
    Notification,
    Offer,
    ProfileChunk,
    Training,
    TrainingMark,
)
from jobbot.followups.service import local_today
from jobbot.llm.client import RawResult
from jobbot.llm.pricing import Usage
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring
from jobbot.trainings import funding, service

from .conftest import admin_engine, make_settings

KEYWORDS = ["Kubernetes", "CKA"]


def answer(items: list[dict[str, Any]]) -> str:
    return f"J'ai cherché.\n<reponse>{json.dumps({'formations': items})}</reponse>"


GOOD = {
    "title": "Kubernetes en français",
    "provider": "Exemple Formation",
    "kind": "cours",
    "format": "self_paced",
    "language": "fr",
    "price": "free",
    "level": "beginner",
    "duration": None,
    "url": "https://formation.example/kubernetes",
    "tags": ["Kubernetes", "débutant"],
    "description": "Premiers pas.",
}


class FakeClient:
    def __init__(self, text: str) -> None:
        self.text = text
        self.calls: list[dict[str, Any]] = []

    async def score(self, params: dict[str, Any]) -> RawResult:
        self.calls.append(params)
        return RawResult(
            self.text, service.MODEL, Usage(3000, 0, 0, 500, web_searches=2), "end_turn"
        )


@pytest.fixture
async def rt() -> AsyncIterator[Runtime]:
    runtime = Runtime.create(make_settings(anthropic_api_key="sk-test"))
    routes._synced = False
    async with admin_engine().begin() as conn:
        await conn.execute(text("TRUNCATE trainings, llm_calls CASCADE"))
        await conn.execute(
            text(
                "UPDATE profiles SET preferences = CAST(:value AS jsonb) WHERE is_main"
            ).bindparams(
                value=json.dumps(
                    {
                        "domain_keywords": KEYWORDS,
                        "domain_only": False,
                        "countries": [],
                        "languages": [],
                    }
                )
            )
        )
    yield runtime
    async with admin_engine().begin() as conn:
        await conn.execute(text("TRUNCATE trainings CASCADE"))
        await conn.execute(text("UPDATE profiles SET preferences = '{}'::jsonb WHERE is_main"))
    await runtime.dispose()


def test_catalog_is_consistent() -> None:
    entries = service.catalog()
    urls = [e["url"] for e in entries]
    assert len(urls) == len(set(urls))
    for entry in entries:
        assert entry["kind"] in service.KINDS and entry["format"] in service.FORMATS
        assert entry["price"] in service.PRICES and entry["url"].startswith("https://")
        assert entry["level"] in (*service.LEVELS, None) and entry["tags"]
    assert any("CKA" in e["title"] for e in entries)


def test_parse_answer_keeps_only_valid() -> None:
    bad: list[Any] = [
        {**GOOD, "url": "http://non-securise.example"},
        {**GOOD, "kind": "masterclass"},
        {**GOOD, "title": ""},
        "pas un objet",
    ]
    found = service.parse_answer(answer([GOOD, *bad]))
    assert [f.url for f in found] == [GOOD["url"]]
    assert service.parse_answer("rien") == [] and service.parse_answer("<reponse>{</reponse>") == []


async def test_catalog_filter_and_marks(rt: Runtime) -> None:
    app = create_app(rt.settings, rt)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        everything = (await api.get("/api/trainings")).json()
        assert everything["domain_keywords"] == KEYWORDS and everything["can_suggest"]
        assert len(everything["items"]) == len(service.catalog())
        # Les plus proches du domaine d'abord : la CKA trouve les deux mots-clés.
        assert "CKA" in everything["items"][0]["title"]
        mine = (await api.get("/api/trainings", params={"domain_only": True})).json()["items"]
        assert mine and all(t["matched"] for t in mine)
        aws = next(t for t in everything["items"] if "Solutions Architect" in t["title"])
        assert aws["id"] not in {t["id"] for t in mine}

        cka = everything["items"][0]
        mark = await api.put(
            f"/api/trainings/{cka['id']}/mark",
            json={"status": "in_progress", "progress": " module 4/12 ", "certified": True},
        )
        assert mark.json() == {
            "status": "in_progress",
            "progress": "module 4/12",
            "done_at": None,
            "certified": None,
            "chunk_id": None,
            "funding_status": None,
            "funding_requested_at": None,
        }
        done = await api.put(
            f"/api/trainings/{aws['id']}/mark",
            json={"status": "done", "done_at": "2026-09-30", "certified": True},
        )
        assert done.json()["certified"] is True
        # Suivie, la formation AWS reste visible même filtrée sur « Mon domaine ».
        mine = (await api.get("/api/trainings", params={"domain_only": True})).json()["items"]
        assert aws["id"] in {t["id"] for t in mine}
        assert (await api.delete(f"/api/trainings/{aws['id']}/mark")).status_code == 204
        assert (
            await api.put("/api/trainings/999999/mark", json={"status": "done"})
        ).status_code == 404


async def test_suggest_keep_and_dismiss(rt: Runtime, monkeypatch: pytest.MonkeyPatch) -> None:
    second = {**GOOD, "title": "Autre", "url": "https://formation.example/autre"}
    fake = FakeClient(answer([GOOD, second]))
    monkeypatch.setattr(scoring, "make_client", lambda _settings: fake)
    app = create_app(rt.settings, rt)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        result = await api.post("/api/trainings/suggest")
        assert result.json() == {"added": 2}
        sent = fake.calls[0]["messages"][0]["content"]
        assert "Kubernetes, CKA" in sent and "fr, en" in sent
        assert "Certified Kubernetes Administrator" in sent  # déjà connues, pas reproposées
        items = (await api.get("/api/trainings")).json()["items"]
        ai = {t["url"]: t for t in items if t["origin"] == "ai"}
        assert set(ai) == {GOOD["url"], second["url"]}
        assert not ai[GOOD["url"]]["verified"]
        kept = ai[GOOD["url"]]["id"]
        assert (
            await api.post(f"/api/trainings/{kept}/review", json={"keep": True})
        ).status_code == 204
        await api.post(f"/api/trainings/{ai[second['url']]['id']}/review", json={"keep": False})
        items = (await api.get("/api/trainings")).json()["items"]
        urls = {t["url"]: t for t in items}
        assert urls[GOOD["url"]]["verified"] and second["url"] not in urls
        # Une seconde recherche qui repropose l'écartée ne la fait pas revenir.
        assert (await api.post("/api/trainings/suggest")).json() == {"added": 0}
        catalog_id = next(t["id"] for t in items if t["origin"] == "catalog")
        assert (
            await api.post(f"/api/trainings/{catalog_id}/review", json={"keep": False})
        ).status_code == 404
    async with rt.sessionmaker() as session:
        calls = list(await session.scalars(select(LlmCall.purpose)))
        dismissed = await session.scalar(
            select(Training.dismissed).where(Training.url == second["url"])
        )
    assert calls == ["training", "training"] and dismissed


async def test_suggest_unavailable(rt: Runtime) -> None:
    async with rt.engine.begin() as conn:
        await conn.execute(text("UPDATE profiles SET preferences = '{}'::jsonb WHERE is_main"))
    app = create_app(rt.settings, rt)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        response = await api.post("/api/trainings/suggest")
    # Sans offre notée ni mots-clés enregistrés : rien à chercher.
    assert response.status_code == 409 and "domaine" in response.json()["detail"]


async def test_trainings_follow_the_profile(rt: Runtime, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeClient(answer([GOOD]))
    monkeypatch.setattr(scoring, "make_client", lambda _settings: fake)
    app = create_app(rt.settings, rt)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        created = await api.post(
            "/api/profiles", json={"name": "Test infirmière", "domain_keywords": ["soins"]}
        )
        nurse = {
            "X-Jobbot-Profile": str(
                next(p["id"] for p in created.json()["items"] if not p["is_main"])
            )
        }
        main_items = (await api.get("/api/trainings")).json()["items"]
        cka = main_items[0]["id"]
        await api.put(f"/api/trainings/{cka}/mark", json={"status": "interested"})

        # Suivi par profil : l'intérêt du profil principal n'apparaît pas chez l'infirmière.
        nurse_page = (await api.get("/api/trainings", headers=nurse)).json()
        assert nurse_page["domain_keywords"] == ["soins"]
        assert next(t for t in nurse_page["items"] if t["id"] == cka)["mark"] is None

        # Suggestion faite pour l'infirmière : visible chez elle seulement.
        assert (await api.post("/api/trainings/suggest", headers=nurse)).json() == {"added": 1}
        assert "soins" in fake.calls[0]["messages"][0]["content"]
        nurse_ai = [
            t
            for t in (await api.get("/api/trainings", headers=nurse)).json()["items"]
            if t["origin"] == "ai"
        ]
        assert [t["url"] for t in nurse_ai] == [GOOD["url"]]
        assert all(
            t["origin"] == "catalog" for t in (await api.get("/api/trainings")).json()["items"]
        )
        # Le profil principal ne peut ni la suivre ni la trier.
        suggestion = nurse_ai[0]["id"]
        assert (
            await api.put(f"/api/trainings/{suggestion}/mark", json={"status": "done"})
        ).status_code == 404
        assert (
            await api.post(f"/api/trainings/{suggestion}/review", json={"keep": True})
        ).status_code == 404
        # La même formation peut aussi être proposée au profil principal.
        assert (await api.post("/api/trainings/suggest")).json() == {"added": 1}
    async with rt.engine.begin() as conn:
        await conn.execute(text("DELETE FROM profiles WHERE NOT is_main"))


async def test_finished_training_becomes_a_profile_block(rt: Runtime) -> None:
    app = create_app(rt.settings, rt)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        cka = (await api.get("/api/trainings")).json()["items"][0]
        block = {
            "title": " Certified Kubernetes Administrator (CNCF) ",
            "content": "Certification obtenue en septembre 2026.",
            "tags": ["Kubernetes", "kubernetes", " CKA "],
        }
        url = f"/api/trainings/{cka['id']}/profile-block"
        # Pas encore terminée : rien n'est créé.
        await api.put(f"/api/trainings/{cka['id']}/mark", json={"status": "in_progress"})
        assert (await api.post(url, json=block)).status_code == 409

        await api.put(
            f"/api/trainings/{cka['id']}/mark",
            json={"status": "done", "done_at": "2026-09-30", "certified": True},
        )
        added = await api.post(url, json=block)
        assert added.status_code == 201
        chunk_id = added.json()["chunk_id"]
        async with rt.sessionmaker() as session:
            chunk = await session.get(ProfileChunk, chunk_id)
            assert chunk is not None
            assert (chunk.kind, chunk.title, chunk.tags) == (
                "formation",
                "Certified Kubernetes Administrator (CNCF)",
                ["Kubernetes", "CKA"],
            )
        # Le lien reste après un nouveau marquage, et apparaît dans la liste.
        again = await api.put(
            f"/api/trainings/{cka['id']}/mark", json={"status": "done", "certified": True}
        )
        assert again.json()["chunk_id"] == chunk_id
        listed = next(
            t for t in (await api.get("/api/trainings")).json()["items"] if t["id"] == cka["id"]
        )
        assert listed["mark"]["chunk_id"] == chunk_id

        # Profil d'essai : les blocs appartiennent au profil principal.
        created = await api.post("/api/profiles", json={"name": "Test", "domain_keywords": []})
        trial = {
            "X-Jobbot-Profile": str(
                next(p["id"] for p in created.json()["items"] if not p["is_main"])
            )
        }
        await api.put(f"/api/trainings/{cka['id']}/mark", json={"status": "done"}, headers=trial)
        assert (await api.post(url, json=block, headers=trial)).status_code == 409
    async with rt.engine.begin() as conn:
        await conn.execute(text("DELETE FROM profiles WHERE NOT is_main"))
        await conn.execute(
            text("DELETE FROM profile_chunks WHERE id = :id").bindparams(id=chunk_id)
        )


async def test_funding_request_argument_status_and_reminder(rt: Runtime) -> None:
    now = datetime.now(UTC)
    async with admin_engine().begin() as conn:
        await conn.execute(text("TRUNCATE offers, notifications CASCADE"))
    async with rt.sessionmaker.begin() as session:
        for key, title, company, asks, days in [
            ("f1", "Ingénieur DevOps", "Consort Group", ["Kubernetes", "AWS"], 2),
            ("f2", "Cloud Engineer", "Swisscom", ["Certification CKA"], 10),
            ("f3", "Comptable", "Fiduciaire SA", ["Excel"], 3),
            ("f4", "SRE", "Ancienne SA", ["Kubernetes"], 200),
        ]:
            offer = Offer(
                fingerprint=key,
                title=title,
                company=company,
                status="to_review",
                first_seen_at=now - timedelta(days=days),
                last_seen_at=now,
            )
            session.add(offer)
            await session.flush()
            session.add(
                Evaluation(
                    offer_id=offer.id,
                    filter_passed=True,
                    criteria_hash="x",
                    keywords_asks=[{"text": a, "covered": False} for a in asks],
                )
            )
    app = create_app(rt.settings, rt)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        cka = (await api.get("/api/trainings")).json()["items"][0]
        found = (await api.get(f"/api/trainings/{cka['id']}/funding-request")).json()
        # 90 derniers jours seulement ; la plus récente d'abord.
        assert found["offers"] == 2
        assert [e["company"] for e in found["examples"]] == ["Consort Group", "Swisscom"]
        assert set(found["matched"]) <= set(cka["tags"]) and found["matched"]

        url = f"/api/trainings/{cka['id']}/funding"
        assert (await api.put(url, json={"status": "requested"})).status_code == 409
        await api.put(f"/api/trainings/{cka['id']}/mark", json={"status": "interested"})
        asked = (await api.put(url, json={"status": "requested"})).json()
        assert asked["funding_status"] == "requested" and asked["funding_requested_at"]

        # Relance : une fois, 14 jours après la demande.
        assert await funding.notify_funding(rt) == 0
        async with rt.sessionmaker.begin() as session:
            mark = await session.scalar(
                select(TrainingMark).where(TrainingMark.training_id == cka["id"])
            )
            assert mark is not None
            mark.funding_requested_at = local_today() - timedelta(days=15)
        assert await funding.notify_funding(rt) == 1
        assert await funding.notify_funding(rt) == 0
        async with rt.sessionmaker() as session:
            [alert] = (await session.scalars(select(Notification))).all()
        assert alert.kind == "training_funding" and cka["title"] in alert.title

        accepted = (await api.put(url, json={"status": "accepted"})).json()
        assert accepted["funding_status"] == "accepted"
        listed = next(
            t for t in (await api.get("/api/trainings")).json()["items"] if t["id"] == cka["id"]
        )
        assert listed["mark"]["funding_status"] == "accepted"
        cleared = (await api.put(url, json={"status": None})).json()
        assert cleared["funding_status"] is None and cleared["funding_requested_at"] is None
    async with admin_engine().begin() as conn:
        await conn.execute(text("TRUNCATE offers, notifications CASCADE"))
