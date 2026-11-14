"""« Ce que jobA1 conseille » (Kevin, 2026-11-14) : sans IA, au moins 5 candidatures ou 5 offres."""

from datetime import UTC, date, datetime, timedelta
from typing import Any

from httpx import AsyncClient
from sqlalchemy import delete

from jobbot.db.models import Application, Evaluation, Offer
from jobbot.insights.advice import channel_advice
from jobbot.insights.service import Facts
from jobbot.runtime import Runtime

from .test_insights import api  # noqa: F401  (la fixture qui vide les tables)

TODAY = date(2026, 11, 14)
OLD = TODAY - timedelta(days=20)
NAMES = {"indeed": "Indeed", "jobup": "jobup"}


def fact(
    source: str = "jobup", *, answered: bool = False, sent: date = OLD, **values: Any
) -> Facts:
    application = Application(
        sent_at=sent,
        method=values.pop("method", "electronique"),
        company="SA",
        job_title="DevOps",
        status="refus" if answered else "sans_reponse",
        **values,
    )
    return Facts(application, source, None, False)


FORM = {"application_url": "https://form.example"}
MAIL = {"contact_email": "rh@example.ch"}


def test_channel_advice_needs_five_settled_applications_and_an_answer_elsewhere() -> None:
    forms = [fact(**FORM) for _ in range(5)]
    mails = [fact(answered=True, **MAIL)]
    found = channel_advice(forms + mails, NAMES, TODAY)
    assert found is not None
    assert (found.kind, found.title, found.base, found.base_unit) == (
        "channel",
        "Les formulaires en ligne ne répondent pas",
        5,
        "applications",
    )
    assert found.text == "Essaie l'e-mail direct au service RH quand l'annonce en donne un."
    # Quatre seulement : pas de conseil.
    assert channel_advice(forms[:4] + mails, NAMES, TODAY) is None
    # Aucune réponse nulle part : « Ce qui bloque » le dit déjà.
    assert channel_advice(forms, NAMES, TODAY) is None
    # Une candidature de moins de 14 jours ne compte pas encore.
    recent = [*forms[:4], fact(sent=TODAY - timedelta(days=3), **FORM)]
    assert channel_advice(recent + mails, NAMES, TODAY) is None


def test_channel_advice_falls_back_on_a_silent_site() -> None:
    indeed = [fact("indeed") for _ in range(6)]
    jobup = [fact("jobup", answered=True)]
    found = channel_advice(indeed + jobup, NAMES, TODAY)
    assert found is not None
    assert (found.kind, found.title, found.base) == (
        "site",
        "Les offres de Indeed ne répondent pas",
        6,
    )


async def test_skill_advice_in_the_bilan(api: AsyncClient, runtime: Runtime) -> None:  # noqa: F811
    now = datetime.now(UTC)
    async with runtime.sessionmaker.begin() as session:
        for n in range(8):
            offer = Offer(
                fingerprint=f"conseil-{n}",
                title="DevOps",
                company=f"Conseil {n} SA",
                status="to_review",
                first_seen_at=now - timedelta(days=3),
                last_seen_at=now,
            )
            session.add(offer)
            await session.flush()
            asks = [{"text": "Kubernetes", "covered": True}]
            if n < 5:
                asks.append({"text": "Terraform" if n else "terraform", "covered": False})
            session.add(
                Evaluation(
                    offer_id=offer.id, filter_passed=True, criteria_hash="h", keywords_asks=asks
                )
            )
    found = (await api.get("/api/insights")).json()
    assert found["advice"] == [
        {
            "kind": "skill",
            "title": "Terraform revient dans 5 offres sur 8",
            "text": "La formation peut être financée par l'ORP.",
            "base": 8,
            "base_unit": "offers",
            "link": "/bilan/formations?onglet=catalogue",
        }
    ]
    # Quatre offres seulement : pas de conseil, le bloc est caché.
    async with runtime.sessionmaker.begin() as session:
        await session.execute(delete(Offer).where(Offer.fingerprint == "conseil-1"))
    assert (await api.get("/api/insights")).json()["advice"] == []
