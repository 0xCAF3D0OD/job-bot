"""Tri manuel des offres, candidatures, coordonnées et relances (docs/08, 0.5.0-a)."""

from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text, update

from jobbot.api.app import create_app
from jobbot.db.models import Application, Notification, Offer, OfferStatus, Setting
from jobbot.notify import service as notify
from jobbot.notify.service import Message
from jobbot.runtime import Runtime
from jobbot.settings import Settings
from jobbot.worker.jobs import JOBS

from .conftest import make_settings

NOW = datetime(2026, 10, 5, 8, 0, tzinfo=UTC)


@pytest.fixture
async def rt(runtime: Runtime) -> AsyncIterator[Runtime]:
    async with runtime.engine.begin() as conn:
        await conn.execute(
            text("TRUNCATE offers, searches, job_runs, applications, notifications CASCADE")
        )
        await conn.execute(text("DELETE FROM settings WHERE key LIKE 'identity_%'"))
    yield runtime


@pytest.fixture
async def api(rt: Runtime, settings: Settings) -> AsyncIterator[AsyncClient]:
    app = create_app(settings, rt)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


async def add_offer(rt: Runtime, n: int, **extra: Any) -> int:
    async with rt.sessionmaker.begin() as session:
        offer = Offer(
            fingerprint=f"o{n}",
            title=f"Ingénieur DevOps {n}",
            company="Acme SA",
            location="Lausanne, VD",
            first_seen_at=NOW + timedelta(minutes=n),
            last_seen_at=NOW,
            status=extra.pop("status", OfferStatus.TO_REVIEW),
            **extra,
        )
        session.add(offer)
        await session.flush()
        return offer.id


async def offer_status(rt: Runtime, offer_id: int) -> str:
    async with rt.sessionmaker() as session:
        offer = await session.get(Offer, offer_id)
        assert offer is not None
        return offer.status


async def test_manual_status_and_views(api: AsyncClient, rt: Runtime) -> None:
    later = await add_offer(rt, 1)
    ignored = await add_offer(rt, 2)
    preparing = await add_offer(rt, 3)
    for offer_id, new in ((later, "later"), (ignored, "ignored"), (preparing, "preparing")):
        response = await api.patch(f"/api/offers/{offer_id}/status", json={"status": new})
        assert response.json() == {"id": offer_id, "status": new}

    counts = (await api.get("/api/offers")).json()["counts"]
    assert (counts["to_review"], counts["later"], counts["in_progress"], counts["all"]) == (
        0,
        1,
        1,
        3,
    )
    later_view = (await api.get("/api/offers", params={"view": "later"})).json()
    assert [o["id"] for o in later_view["items"]] == [later]

    assert (
        await api.patch(f"/api/offers/{later}/status", json={"status": "applied"})
    ).status_code == 422
    assert (
        await api.patch("/api/offers/999999/status", json={"status": "later"})
    ).status_code == 404


@pytest.mark.parametrize(
    ("rate", "expected"),
    [
        ((100, 100), "plein temps"),
        ((80, 100), "plein temps ou temps partiel (80-100 %)"),
        ((60, 60), "temps partiel (60 %)"),
        ((60, 80), "temps partiel (60-80 %)"),
        ((None, None), None),
    ],
)
async def test_prefill(
    api: AsyncClient, rt: Runtime, rate: tuple[int | None, int | None], expected: str | None
) -> None:
    offer_id = await add_offer(rt, 1, rate_min=rate[0], rate_max=rate[1])
    prefill = (await api.get(f"/api/offers/{offer_id}/application-prefill")).json()
    assert prefill["rate_text"] == expected
    assert (prefill["company"], prefill["job_title"], prefill["method"]) == (
        "Acme SA",
        "Ingénieur DevOps 1",
        "electronique",
    )
    assert prefill["assigned_by_orp"] is False and prefill["sent_at"]


