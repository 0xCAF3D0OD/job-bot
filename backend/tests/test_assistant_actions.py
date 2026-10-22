"""Actions proposées par l'assistant (docs/52) : l'IA propose, seul un clic les fait."""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.assistant import actions, service
from jobbot.db.models import Application, ChatAction, ChatConversation, Offer
from jobbot.runtime import Runtime
from tests.test_assistant import FakeChat, events, reset, turn


@pytest.fixture
def llm(monkeypatch: pytest.MonkeyPatch, runtime: Runtime) -> None:
    monkeypatch.setattr(type(runtime.settings), "llm_configured", property(lambda _self: True))


async def _offer(runtime: Runtime, status: str = "to_review") -> int:
    now = datetime.now(UTC)
    async with runtime.sessionmaker.begin() as session:
        offer = Offer(
            fingerprint=f"actions-{now.timestamp()}",
            title="Cloud Architect",
            company="Jura Data SA",
            status=status,
            first_seen_at=now,
            last_seen_at=now,
        )
        session.add(offer)
        await session.flush()
        return offer.id


def _propose(name_id: str, kind: str, target: int, value: str) -> dict[str, object]:
    return {
        "type": "tool_use",
        "id": name_id,
        "name": "proposer_action",
        "input": {"type": kind, "id": target, "valeur": value},
    }


async def test_propose_then_confirm_then_undo(
    client: AsyncClient, runtime: Runtime, monkeypatch: pytest.MonkeyPatch, llm: None
) -> None:
    await reset(runtime)
    offer_id = await _offer(runtime)
    fake = FakeChat(
        [
            turn(
                [
                    {"type": "text", "text": "Je te propose de la mettre de côté."},
                    _propose("t1", "offre_statut", offer_id, "later"),
                ],
                "tool_use",
            ),
            turn([{"type": "text", "text": "À confirmer ci-dessous."}], "end_turn"),
        ]
    )
    monkeypatch.setattr(service, "make_chat_client", lambda _settings: fake)

    response = await client.post("/api/assistant/messages", json={"text": "Trie mes offres"})
    found = events(response.text)
    proposals = [data for kind, data in found if kind == "action"]
    assert len(proposals) == 1
    proposal = proposals[0]
    assert proposal["label"] == "Passer « Cloud Architect » (Jura Data SA) en Plus tard"
    assert proposal["state"] == "proposed"
    # L'outil n'a rien changé : l'IA apprend seulement que c'est en attente.
    result = fake.calls[1]["messages"][-1]["content"][0]
    assert "en attente de la confirmation" in result["content"]
    async with runtime.sessionmaker() as session:
        offer = await session.get(Offer, offer_id)
        assert offer is not None and offer.status == "to_review"

    # La discussion rouverte garde la proposition.
    conversation_id = found[0][1]["id"]
    detail = (await client.get(f"/api/assistant/conversations/{conversation_id}")).json()
    assert [a["state"] for a in detail["actions"]] == ["proposed"]

    done = (await client.post(f"/api/assistant/actions/{proposal['id']}/confirm")).json()
    assert done["state"] == "done" and done["note"] is None
    async with runtime.sessionmaker() as session:
        offer = await session.get(Offer, offer_id)
        assert offer is not None and offer.status == "later"
    # Confirmer deux fois ne refait rien.
    again = (await client.post(f"/api/assistant/actions/{proposal['id']}/confirm")).json()
    assert again["state"] == "done" and again["note"] == "déjà décidée"

    undone = (await client.post(f"/api/assistant/actions/{proposal['id']}/undo")).json()
    assert undone["state"] == "undone"
    async with runtime.sessionmaker() as session:
        offer = await session.get(Offer, offer_id)
        assert offer is not None and offer.status == "to_review"


