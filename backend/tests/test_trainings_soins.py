"""Formations en soins (Kevin, 16.11.2026) : diplômes acceptés, vérification des liens."""

import json
from collections.abc import AsyncIterator

import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from jobbot.api.app import create_app
from jobbot.api.routes import trainings as routes
from jobbot.db.models import ChunkKind, ProfileChunk, Training
from jobbot.runtime import Runtime
from jobbot.trainings import diplomas, links, service

from .conftest import admin_engine, make_settings


@pytest.fixture
async def rt() -> AsyncIterator[Runtime]:
    runtime = Runtime.create(make_settings())
    routes._synced = False
    async with admin_engine().begin() as conn:
        await conn.execute(text("TRUNCATE trainings, profile_chunks CASCADE"))
        await conn.execute(text("DELETE FROM settings WHERE key = 'training_diplomas'"))
        await conn.execute(
            text(
                "UPDATE profiles SET preferences = CAST(:value AS jsonb) WHERE is_main"
            ).bindparams(value=json.dumps({"domain_keywords": ["Soins infirmiers"]}))
        )
    yield runtime
    async with admin_engine().begin() as conn:
        await conn.execute(text("TRUNCATE trainings, profile_chunks CASCADE"))
        await conn.execute(text("DELETE FROM settings WHERE key = 'training_diplomas'"))
        await conn.execute(text("UPDATE profiles SET preferences = '{}'::jsonb WHERE is_main"))
    await runtime.dispose()


def test_catalog_prerequisites_are_known() -> None:
    entries = service.catalog()
    for entry in entries:
        assert set(entry["prerequisites"]) <= set(diplomas.DIPLOMAS)
        assert entry.get("link_status", "ok") in ("ok", "a_reverifier")
    nursing = [e for e in entries if "soins_infirmiers" in e["prerequisites"]]
    assert len(nursing) == 8
    a2 = next(e for e in entries if e["title"].startswith("Certificat (A2)"))
    assert a2["prerequisites"] == ["bachelor_hes_sante", "bachelor_hes_social"]


@pytest.mark.parametrize(
    ("status", "content_type", "body", "expected"),
    [
        (200, "text/html", "<title>CAS Évaluation clinique</title>", "ok"),
        (200, "application/pdf", "", "ok"),
        (404, "text/html", "", "mort"),
        (410, "text/html", "", "mort"),
        (200, "text/html", "<title>Erreur 404 | HEdS La Source</title>", "mort"),
        (200, "text/html", "<title>Page non trouvée</title>", "mort"),
        (500, "text/html", "", "a_reverifier"),
        (503, "text/html", "", "a_reverifier"),
        (200, "text/html", "<h1>Cookie not accepted, cannot continue!</h1>", "a_reverifier"),
        (403, "text/html", "", "a_reverifier"),
    ],
)
def test_link_rules(status: int, content_type: str, body: str, expected: str) -> None:
    assert links.classify(status, content_type, body) == expected


