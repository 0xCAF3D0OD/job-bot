"""A2 du 13 novembre : toute offre jamais notée finit notée, ou « Note impossible » avec la raison.

Une offre ajoutée à la main puis passée en préparation avant sa note restait sans note (offres 638
et 841 en production) ; une note faite sans profil restait vide une fois le profil là (offre 796) ;
une offre sans texte appelait l'IA pour rien (offre 619).
"""

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text, update

from jobbot.api.app import create_app
from jobbot.core.filter import Criteria
from jobbot.db.models import Evaluation, Offer, OfferLink, OfferStatus, ProfileChunk
from jobbot.filtering.service import save_criteria
from jobbot.runtime import Runtime
from jobbot.scoring import backlog
from jobbot.scoring import service

from .conftest import admin_engine, make_settings
from .test_scoring import FakeClient, add_offer, ai, evaluation, fake, raw  # noqa: F401

FINAL_TEXT = "Électricien de montage CFC, chantiers de logements à Fribourg. " * 5


@pytest.fixture
async def api(ai: Runtime) -> AsyncIterator[AsyncClient]:  # noqa: F811
    async with admin_engine().begin() as conn:
        await conn.execute(text("DELETE FROM procrastinate_jobs"))
    app = create_app(ai.settings, ai)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    async with admin_engine().begin() as conn:
        await conn.execute(text("DELETE FROM procrastinate_jobs"))


async def no_text(rt: Runtime, offer_id: int) -> None:
    async with rt.sessionmaker.begin() as session:
        await session.execute(update(Offer).where(Offer.id == offer_id).values(snippet=None))


async def queued_tasks() -> list[str]:
    async with admin_engine().begin() as conn:
        rows = await conn.execute(text("SELECT task_name FROM procrastinate_jobs ORDER BY id"))
        return [r[0] for r in rows]


async def test_added_then_prepared_at_once_is_still_scored(
    api: AsyncClient,
    ai: Runtime,  # noqa: F811
    fake: FakeClient,  # noqa: F811
) -> None:
    body = {"title": "Électricien CFC", "location": "Fribourg", "description": FINAL_TEXT}
    added = (await api.post("/api/offers/manual", json=body)).json()
    # La note part tout de suite : la tâche de notation est en file pour ce compte.
    assert await queued_tasks() == ["score"]
    # La personne lance sa lettre avant que la note arrive.
    moved = await api.patch(f"/api/offers/{added['id']}/status", json={"status": "preparing"})
    assert moved.status_code == 200
    result = await service.run_scoring(ai)
    stored = await evaluation(ai, added["id"])
    assert result.scored == 1 and stored is not None and stored.score == 78
    assert stored.score_attempts == 0 and stored.score_final is None


async def test_manual_offer_set_aside_by_criteria_is_scored_and_kept(
    api: AsyncClient,
    ai: Runtime,  # noqa: F811
    fake: FakeClient,  # noqa: F811
) -> None:
    async with ai.sessionmaker.begin() as session:
        await save_criteria(session, Criteria(banned_words=("électricien",)))
    body = {"title": "Électricien CFC", "location": "Fribourg", "description": FINAL_TEXT}
    added = (await api.post("/api/offers/manual", json=body)).json()
    assert added["status"] == "filtered_out"
    # Une offre d'alerte écartée, elle, reste sans note (le filtre évite de payer l'IA).
    alert = await add_offer(ai, 7, status=OfferStatus.FILTERED_OUT)
    await service.run_scoring(ai)
    manual = await evaluation(ai, added["id"])
    assert manual is not None and manual.score == 78
    assert await evaluation(ai, alert) is None
    assert len(fake.calls) == 1
    offer = (await api.get(f"/api/offers/{added['id']}")).json()
    assert offer["status"] == "filtered_out" and offer["score"] == 78


async def test_offer_without_text_never_calls_the_ai(
    ai: Runtime,  # noqa: F811
    fake: FakeClient,  # noqa: F811
) -> None:
    blank = await add_offer(ai, 1, status=OfferStatus.PREPARING)
    await no_text(ai, blank)
    result = await service.run_scoring(ai)
    stored = await evaluation(ai, blank)
    assert fake.calls == [] and result.no_text == 1
    assert stored is not None and stored.score_final == "sans_texte" and stored.score is None
    await service.run_scoring(ai)
    assert fake.calls == []
    # Le texte arrive (« Coller le texte ») : la note est demandée, elle part.
    async with ai.sessionmaker.begin() as session:
        await session.execute(update(Offer).values(description=FINAL_TEXT))
    assert await service.score_offer(ai, blank) == 78


async def test_three_failures_in_a_row_end_in_note_impossible(
    ai: Runtime,  # noqa: F811
    fake: FakeClient,  # noqa: F811
) -> None:
    empty = await add_offer(ai, 1)
    broken = await add_offer(ai, 2, status=OfferStatus.LATER)
    fake.responses = {"Offre 1": raw(""), "Offre 2": raw("pas du json")}
    for expected in (1, 2):
        await service.run_scoring(ai)
        stored = await evaluation(ai, empty)
        assert stored is not None and stored.score_attempts == expected
        assert stored.score_final is None
    await service.run_scoring(ai)
    assert (await evaluation(ai, empty)).score_final == "reponse_vide"  # type: ignore[union-attr]
    assert (await evaluation(ai, broken)).score_final == "erreur"  # type: ignore[union-attr]
    assert len(fake.calls) == 6
    # État final : plus repris.
    await service.run_scoring(ai)
    assert len(fake.calls) == 6


