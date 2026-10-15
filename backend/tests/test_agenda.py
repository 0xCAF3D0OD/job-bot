"""Tes dates dans ton agenda (docs/40) : fichier par entretien, abonnement à jeton secret."""

from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from jobbot.agenda import ics, service
from jobbot.api.app import create_app
from jobbot.db.models import Application, Interview
from jobbot.followups.service import local_today
from jobbot.runtime import Runtime
from jobbot.settings import Settings

from .conftest import make_settings

TRUNCATE = "TRUNCATE calendar_tokens, applications, interviews, orp_months CASCADE"


@pytest.fixture
async def api(runtime: Runtime, settings: Settings) -> AsyncIterator[AsyncClient]:
    async with runtime.engine.begin() as conn:
        await conn.execute(text(TRUNCATE))
    app = create_app(settings, runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    async with runtime.engine.begin() as conn:
        await conn.execute(text(TRUNCATE))


@pytest.fixture
async def secured() -> AsyncIterator[AsyncClient]:
    """Connexion obligatoire : l'abonnement passe par son jeton seulement."""
    runtime = Runtime.create(make_settings(auth_enabled=True))
    app = create_app(runtime.settings, runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    await runtime.dispose()


def test_ics_escapes_and_folds() -> None:
    assert ics.escape("a,b;c\\d\ne") == "a\\,b\\;c\\\\d\\ne"
    lines = ics.fold("DESCRIPTION:" + "é" * 80)
    assert all(len(line.encode()) <= 75 for line in lines)
    assert lines[1].startswith(" ")
    body = ics.calendar([ics.Event(uid="u", summary="Jour", start=date(2026, 11, 5))])
    assert body.startswith("BEGIN:VCALENDAR\r\n") and body.endswith("END:VCALENDAR\r\n")
    assert "DTSTART;VALUE=DATE:20261105\r\n" in body and "DTEND;VALUE=DATE:20261106" in body


async def test_interview_file_and_subscription(
    api: AsyncClient, secured: AsyncClient, runtime: Runtime
) -> None:
    today = local_today()
    interview_at = datetime.now(UTC).replace(microsecond=0) + timedelta(days=2)
    async with runtime.sessionmaker.begin() as session:
        meeting = Application(
            sent_at=today - timedelta(days=4),
            method="electronique",
            company="Exemple, SA",
            job_title="DevOps Engineer",
            orp_month=f"{today:%Y-%m}",
            status="entretien",
            interview_at=interview_at,
            company_address="Rue secrète 1",
            contact_name="Marie Secret",
        )
        waiting = Application(
            sent_at=today - timedelta(days=3),
            method="electronique",
            company="Autre SA",
            job_title="SRE",
            orp_month=f"{today:%Y-%m}",
        )
        session.add_all([meeting, waiting])
        await session.flush()
        session.add(
            Interview(
                application_id=meeting.id,
                held_at=today,
                kind="rh",
                rating=4,
                next_step="reponse",
                next_step_at=today + timedelta(days=5),
            )
        )
        meeting_id = meeting.id

    single = await api.get(
        f"/api/applications/{meeting_id}/interview.ics", params={"origin": "javascript:alert(1)"}
    )
    assert "URL:http://test/candidatures/suivi" in single.text  # adresse refusée : la requête
    assert single.headers["content-type"].startswith("text/calendar")
    assert 'filename="entretien-exemple-sa.ics"' in single.headers["content-disposition"]
    assert "SUMMARY:Entretien \u2013 Exemple\\, SA" in single.text
    assert "TRIGGER:-P1D" in single.text and "TRIGGER:-PT2H" in single.text
    assert (await api.get(f"/api/applications/{meeting_id + 999}/interview.ics")).status_code == 404

    created = (
        await api.post(
            "/api/agenda/tokens", json={"name": "iPhone", "origin": "https://moi.tunnel.ms"}
        )
    ).json()
    # L'adresse donnée par le navigateur (tunnel, https) sert à l'abonnement et aux liens.
    assert created["url"].startswith("https://moi.tunnel.ms/api/agenda/feed/jba_")
    path = created["url"].removeprefix("https://moi.tunnel.ms")
    assert path.startswith("/api/agenda/feed/jba_")
    # Sans connexion : l'abonnement est lisible avec son jeton, et seulement lui.
    feed = await secured.get(path)
    assert feed.status_code == 200
    body = feed.text
    assert "Entretien \u2013 Exemple\\, SA" in body
    assert "Relancer Autre SA ?" in body
    assert "Suite attendue \u2013 Exemple\\, SA" in body
    assert "Preuves ORP d" in body and "TRIGGER:-P3D" in body
    assert "URL:https://moi.tunnel.ms/candidatures/suivi" in body
    # Le minimum : ni adresse, ni contact.
    assert "Rue secrète" not in body and "Marie" not in body
    assert (await secured.get("/api/agenda/feed/jba_faux.ics")).status_code == 404
    assert (await secured.get("/api/agenda/tokens")).status_code == 401

    assert [t["name"] for t in (await api.get("/api/agenda/tokens")).json()] == ["iPhone"]
    assert (await api.delete(f"/api/agenda/tokens/{created['id']}")).status_code == 204
    assert (await secured.get(path)).status_code == 404


def test_month_elision() -> None:
    assert service._of_month("2026-10") == "d'octobre 2026"
    assert service._of_month("2026-09") == "de septembre 2026"