async def test_link_errors_are_rechecked() -> None:
    def broken(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("délai", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(broken)) as client:
        assert await links.check(client, "https://formation.example/") == "a_reverifier"


def test_diploma_detection() -> None:
    F, E = ChunkKind.FORMATION, ChunkKind.EXPERIENCE
    assert diplomas.detect([(F, "Bachelor of Science HES-SO en soins infirmiers", "")]) == {
        "soins_infirmiers",
        "bachelor_hes_sante",
    }
    assert diplomas.detect([(F, "Diplôme d'État infirmier", "IFSI de Lyon, 2015")]) == {
        "soins_infirmiers"
    }
    assert diplomas.detect([(F, "Diplôme ES en soins infirmiers", "")]) == {"soins_infirmiers"}
    assert diplomas.detect([(E, "Infirmier·ère en gériatrie, EMS Les Lilas", "")]) == {
        "soins_infirmiers"
    }
    assert diplomas.detect([(E, "Aide-infirmière", "")]) == set()
    assert diplomas.detect([(F, "Bachelor HES en travail social", "")]) == {"bachelor_hes_social"}
    assert diplomas.detect([(F, "CFC d'employée de commerce", "")]) == set()
    assert diplomas.eligible([], set()) and not diplomas.eligible(["soins_infirmiers"], set())


async def _chunk(runtime: Runtime, kind: str, title: str) -> None:
    async with runtime.sessionmaker.begin() as session:
        session.add(ProfileChunk(kind=kind, title=title, content="", tags=[]))


async def test_nursing_catalog_waits_for_links_then_shows_prerequisites(rt: Runtime) -> None:
    app = create_app(rt.settings, rt)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        page = (await api.get("/api/trainings", params={"domain_only": True})).json()
        # Les 14 fiches attendent la vérification de leur lien.
        assert page["items"] == [] and page["diplomas_detected"] == []

        async with admin_engine().begin() as conn:
            await conn.execute(text("UPDATE trainings SET link_status = 'ok'"))
        page = (await api.get("/api/trainings", params={"domain_only": True})).json()
        cas = next(t for t in page["items"] if t["title"] == "CAS Évaluation clinique infirmière")
        assert cas["prerequisites"] == ["soins_infirmiers"] and not cas["eligible"]
        bls = next(t for t in page["items"] if t["title"].startswith("Réanimation BLS"))
        assert bls["prerequisites"] == [] and bls["eligible"]

        await _chunk(rt, ChunkKind.EXPERIENCE, "Infirmière responsable d'unité de soins")
        page = (await api.get("/api/trainings", params={"domain_only": True})).json()
        assert page["diplomas_detected"] == ["soins_infirmiers"]
        assert all(t["eligible"] for t in page["items"] if "soins_infirmiers" in t["prerequisites"])

        # « J'ai ce diplôme » : déclaré, puis annulé.
        saved = await api.put("/api/trainings/diplomas", json={"diplomas": ["bachelor_hes_social"]})
        assert saved.json() == {
            "detected": ["soins_infirmiers"],
            "declared": ["bachelor_hes_social"],
        }
        a2 = next(
            t
            for t in (await api.get("/api/trainings")).json()["items"]
            if t["title"].startswith("Certificat (A2)")
        )
        assert a2["eligible"]
        assert (
            await api.put("/api/trainings/diplomas", json={"diplomas": ["autre"]})
        ).status_code == 422
        cleared = await api.put("/api/trainings/diplomas", json={"diplomas": []})
        assert cleared.json()["declared"] == []


async def test_link_job_checks_due_catalog_entries(rt: Runtime) -> None:
    app = create_app(rt.settings, rt)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        await api.get("/api/trainings")  # le catalogue est recopié en base

    def answer(request: httpx.Request) -> httpx.Response:
        if "orientation.ch" in str(request.url):
            return httpx.Response(500)
        if "ecolelasource" in str(request.url):
            return httpx.Response(404)
        return httpx.Response(200, headers={"content-type": "text/html"}, text="<title>ok</title>")

    async with (
        httpx.AsyncClient(transport=httpx.MockTransport(answer)) as client,
        rt.sessionmaker.begin() as session,
    ):
        assert await links.check_due(session, client) == len(service.catalog())
    async with rt.sessionmaker.begin() as session:
        rows = {t.url: t for t in await session.scalars(select(Training))}
    orientation = [t for u, t in rows.items() if "orientation.ch" in u]
    assert len(orientation) == 3 and all(t.link_status == "a_reverifier" for t in orientation)
    lasource = [t for u, t in rows.items() if "ecolelasource" in u]
    assert lasource and all(t.link_status == "mort" and t.link_next_check is None for t in lasource)
    chuv = next(t for u, t in rows.items() if "form_ofr_56" in u)
    assert chuv.link_status == "ok" and chuv.link_next_check is not None
    # Rien n'est dû juste après : la prochaine vérification est dans 24 h ou 30 jours.
    async with (
        httpx.AsyncClient(transport=httpx.MockTransport(answer)) as client,
        rt.sessionmaker.begin() as session,
    ):
        assert await links.check_due(session, client) == 0
