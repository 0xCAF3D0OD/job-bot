"""Profils d'essai (docs/17) : Actualités par profil, création, duplication, suppression."""

import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from jobbot.api.app import create_app
from jobbot.db.models import NewsItem, NewsSource, ProfileSource
from jobbot.runtime import Runtime
from jobbot.settings import Settings

RESET = [
    "TRUNCATE news_items",
    "DELETE FROM news_sources WHERE name LIKE 'Test %'",
    "DELETE FROM profiles WHERE NOT is_main",
    "UPDATE profiles SET preferences = '{}'::jsonb, news_seen_at = NULL WHERE is_main",
]


@pytest.fixture
async def api(
    runtime: Runtime, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[AsyncClient]:
    async def fake_enqueue(_settings: Settings, _name: str) -> bool:
        return True

    monkeypatch.setattr("jobbot.api.routes.news.enqueue", fake_enqueue)
    async with runtime.engine.begin() as conn:
        for statement in RESET:
            await conn.execute(text(statement))
    app = create_app(settings, runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    async with runtime.engine.begin() as conn:
        for statement in RESET:
            await conn.execute(text(statement))


def as_profile(profile_id: int) -> dict[str, str]:
    return {"X-Jobbot-Profile": str(profile_id)}


async def test_profiles_crud(api: AsyncClient) -> None:
    listed = (await api.get("/api/profiles")).json()
    main = next(p for p in listed["items"] if p["is_main"])
    assert listed["current_id"] == main["id"] and len(listed["items"]) == 1

    created = await api.post(
        "/api/profiles",
        json={
            "name": "Infirmière à Lausanne",
            "occupation": "infirmière en soins généraux",
            "domain_keywords": ["soins", "infirmière"],
            "languages": ["fr"],
            "countries": ["CH"],
        },
    )
    assert created.status_code == 201
    nurse = next(p for p in created.json()["items"] if not p["is_main"])
    # Il suit au départ les articles « marché de l'emploi » du catalogue (SECO, RTS, Le Temps).
    assert nurse["sources"] == 3 and nurse["domain_keywords"] == ["soins", "infirmière"]

    mine = (await api.get("/api/profiles", headers=as_profile(nurse["id"]))).json()
    assert mine["current_id"] == nurse["id"]
    # Profil inconnu : retour au principal.
    assert (await api.get("/api/profiles", headers=as_profile(999999))).json()[
        "current_id"
    ] == main["id"]

    prefs = (await api.get("/api/news/preferences", headers=as_profile(nurse["id"]))).json()
    assert prefs == {
        "domain_keywords": ["soins", "infirmière"],
        "domain_only": True,
        "countries": ["CH"],
        "languages": ["fr"],
    }

    copy = (await api.post(f"/api/profiles/{nurse['id']}/duplicate")).json()["items"]
    duplicate = next(p for p in copy if p["name"] == "Infirmière à Lausanne (copie)")
    assert duplicate["sources"] == 3 and duplicate["domain_keywords"] == ["soins", "infirmière"]
    renamed = await api.patch(f"/api/profiles/{duplicate['id']}", json={"name": "Variante"})
    assert any(p["name"] == "Variante" for p in renamed.json()["items"])
    assert (await api.delete(f"/api/profiles/{main['id']}")).status_code == 409
    left = (await api.delete(f"/api/profiles/{duplicate['id']}")).json()["items"]
    assert {p["id"] for p in left} == {main["id"], nurse["id"]}


async def test_news_follow_the_profile(api: AsyncClient, runtime: Runtime) -> None:
    nurse_id = next(
        p["id"]
        for p in (await api.post("/api/profiles", json={"name": "Test infirmière"})).json()["items"]
        if not p["is_main"]
    )
    main_id = (await api.get("/api/profiles")).json()["current_id"]
    now = datetime.now(UTC)
    async with runtime.sessionmaker.begin() as session:
        shared = NewsSource(
            kind="articles",
            name="Test commune",
            url="https://c",
            feed_url="https://t.example/c",
            fetched_at=now,
        )
        own = NewsSource(
            kind="articles",
            name="Test soins",
            url="https://s",
            feed_url="https://t.example/s",
            fetched_at=now,
        )
        session.add_all([shared, own])
        await session.flush()
        session.add_all(
            [
                ProfileSource(profile_id=main_id, source_id=shared.id),
                ProfileSource(profile_id=nurse_id, source_id=shared.id),
                ProfileSource(profile_id=nurse_id, source_id=own.id),
                NewsItem(
                    source_id=shared.id,
                    title="Chômage stable",
                    url="https://t.example/1",
                    published_at=now,
                ),
                NewsItem(
                    source_id=own.id,
                    title="Pénurie de soignants",
                    url="https://t.example/2",
                    published_at=now,
                ),
            ]
        )
        shared_id, own_id = shared.id, own.id

    def titles(page: dict) -> set[str]:
        return {i["title"] for i in page["items"]}

    main_page = (await api.get("/api/news", params={"limit": 100})).json()
    nurse_page = (
        await api.get("/api/news", params={"limit": 100}, headers=as_profile(nurse_id))
    ).json()
    assert "Pénurie de soignants" not in titles(main_page)
    assert {"Chômage stable", "Pénurie de soignants"} <= titles(nurse_page)
    assert nurse_page["new_articles"] >= 2

    # « Vu » et préférences par profil.
    await api.post("/api/news/seen", headers=as_profile(nurse_id))
    assert (await api.get("/api/news", headers=as_profile(nurse_id))).json()["new_articles"] == 0
    assert (await api.get("/api/news")).json()["new_articles"] >= 1
    await api.put(
        "/api/news/preferences",
        headers=as_profile(nurse_id),
        json={"domain_keywords": ["soins"], "domain_only": True, "countries": [], "languages": []},
    )
    assert (await api.get("/api/news/preferences")).json()["domain_keywords"] != ["soins"]

    # Pause par profil ; la source reste relevée pour l'autre.
    await api.patch(
        f"/api/news/sources/{shared_id}", headers=as_profile(nurse_id), json={"active": False}
    )
    assert "Chômage stable" not in titles(
        (await api.get("/api/news", params={"limit": 100}, headers=as_profile(nurse_id))).json()
    )
    assert "Chômage stable" in titles((await api.get("/api/news", params={"limit": 100})).json())
    # Une source d'un autre profil n'est ni modifiable ni retirable ici.
    assert (
        await api.patch(f"/api/news/sources/{own_id}", json={"active": False})
    ).status_code == 404

    # Retirée par le seul profil qui la suit : effacée avec ses contenus.
    await api.delete(f"/api/news/sources/{own_id}", headers=as_profile(nurse_id))
    await api.delete(f"/api/news/sources/{shared_id}", headers=as_profile(nurse_id))
    async with runtime.sessionmaker() as session:
        names = set(
            await session.scalars(select(NewsSource.name).where(NewsSource.name.like("Test %")))
        )
    assert names == {"Test commune"}

    # Ajout d'une source déjà connue d'un autre profil : réutilisée, pas de doublon.
    catalog = (await api.get("/api/news/catalog", headers=as_profile(nurse_id))).json()["sources"]
    assert next(s for s in catalog if s["id"] == "seco")["added"]
    assert not next(s for s in catalog if s["id"] == "techworld-nana")["added"]
    added = await api.post("/api/news/catalog/techworld-nana", headers=as_profile(nurse_id))
    assert added.status_code == 201
    async with runtime.sessionmaker() as session:
        count = len(
            list(
                await session.scalars(
                    select(NewsSource.id).where(NewsSource.name == "TechWorld with Nana")
                )
            )
        )
    assert count == 1


async def test_keywords_proposed_from_occupation(
    runtime: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    from jobbot.llm.client import RawResult
    from jobbot.llm.pricing import Usage
    from jobbot.profiles import keywords
    from jobbot.scoring import service as scoring

    from .conftest import make_settings

    calls: list[dict] = []

    class Fake:
        async def score(self, params: dict) -> RawResult:
            calls.append(params)
            found = ["infirmière", "Infirmière", "EMS", 3, "soins infirmiers"]
            text_ = f"<reponse>{json.dumps({'keywords': found})}</reponse>"
            return RawResult(text_, keywords.MODEL, Usage(300, 0, 0, 60), "end_turn")

    monkeypatch.setattr(scoring, "make_client", lambda _settings: Fake())
    rt = Runtime.create(make_settings(anthropic_api_key="sk-test"))
    try:
        app = create_app(rt.settings, rt)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
            assert (await api.get("/api/profiles/keywords")).json()["available"]
            proposed = await api.post(
                "/api/profiles/keywords", json={"occupation": "infirmière <b>"}
            )
        assert proposed.json() == {
            "keywords": ["infirmière", "EMS", "soins infirmiers"],
            "available": True,
        }
        assert calls[0]["messages"][0]["content"] == "<metier>infirmière b</metier>"
        assert "tools" not in calls[0]
    finally:
        await rt.dispose()


async def test_keywords_without_api_key(api: AsyncClient) -> None:
    assert not (await api.get("/api/profiles/keywords")).json()["available"]
    assert (
        await api.post("/api/profiles/keywords", json={"occupation": "infirmière"})
    ).status_code == 409