async def test_refused_proposals_and_limit(
    client: AsyncClient, runtime: Runtime, monkeypatch: pytest.MonkeyPatch, llm: None
) -> None:
    await reset(runtime)
    offer_id = await _offer(runtime)
    fake = FakeChat(
        [
            turn(
                [
                    # Déjà dans cet état, statut interdit, puis quatre de suite : trois au plus.
                    _propose("t1", "offre_statut", offer_id, "to_review"),
                    _propose("t2", "offre_statut", offer_id, "applied"),
                    _propose("t3", "offre_statut", offer_id, "later"),
                    _propose("t4", "offre_statut", offer_id, "ignored"),
                    _propose("t5", "offre_expiree", offer_id, "expired"),
                    _propose("t6", "offre_statut", offer_id, "later"),
                ],
                "tool_use",
            ),
            turn([{"type": "text", "text": "Voilà."}], "end_turn"),
        ]
    )
    monkeypatch.setattr(service, "make_chat_client", lambda _settings: fake)
    response = await client.post("/api/assistant/messages", json={"text": "Trie"})
    shown = [data for kind, data in events(response.text) if kind == "action"]
    assert len(shown) == 3
    results = fake.calls[1]["messages"][-1]["content"]
    assert results[0]["is_error"] and "déjà dans cet état" in results[0]["content"]
    assert results[1]["is_error"] and "non proposable" in results[1]["content"]
    assert results[5]["is_error"] and "3 propositions au plus" in results[5]["content"]


async def test_stale_proposal_changes_nothing(runtime: Runtime) -> None:
    await reset(runtime)
    offer_id = await _offer(runtime)
    async with runtime.sessionmaker.begin() as session:
        conversation = ChatConversation(title="t")
        session.add(conversation)
        await session.flush()
        action = await actions.propose(
            session, conversation.id, {"type": "offre_statut", "id": offer_id, "valeur": "later"}, 0
        )
        action_id = action.id
    # Entre-temps, l'offre a été triée à la main.
    async with runtime.sessionmaker.begin() as session:
        offer = await session.get(Offer, offer_id)
        assert offer is not None
        offer.status = "later"
    async with runtime.sessionmaker.begin() as session:
        stored = await session.get(ChatAction, action_id)
        assert stored is not None
        with pytest.raises(actions.ActionRefused):
            await actions.confirm(session, stored)
    async with runtime.sessionmaker() as session:
        stored = await session.get(ChatAction, action_id)
        assert stored is not None and stored.state == "stale"


async def test_application_status_and_expiry(client: AsyncClient, runtime: Runtime) -> None:
    await reset(runtime)
    today = datetime.now(UTC).date()
    offer_id = await _offer(runtime)
    async with runtime.sessionmaker.begin() as session:
        application = Application(
            sent_at=today - timedelta(days=30),
            method="electronique",
            company="Exemple SA",
            job_title="Ingénieur DevOps",
            orp_month=f"{today:%Y-%m}",
            status="relancee",
            followed_up_at=today - timedelta(days=15),
        )
        conversation = ChatConversation(title="t")
        session.add_all([application, conversation])
        await session.flush()
        no_answer = await actions.propose(
            session,
            conversation.id,
            {"type": "candidature_statut", "id": application.id, "valeur": "sans_reponse"},
            0,
        )
        expiry = await actions.propose(
            session,
            conversation.id,
            {"type": "offre_expiree", "id": offer_id, "valeur": "expired"},
            1,
        )
        ids = (no_answer.id, expiry.id, application.id)
    assert (
        no_answer.label
        == "Passer la candidature « Ingénieur DevOps » chez Exemple SA en « Sans réponse »"
    )

    for action_id in ids[:2]:
        assert (await client.post(f"/api/assistant/actions/{action_id}/confirm")).json()[
            "state"
        ] == "done"
    async with runtime.sessionmaker() as session:
        saved = await session.get(Application, ids[2])
        assert saved is not None and saved.status == "sans_reponse"
        # Relancée puis sans réponse : la date de relance est gardée (docs/38).
        assert saved.followed_up_at == today - timedelta(days=15)
        offer = await session.get(Offer, offer_id)
        assert (
            offer is not None and offer.expired_at is not None and offer.expiry_source == "manual"
        )

    for action_id in ids[:2]:
        assert (await client.post(f"/api/assistant/actions/{action_id}/undo")).json()[
            "state"
        ] == "undone"
    async with runtime.sessionmaker() as session:
        saved = await session.get(Application, ids[2])
        assert saved is not None and saved.status == "relancee"
        offer = await session.get(Offer, offer_id)
        assert offer is not None and offer.expired_at is None and offer.expiry_override is None


