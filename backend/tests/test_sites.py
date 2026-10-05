"""Sites suivis et lecture des alertes par l'IA (docs/11 §2). Sans réseau ni IA réelle."""

import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from email.message import EmailMessage
from email.utils import format_datetime
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text, update

from jobbot.api.app import create_app
from jobbot.collect import service
from jobbot.db.models import LlmCall, OfferLink, Search, Site
from jobbot.llm import alert
from jobbot.llm.client import RawResult
from jobbot.llm.pricing import Usage
from jobbot.mail.message import parse_email
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring

from .conftest import make_settings
from .test_collect import FakeMailbox, mailbox

__all__ = ["mailbox"]
T0 = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
JOB = "https://www.linkedin.com/comm/jobs/view/4012345678/?trackingId=abc&refId=kevin"
JOBS_CH = "https://www.jobs.ch/fr/offres-emplois/detail/0f1e2d3c-4b5a-6978-8a9b-0c1d2e3f4a5b/?source=alert"


def linkedin_email(message_id: str = "<l1@linkedin.com>") -> bytes:
    msg = EmailMessage()
    msg["From"] = "LinkedIn Job Alerts <jobalerts-noreply@linkedin.com>"
    msg["To"] = "alertes@example.com"
    msg["Subject"] = "Platform engineer : 2 nouvelles offres"
    msg["Message-ID"] = message_id
    msg["Date"] = format_datetime(T0)
    msg.set_content("Bonjour Jean Exemple, voici vos offres. Contact : jean@example.org")
    msg.add_alternative(
        f'<html><body><p>Bonjour Jean Exemple</p><a href="{JOB}">Platform engineer</a>'
        f'<p>Acme SA · Lausanne</p><a href="https://www.linkedin.com/settings">Réglages</a>'
        "</body></html>",
        subtype="html",
    )
    return msg.as_bytes()


def test_canonical_links() -> None:
    assert alert.canonical(JOB) == ("https://www.linkedin.com/jobs/view/4012345678/", "4012345678")
    assert alert.canonical(JOBS_CH) == (
        "https://www.jobs.ch/fr/offres-emplois/detail/0f1e2d3c-4b5a-6978-8a9b-0c1d2e3f4a5b/",
        "0f1e2d3c-4b5a-6978-8a9b-0c1d2e3f4a5b",
    )
    assert alert.canonical("https://Exemple.ch/job?id=1#x") == ("https://exemple.ch/job", None)


def test_prepare_hides_personal_data() -> None:
    email = parse_email(linkedin_email(), fallback_received=T0)
    prepared = alert.prepare(email, ["Jean Exemple"])
    assert "Jean Exemple" not in prepared.text and "jean@example.org" not in prepared.text
    assert prepared.links[0] == JOB
    params = json.dumps(alert.request_params(prepared, email.subject), ensure_ascii=False)
    assert "Jean Exemple" not in params and "[1] " + JOB in params
    assert alert.request_params(prepared, None)["model"] == "claude-haiku-4-5"


def test_parse_output_keeps_only_real_links() -> None:
    prepared = alert.AlertInput(text="x", links=[JOB, JOBS_CH])
    output = json.dumps(
        {
            "offers": [
                {
                    "title": "Platform engineer",
                    "company": "Acme SA",
                    "location": "Lausanne",
                    "rate": "80-100 %",
                    "link": 1,
                },
                {"title": "Inventée", "company": None, "location": None, "rate": None, "link": 9},
                {"title": "Doublon", "company": None, "location": None, "rate": None, "link": 1},
            ]
        }
    )
    parsed = alert.parse_output(output, prepared, "Alerte")
    assert [(o.title, o.location, o.external_id) for o in parsed.offers] == [
        ("Platform engineer", "Lausanne 80-100 %", "4012345678")
    ]


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def score(self, params: dict[str, Any]) -> RawResult:
        self.calls.append(params)
        body = {
            "offers": [
                {
                    "title": "Platform engineer",
                    "company": "Acme SA",
                    "location": "Lausanne",
                    "rate": None,
                    "link": 1,
                }
            ]
        }
        return RawResult(
            json.dumps(body), "claude-haiku-4-5-20251001", Usage(3000, 0, 0, 200), "end_turn"
        )


