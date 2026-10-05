"""Preuves ORP : format, tableau du mois, CSV, remise (docs/09, 0.6.0-a)."""

from collections.abc import AsyncIterator
from datetime import UTC, date, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from jobbot.api.app import create_app
from jobbot.api.routes import orp as orp_route
from jobbot.core.orp import ApplicationData, due_date, result_text, shift_month, to_csv, to_row
from jobbot.db.models import Search, Setting
from jobbot.runtime import Runtime
from jobbot.settings import Settings

TODAY = date(2026, 11, 3)


def app_data(**extra: object) -> ApplicationData:
    values: dict[str, object] = {
        "id": 1,
        "sent_at": date(2026, 10, 2),
        "company": "Acme SA",
        "company_address": "Avenue de l'Exemple 5\n1003 Lausanne",
        "contact_name": None,
        "contact_phone": None,
        "job_title": "Ingénieur DevOps junior",
        "rate_text": "plein temps",
        "method": "electronique",
        "assigned_by_orp": False,
        "status": "en_attente",
        "status_reason": None,
        "interview_at": None,
    }
    values.update(extra)
    return ApplicationData(**values)  # type: ignore[arg-type]


def test_result_text() -> None:
    assert result_text("en_attente", None, None) == "en suspens"
    assert result_text("relancee", None, None) == "en suspens"
    assert result_text("sans_reponse", None, None) == "en suspens (sans réponse)"
    interview = datetime(2026, 11, 12, 8, 0, tzinfo=UTC)
    assert result_text("entretien", None, interview) == "en suspens (entretien le 12.11)"
    assert result_text("refus", "profil senior", None) == "refus : profil senior"
    assert result_text("refus", None, None) == "refus"
    assert result_text("engagement", None, None) == "engagement"


def test_row_and_csv() -> None:
    row = to_row(app_data())
    assert (row.date, row.address, row.method, row.assigned) == (
        "02.10.2026",
        "Avenue de l'Exemple 5, 1003 Lausanne",
        "électronique",
        "non",
    )
    assert row.missing == []
    incomplete = to_row(app_data(company_address="  ", assigned_by_orp=True, method="personnel"))
    assert incomplete.missing == ["adresse de l'entreprise"]
    assert (incomplete.method, incomplete.assigned) == ("en personne", "oui")

    with_url = to_row(app_data(application_url="https://emploi.exemple.ch/1"))
    assert with_url.url == "https://emploi.exemple.ch/1"
    assert to_csv([with_url]).decode("utf-8").rstrip().endswith(";https://emploi.exemple.ch/1")
    content = to_csv([row]).decode("utf-8")
    assert content.startswith("﻿Date;Entreprise;Adresse;")
    assert "02.10.2026;Acme SA;Avenue de l'Exemple 5, 1003 Lausanne;;;" in content


def test_months() -> None:
    assert shift_month("2026-12", 1) == "2027-01"
    assert shift_month("2026-01", -1) == "2025-12"
    assert due_date("2026-12") == date(2027, 1, 5)


@pytest.fixture
async def api(
    runtime: Runtime, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[AsyncClient]:
    monkeypatch.setattr(orp_route, "_today", lambda: TODAY)
    async with runtime.engine.begin() as conn:
        await conn.execute(text("TRUNCATE offers, applications, orp_months, searches CASCADE"))
        await conn.execute(text("DELETE FROM settings WHERE key LIKE 'identity_%'"))
    async with runtime.sessionmaker.begin() as session:
        await session.merge(Setting(key="orp_monthly_target", value=20))
    app = create_app(settings, runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    async with runtime.engine.begin() as conn:
        await conn.execute(text("DELETE FROM settings WHERE key = 'orp_monthly_target'"))


async def add(api: AsyncClient, sent_at: str, **extra: object) -> int:
    body = {"sent_at": sent_at, "company": "Acme SA", "job_title": "DevOps", **extra}
    response = await api.post("/api/applications", json=body)
    assert response.status_code == 201
    application_id: int = response.json()["id"]
    return application_id


async def test_month_table(api: AsyncClient, runtime: Runtime) -> None:
    await add(api, "2026-10-20", company_address="Rue 1\n1000 Lausanne")
    await add(api, "2026-10-02")
    await add(api, "2026-11-01")
    await api.put(
        "/api/identity",
        json={
            "name": "Jean Exemple",
            "street": "Rue du Test 1",
            "postcode": "1020",
            "city": "Renens",
        },
    )
    async with runtime.sessionmaker.begin() as session:
        session.add_all(
            [
                Search(
                    source="jobup",
                    message_id=f"m{n}",
                    received_at=at,
                    alert_label="DevOps Lausanne",
                    raw_key="k",
                    parse_status="parsed",
                    results_count=4,
                )
                for n, at in enumerate(
                    [datetime(2026, 10, 5, 7, tzinfo=UTC), datetime(2026, 11, 2, 7, tzinfo=UTC)]
                )
            ]
        )

    # Par défaut : octobre, pas encore remis.
    month = (await api.get("/api/orp")).json()
    assert month["month"] == "2026-10" and month["state"] == "a_remettre"
    assert month["due_date"] == "2026-11-05"
    assert (month["count"], month["target"], month["incomplete"]) == (2, 20, 1)
    assert [r["date"] for r in month["rows"]] == ["02.10.2026", "20.10.2026"]
    assert month["rows"][0]["missing"] == ["adresse de l'entreprise"]
    assert month["holder"] == {"name": "Jean Exemple", "address": "Rue du Test 1, 1020 Renens"}
    assert [s["label"] for s in month["searches"]] == ["DevOps Lausanne"]

    current = (await api.get("/api/orp", params={"month": "2026-11"})).json()
    assert current["state"] == "en_cours" and current["count"] == 1


async def test_csv_submission_and_changes(api: AsyncClient) -> None:
    first = await add(api, "2026-10-02")
    response = await api.get("/api/orp/2026-10/csv")
    assert response.status_code == 200
    assert (
        response.headers["content-disposition"] == 'attachment; filename="preuves-orp-2026-10.csv"'
    )
    assert response.content.startswith(b"\xef\xbb\xbfDate;")
    assert (await api.get("/api/orp", params={"month": "2026-10"})).json()["exported_at"]

    assert (await api.put("/api/orp/2026-10/submission")).status_code == 204
    month = (await api.get("/api/orp", params={"month": "2026-10"})).json()
    assert month["state"] == "remis" and not month["changed_after_submit"]
    # Une fois octobre remis, la page s'ouvre sur novembre.
    assert (await api.get("/api/orp")).json()["month"] == "2026-11"

    # Modifier une candidature d'octobre : signalé.
    await api.put(
        f"/api/applications/{first}",
        json={
            "sent_at": "2026-10-02",
            "company": "Acme SA",
            "job_title": "DevOps",
            "status": "refus",
        },
    )
    month = (await api.get("/api/orp", params={"month": "2026-10"})).json()
    assert month["changed_after_submit"] and month["rows"][0]["result"] == "refus"

    assert (await api.delete("/api/orp/2026-10/submission")).status_code == 204
    month = (await api.get("/api/orp", params={"month": "2026-10"})).json()
    assert month["state"] == "a_remettre" and not month["changed_after_submit"]
    assert (await api.get("/api/orp/2026-13/csv")).status_code == 422


async def test_default_month_without_previous(api: AsyncClient) -> None:
    # Rien en octobre : la page s'ouvre sur le mois en cours.
    assert (await api.get("/api/orp")).json()["month"] == "2026-11"