async def test_application_lifecycle(api: AsyncClient, rt: Runtime) -> None:
    offer_id = await add_offer(rt, 1)
    body = {
        "offer_id": offer_id,
        "sent_at": "2026-10-03",
        "company": " Acme SA ",
        "job_title": "Ingénieur DevOps",
        "contact_name": "  ",
        "rate_text": "plein temps",
    }
    created = await api.post("/api/applications", json=body)
    assert created.status_code == 201
    app = created.json()
    assert (app["company"], app["contact_name"], app["orp_month"], app["status"]) == (
        "Acme SA",
        None,
        "2026-10",
        "en_attente",
    )
    assert await offer_status(rt, offer_id) == "applied"
    assert (await api.post("/api/applications", json=body)).status_code == 409
    blocked = await api.patch(f"/api/offers/{offer_id}/status", json={"status": "later"})
    assert blocked.status_code == 409

    updated = await api.put(
        f"/api/applications/{app['id']}",
        json={**body, "status": "entretien", "interview_at": "2026-10-12T09:30:00+02:00"},
    )
    assert updated.json()["status"] == "entretien" and updated.json()["status_at"]

    assert (await api.delete(f"/api/applications/{app['id']}")).status_code == 204
    assert await offer_status(rt, offer_id) == "preparing"


async def test_manual_application_without_offer_and_validation(api: AsyncClient) -> None:
    ok = await api.post(
        "/api/applications",
        json={
            "sent_at": "2026-09-30",
            "company": "Candidature spontanée SA",
            "job_title": "DevOps",
            "method": "ecrit",
        },
    )
    assert ok.status_code == 201 and ok.json()["offer_id"] is None
    blank = await api.post(
        "/api/applications", json={"sent_at": "2026-09-30", "company": "   ", "job_title": "x"}
    )
    assert blank.status_code == 422
    bad_method = await api.post(
        "/api/applications",
        json={"sent_at": "2026-09-30", "company": "A", "job_title": "x", "method": "pigeon"},
    )
    assert bad_method.status_code == 422


async def test_month_list_and_summary(api: AsyncClient, rt: Runtime) -> None:
    for day in ("2026-09-29", "2026-10-01", "2026-10-03"):
        await api.post("/api/applications", json={"sent_at": day, "company": "A", "job_title": day})
    async with rt.sessionmaker.begin() as session:
        await session.execute(
            update(Setting).where(Setting.key == "orp_monthly_target").values(value=20)
        )
    october = (await api.get("/api/applications", params={"month": "2026-10"})).json()
    assert [a["job_title"] for a in october] == ["2026-10-03", "2026-10-01"]
    summary = (await api.get("/api/applications/summary", params={"month": "2026-10"})).json()
    assert summary == {"month": "2026-10", "count": 2, "target": 20}
    assert (await api.get("/api/applications", params={"month": "octobre"})).status_code == 422
    async with rt.sessionmaker.begin() as session:
        await session.execute(
            update(Setting).where(Setting.key == "orp_monthly_target").values(value=None)
        )


async def test_identity_round_trip(api: AsyncClient) -> None:
    empty = (await api.get("/api/identity")).json()
    assert empty == {
        "name": None,
        "street": None,
        "postcode": None,
        "city": None,
        "phone": None,
        "email": None,
    }
    identity = {
        "name": "Jean Exemple",
        "street": "Rue du Test 1",
        "postcode": " 1020 ",
        "city": "Renens",
        "phone": " +41 79 000 00 00 ",
        "email": "",
    }
    saved = (await api.put("/api/identity", json=identity)).json()
    assert saved["phone"] == "+41 79 000 00 00" and saved["email"] is None
    assert saved["postcode"] == "1020"
    assert (await api.get("/api/identity")).json() == saved


async def test_identity_rejects_bad_postcode(api: AsyncClient) -> None:
    response = await api.put("/api/identity", json={"postcode": "10200"})
    assert response.status_code == 422


# --- Relances ------------------------------------------------------------------------


@pytest.fixture
def sent(monkeypatch: pytest.MonkeyPatch) -> list[Message]:
    messages: list[Message] = []

    async def fake_send(_settings: Settings, message: Message) -> None:
        messages.append(message)

    monkeypatch.setattr(notify, "send", fake_send)
    return messages


