"""Profils d'essai (docs/17) : « Mon domaine » par profil, création, duplication, suppression."""

import json
from collections.abc import AsyncIterator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from jobbot.api.app import create_app
from jobbot.runtime import Runtime
from jobbot.settings import Settings

RESET = [
    "DELETE FROM profiles WHERE NOT is_main",
    "UPDATE profiles SET preferences = '{}'::jsonb WHERE is_main",
]


@pytest.fixture
async def api(runtime: Runtime, settings: Settings) -> AsyncIterator[AsyncClient]:
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
    assert nurse["domain_keywords"] == ["soins", "infirmière"]

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
    assert duplicate["domain_keywords"] == ["soins", "infirmière"]
    renamed = await api.patch(f"/api/profiles/{duplicate['id']}", json={"name": "Variante"})
    assert any(p["name"] == "Variante" for p in renamed.json()["items"])
    assert (await api.delete(f"/api/profiles/{main['id']}")).status_code == 409
    left = (await api.delete(f"/api/profiles/{duplicate['id']}")).json()["items"]
    assert {p["id"] for p in left} == {main["id"], nurse["id"]}


async def test_domain_follows_the_profile(api: AsyncClient) -> None:
    """« Mon domaine » est propre à chaque profil (docs/17)."""
    created = await api.post(
        "/api/profiles",
        json={"name": "Infirmière", "domain_keywords": ["soins"], "languages": [], "countries": []},
    )
    nurse_id = next(p["id"] for p in created.json()["items"] if not p["is_main"])
    nurse = (await api.get("/api/news/preferences", headers=as_profile(nurse_id))).json()
    await api.put(
        "/api/news/preferences",
        headers=as_profile(nurse_id),
        json={**nurse, "domain_keywords": ["soins", "EMS"]},
    )
    assert (await api.get("/api/news/preferences", headers=as_profile(nurse_id))).json()[
        "domain_keywords"
    ] == ["soins", "EMS"]
    assert (await api.get("/api/news/preferences")).json()["domain_keywords"] != ["soins", "EMS"]


async def test_keywords_proposed_from_occupation(
    runtime: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    from jobbot.llm.client import RawResult
    from jobbot.llm.pricing import Usage
    from jobbot.profiles import keywords
    from jobbot.scoring import service as scoring

    from .conftest import make_settings

    calls: list[dict[str, Any]] = []

    class Fake:
        async def score(self, params: dict[str, Any]) -> RawResult:
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