async def test_success_after_a_failure_resets_the_count(
    ai: Runtime,  # noqa: F811
    fake: FakeClient,  # noqa: F811
) -> None:
    offer = await add_offer(ai, 1)
    fake.responses = {"Offre 1": raw("")}
    await service.run_scoring(ai)
    fake.responses = {}
    await service.run_scoring(ai)
    stored = await evaluation(ai, offer)
    assert stored is not None and stored.score == 78 and stored.score_attempts == 0


async def test_scored_offer_is_never_scored_again(
    ai: Runtime,  # noqa: F811
    fake: FakeClient,  # noqa: F811
) -> None:
    offer = await add_offer(ai, 1)
    await service.run_scoring(ai)
    for status in (OfferStatus.PREPARING, OfferStatus.LATER, OfferStatus.APPLIED):
        async with ai.sessionmaker.begin() as session:
            await session.execute(update(Offer).where(Offer.id == offer).values(status=status))
        await service.run_scoring(ai)
    assert len(fake.calls) == 1


async def test_note_made_without_profile_is_redone_once_the_profile_exists(
    ai: Runtime,  # noqa: F811
    fake: FakeClient,  # noqa: F811
) -> None:
    async with ai.sessionmaker.begin() as session:
        await session.execute(update(ProfileChunk).values(active=False))
    offer = await add_offer(ai, 1, status=OfferStatus.PREPARING)
    await service.run_scoring(ai)
    stored = await evaluation(ai, offer)
    assert stored is not None and stored.scored_at is not None and stored.score is None
    # Toujours sans profil : elle attend, sans appel ni essai compté.
    await service.run_scoring(ai)
    assert len(fake.calls) == 1
    assert (await evaluation(ai, offer)).score_attempts == 0  # type: ignore[union-attr]
    async with ai.sessionmaker.begin() as session:
        await session.execute(update(ProfileChunk).values(active=True))
    await service.run_scoring(ai)
    await service.run_scoring(ai)
    assert len(fake.calls) == 2
    assert (await evaluation(ai, offer)).score == 78  # type: ignore[union-attr]


async def test_backlog_waits_for_the_command(
    ai: Runtime,  # noqa: F811
    fake: FakeClient,  # noqa: F811
) -> None:
    """Les offres jamais notées d'avant A2 : la tâche ne les prend pas ; la commande les compte,
    chiffre le coût, puis les rend sur `--lancer`."""
    waiting = await add_offer(ai, 1, status=OfferStatus.PREPARING)
    blank = await add_offer(ai, 2, status=OfferStatus.APPLIED)
    await no_text(ai, blank)
    alert = await add_offer(ai, 3, status=OfferStatus.FILTERED_OUT)
    async with ai.sessionmaker.begin() as session:
        for offer_id in (waiting, blank, alert):
            session.add(
                Evaluation(
                    offer_id=offer_id,
                    filter_passed=offer_id != alert,
                    filter_reasons=[],
                    criteria_hash="",
                    score_final=service.FINAL_BACKLOG,
                )
            )
    await service.run_scoring(ai)
    assert fake.calls == []

    admin = Runtime.create(make_settings(anthropic_api_key="sk-test"), "admin")
    try:
        found = await backlog.count(admin)
        assert [(b.offers, b.without_text) for b in found] == [(2, 1)]
        assert str(found[0].cost_chf) == "0.02"
        assert await backlog.release(admin) == 2
    finally:
        await admin.dispose()
    await service.run_scoring(ai)
    assert len(fake.calls) == 1
    assert (await evaluation(ai, waiting)).score == 78  # type: ignore[union-attr]
    assert (await evaluation(ai, blank)).score_final == "sans_texte"  # type: ignore[union-attr]
    assert (await evaluation(ai, alert)).score_final == "a_rattraper"  # type: ignore[union-attr]
    async with ai.sessionmaker() as session:
        links = await session.scalars(select(OfferLink))
        assert list(links) == []


async def alert_set_aside(rt: Runtime, n: int) -> int:
    """Une offre d'alerte écartée par les critères : passée par le filtre, jamais notée."""
    offer_id = await add_offer(rt, n, status=OfferStatus.FILTERED_OUT, location="Zurich")
    async with rt.sessionmaker.begin() as session:
        session.add(
            Evaluation(offer_id=offer_id, filter_passed=False, filter_reasons=[], criteria_hash="")
        )
    return offer_id


@pytest.mark.parametrize("status", ["later", "preparing"])
async def test_set_aside_offer_kept_or_prepared_is_scored_then(
    api: AsyncClient,
    ai: Runtime,  # noqa: F811
    fake: FakeClient,  # noqa: F811
    status: str,
) -> None:
    offer = await alert_set_aside(ai, 1)
    await service.run_scoring(ai)
    assert fake.calls == []
    moved = await api.patch(f"/api/offers/{offer}/status", json={"status": status})
    assert moved.status_code == 200
    assert await queued_tasks() == ["score"]
    await service.run_scoring(ai)
    assert (await evaluation(ai, offer)).score == 78  # type: ignore[union-attr]


async def test_set_aside_offer_back_after_criteria_change_is_scored_then(
    api: AsyncClient,
    ai: Runtime,  # noqa: F811
    fake: FakeClient,  # noqa: F811
) -> None:
    async with ai.sessionmaker.begin() as session:
        await save_criteria(session, Criteria(banned_words=("offre",)))
    offer = await alert_set_aside(ai, 1)
    await service.run_scoring(ai)
    assert fake.calls == []
    criteria = (await api.get("/api/criteria")).json()
    saved = await api.put("/api/criteria", json={**criteria, "banned_words": []})
    assert saved.status_code == 200 and saved.json()["returned"] == 1
    assert await queued_tasks() == ["score"]
    await service.run_scoring(ai)
    stored = await evaluation(ai, offer)
    assert stored is not None and stored.score == 78