@pytest.fixture
async def rt(tmp_path: Any) -> AsyncIterator[Runtime]:
    runtime = Runtime.create(
        make_settings(
            imap_user="alertes@example.com",
            imap_password="secret-de-test",
            storage_path=tmp_path,
            anthropic_api_key="sk-test",
        )
    )
    async with runtime.engine.begin() as conn:
        await conn.execute(text("TRUNCATE searches, offers, job_runs, llm_calls CASCADE"))
        await conn.execute(
            text(
                "DELETE FROM sites WHERE NOT builtin"
                " AND slug NOT IN ('jobsch', 'linkedin', 'jobroom')"
            )
        )
        await conn.execute(text("UPDATE sites SET active = slug <> 'jobroom'"))
    yield runtime
    async with runtime.engine.begin() as conn:
        await conn.execute(text("UPDATE sites SET active = slug <> 'jobroom'"))
    await runtime.dispose()


async def test_linkedin_alert_read_by_ai(
    rt: Runtime, mailbox: FakeMailbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeClient()
    monkeypatch.setattr(scoring, "make_client", lambda _settings: fake)
    mailbox.add(linkedin_email(), "<l1@linkedin.com>")
    await service.collect(rt)
    async with rt.sessionmaker() as session:
        [search] = (await session.scalars(select(Search))).all()
        assert (search.source, search.parse_status, search.parser_version) == (
            "linkedin",
            "parsed",
            "alert-v2",
        )
        [link] = (await session.scalars(select(OfferLink))).all()
        assert (link.source, link.url) == (
            "linkedin",
            "https://www.linkedin.com/jobs/view/4012345678/",
        )
        assert list(await session.scalars(select(LlmCall.purpose))) == ["alert"]


async def test_paused_site_and_no_key(
    rt: Runtime, mailbox: FakeMailbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeClient()
    monkeypatch.setattr(scoring, "make_client", lambda _settings: fake)
    async with rt.sessionmaker.begin() as session:
        await session.execute(update(Site).where(Site.slug == "linkedin").values(active=False))
    mailbox.add(linkedin_email(), "<l1@linkedin.com>")
    await service.collect(rt)
    async with rt.sessionmaker() as session:
        [search] = (await session.scalars(select(Search))).all()
    assert (search.source, search.parse_status, search.error) == (
        "linkedin",
        "unrecognized",
        "site en pause",
    )
    assert fake.calls == []

    # Le site réactivé, « Relire » traite l'alerte gardée.
    async with rt.sessionmaker.begin() as session:
        await session.execute(update(Site).where(Site.slug == "linkedin").values(active=True))
    app = create_app(rt.settings, rt)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        reread = (await api.post("/api/sites/reread")).json()
    assert reread["updated"] == 1 and reread["new_offers"] == 1


async def test_sites_api(rt: Runtime) -> None:
    app = create_app(rt.settings, rt)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        sites = (await api.get("/api/sites")).json()
        assert {s["slug"]: s["reader"] for s in sites}["linkedin"] == "ai"
        assert [s["slug"] for s in sites if s["builtin"]] == ["jobup", "indeed"]

        created = await api.post(
            "/api/sites",
            json={
                "name": "JobScout24",
                "senders": [" Alerts@JobScout24.ch "],
                "url": "https://www.jobscout24.ch",
            },
        )
        assert created.status_code == 201
        added = next(s for s in created.json() if s["slug"] == "jobscout24")
        assert added["senders"] == ["alerts@jobscout24.ch"] and added["active"]
        assert (
            await api.post("/api/sites", json={"name": "JobScout24", "senders": ["x.ch"]})
        ).status_code == 409
        assert (
            await api.post("/api/sites", json={"name": "Bad", "senders": ["pas une adresse"]})
        ).status_code == 422

        paused = (await api.patch(f"/api/sites/{added['id']}", json={"active": False})).json()
        assert not next(s for s in paused if s["slug"] == "jobscout24")["active"]
        jobup = next(s for s in sites if s["slug"] == "jobup")
        assert (await api.delete(f"/api/sites/{jobup['id']}")).status_code == 409
        remaining = (await api.delete(f"/api/sites/{added['id']}")).json()
        assert all(s["slug"] != "jobscout24" for s in remaining)