async def add_application(rt: Runtime, sent_at: date, status: str = "en_attente") -> int:
    async with rt.sessionmaker.begin() as session:
        application = Application(
            sent_at=sent_at,
            method="electronique",
            company="Acme SA",
            job_title=f"Poste du {sent_at}",
            status=status,
            orp_month=sent_at.strftime("%Y-%m"),
        )
        session.add(application)
        await session.flush()
        return application.id


async def test_reminders_once_after_ten_days(rt: Runtime, sent: list[Message]) -> None:
    today = date(2026, 10, 20)
    old = await add_application(rt, date(2026, 10, 8))
    await add_application(rt, date(2026, 10, 15))  # trop récente
    await add_application(rt, date(2026, 10, 1), status="refus")  # déjà une réponse

    # Sans ntfy : l'alerte est dans la cloche, rien ne part vers le téléphone.
    assert await notify.notify_reminders(rt, today) == 1
    assert sent == []
    async with rt.sessionmaker() as session:
        [bell] = (
            await session.scalars(select(Notification).where(Notification.kind == "follow_up"))
        ).all()
    assert bell.link == "/candidatures" and bell.read_at is None
    assert await notify.notify_reminders(rt, today) == 0  # une seule fois

    configured = Runtime.create(make_settings(ntfy_topic="sujet"))
    try:
        await add_application(configured, date(2026, 10, 9))
        assert await notify.notify_reminders(configured, today) == 1
    finally:
        await configured.dispose()
    [message] = sent
    assert message.title == "1 candidature(s) sans réponse depuis 10 jours"
    assert "Acme SA — Poste du 2026-10-09 (envoyée le 09.10)" in message.message
    async with rt.sessionmaker() as session:
        reminded = await session.scalar(
            select(Application.reminded_at).where(Application.id == old)
        )
    assert reminded is not None


@pytest.mark.parametrize(
    ("moment", "active"),
    [
        (datetime(2026, 7, 1, 7, 0, tzinfo=UTC), True),  # 9 h en été
        (datetime(2026, 7, 1, 8, 0, tzinfo=UTC), False),
        (datetime(2026, 1, 15, 8, 0, tzinfo=UTC), True),  # 9 h en hiver
    ],
)
def test_reminders_run_once_a_day_at_nine(moment: datetime, active: bool) -> None:
    assert JOBS["reminders"].is_active_at(moment) is active


async def test_offer_address_manual_and_prefill(api: AsyncClient, rt: Runtime) -> None:
    offer_id = await add_offer(rt, 1)
    saved = (
        await api.patch(
            f"/api/offers/{offer_id}/address", json={"address": " Rue du Port 2 \n\n1201 Genève "}
        )
    ).json()
    assert saved == {
        "id": offer_id,
        "company_address": "Rue du Port 2\n1201 Genève",
        "company_address_source": "manual",
    }
    offer = (await api.get(f"/api/offers/{offer_id}")).json()
    assert offer["company_address_source"] == "manual"
    prefill = (await api.get(f"/api/offers/{offer_id}/application-prefill")).json()
    assert prefill["company_address"] == "Rue du Port 2, 1201 Genève"
    cleared = (await api.patch(f"/api/offers/{offer_id}/address", json={"address": ""})).json()
    assert cleared["company_address"] is None and cleared["company_address_source"] is None
    assert (await api.patch("/api/offers/999999/address", json={})).status_code == 404


async def test_application_url_prefilled_from_offer(api: AsyncClient, rt: Runtime) -> None:
    offer_id = await add_offer(rt, 1, apply_url="https://emploi.exemple.ch/postuler/1")
    prefill = (await api.get(f"/api/offers/{offer_id}/application-prefill")).json()
    assert prefill["application_url"] == "https://emploi.exemple.ch/postuler/1"
    created = (
        await api.post("/api/applications", json={**prefill, "application_url": " rh@exemple.ch "})
    ).json()
    assert created["application_url"] == "rh@exemple.ch"