async def test_no_action_on_an_applied_offer_and_deleted_with_conversation(
    client: AsyncClient, runtime: Runtime
) -> None:
    await reset(runtime)
    offer_id = await _offer(runtime, status="applied")
    async with runtime.sessionmaker.begin() as session:
        conversation = ChatConversation(title="t")
        session.add(conversation)
        await session.flush()
        with pytest.raises(actions.ActionRefused, match="candidature"):
            await actions.propose(
                session,
                conversation.id,
                {"type": "offre_statut", "id": offer_id, "valeur": "later"},
                0,
            )
        other = await _offer_in(session)
        await actions.propose(
            session, conversation.id, {"type": "offre_statut", "id": other, "valeur": "ignored"}, 0
        )
        conversation_id = conversation.id
    await client.delete(f"/api/assistant/conversations/{conversation_id}")
    async with runtime.sessionmaker() as session:
        assert (await session.scalars(select(ChatAction))).all() == []


async def _offer_in(session: AsyncSession) -> int:
    now = datetime.now(UTC)
    offer = Offer(
        fingerprint="actions-other",
        title="SRE",
        company="Exemple SA",
        status="to_review",
        first_seen_at=now,
        last_seen_at=now,
    )
    session.add(offer)
    await session.flush()
    return offer.id


async def test_the_rhythm_through_the_assistant(runtime: Runtime) -> None:
    """Le bon rythme (docs/86, 0.68.1) : jours de recherche et pause, confirmés puis annulés."""
    from sqlalchemy import text

    from jobbot.followups.service import local_today
    from jobbot.rhythm import service as rhythm

    await reset(runtime)
    keys = "('rhythm_days', 'rhythm_pause_from', 'rhythm_pause_until')"
    async with runtime.engine.begin() as conn:
        await conn.execute(text(f"DELETE FROM settings WHERE key IN {keys}"))
    start = local_today() + timedelta(days=7)
    end = start + timedelta(days=6)
    async with runtime.sessionmaker.begin() as session:
        conversation = ChatConversation(title="t")
        session.add(conversation)
        await session.flush()
        days = await actions.propose(
            session, conversation.id, {"type": "rythme_jours", "id": 0, "valeur": "4,0,2"}, 0
        )
        pause = await actions.propose(
            session,
            conversation.id,
            {"type": "pause", "id": 0, "valeur": f"{start}/{end}"},
            1,
        )
        assert days.label == "Garder comme jours de recherche : lundi, mercredi, vendredi"
        assert pause.label.startswith("Faire une pause du ")
        for wrong in ("0,1,2,3,4", "8", ""):
            with pytest.raises(actions.ActionRefused):
                await actions.propose(
                    session, conversation.id, {"type": "rythme_jours", "id": 0, "valeur": wrong}, 2
                )
        with pytest.raises(actions.ActionRefused):
            await actions.propose(
                session, conversation.id, {"type": "pause", "id": 0, "valeur": "fin"}, 2
            )
        await actions.confirm(session, days)
        await actions.confirm(session, pause)
    async with runtime.sessionmaker() as session:
        loaded = await rhythm.load(session)
    assert loaded.days == (0, 2, 4) and loaded.paused(start + timedelta(days=1))
    async with runtime.sessionmaker.begin() as session:
        stored = await session.get(ChatAction, days.id)
        assert stored is not None
        await actions.undo(session, stored)
        stored_pause = await session.get(ChatAction, pause.id)
        assert stored_pause is not None
        await actions.undo(session, stored_pause)
    async with runtime.sessionmaker() as session:
        loaded = await rhythm.load(session)
    assert loaded.days == rhythm.DEFAULT_DAYS and loaded.pause_from is None
    async with runtime.engine.begin() as conn:
        await conn.execute(text(f"DELETE FROM settings WHERE key IN {keys}"))
