"""Assistant (docs/24) : flux SSE, fonctions de lecture, conservation, jamais de coordonnées."""

import json
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select, text

from jobbot.assistant import service, tools
from jobbot.db.models import (
    Application,
    ChatConversation,
    ChatMessage,
    Evaluation,
    LlmCall,
    Offer,
)
from jobbot.llm.client import ChatTurn, RawResult
from jobbot.llm.pricing import Usage
from jobbot.runtime import Runtime


async def reset(runtime: Runtime) -> None:
    async with runtime.engine.begin() as conn:
        await conn.execute(
            text("TRUNCATE chat_conversations, applications, offers, llm_calls CASCADE")
        )


def events(body: str) -> list[tuple[str, dict[str, Any]]]:
    found = []
    for block in body.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        found.append((lines["event"], json.loads(lines["data"])))
    return found


def turn(content: list[dict[str, Any]], stop: str) -> ChatTurn:
    text_ = "".join(b["text"] for b in content if b["type"] == "text")
    return ChatTurn(content, RawResult(text_, service.MODEL, Usage(3000, 0, 0, 200), stop))


class FakeChat:
    """Rejoue des tours préparés ; garde les paramètres de chaque appel."""

    def __init__(self, turns: list[ChatTurn]) -> None:
        self.turns = turns
        self.calls: list[dict[str, Any]] = []

    async def stream(self, params: dict[str, Any]) -> AsyncIterator[str | ChatTurn]:
        self.calls.append(json.loads(json.dumps(params)))
        current = self.turns.pop(0)
        for block in current.content:
            if block["type"] == "text":
                words = block["text"].split(" ")
                for index, word in enumerate(words):
                    yield word if index == len(words) - 1 else word + " "
        yield current


@pytest.fixture
def llm(monkeypatch: pytest.MonkeyPatch, runtime: Runtime) -> None:
    monkeypatch.setattr(type(runtime.settings), "llm_configured", property(lambda _self: True))


async def test_unavailable_without_key(client: AsyncClient, runtime: Runtime) -> None:
    assert (await client.get("/api/assistant/status")).json()["available"] is False
    response = await client.post("/api/assistant/messages", json={"text": "Bonjour"})
    assert response.status_code == 409
    async with runtime.sessionmaker() as session:
        assert await session.scalar(select(func.count()).select_from(ChatMessage)) == 0


async def test_answer_with_tool_and_history(
    client: AsyncClient, runtime: Runtime, monkeypatch: pytest.MonkeyPatch, llm: None
) -> None:
    await reset(runtime)
    today = datetime.now(UTC).date()
    async with runtime.sessionmaker.begin() as session:
        session.add(
            Application(
                sent_at=today - timedelta(days=12),
                method="electronique",
                company="Exemple SA",
                company_address=None,
                contact_name="Marie Secret",
                contact_phone="+41 79 000 00 00",
                contact_email="marie@example.ch",
                job_title="Ingénieur DevOps",
                orp_month=f"{today:%Y-%m}",
                status="en_attente",
            )
        )
    fake = FakeChat(
        [
            turn(
                [
                    {"type": "text", "text": "Je regarde."},
                    {
                        "type": "tool_use",
                        "id": "t1",
                        "name": "candidatures",
                        "input": {},
                    },
                ],
                "tool_use",
            ),
            turn([{"type": "text", "text": "Relance Exemple SA."}], "end_turn"),
        ]
    )
    monkeypatch.setattr(service, "make_chat_client", lambda _settings: fake)

    response = await client.post(
        "/api/assistant/messages",
        json={"text": "  Qui relancer ?  ", "page": "/candidatures/suivi"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    found = events(response.text)
    kinds = [kind for kind, _ in found]
    assert kinds[0] == "conversation" and kinds[-1] == "done" and "error" not in kinds
    assert ("tool", {"name": "candidatures", "label": "tes candidatures"}) in found
    conversation_id = found[0][1]["id"]
    assert found[0][1]["title"] == "Qui relancer ?"

    first, second = fake.calls
    assert first["model"] == "claude-sonnet-5" and first["system"][0]["cache_control"]
    assert all(t["eager_input_streaming"] for t in first["tools"])
    assert first["messages"] == [
        {"role": "user", "content": "[Page ouverte : /candidatures/suivi]\nQui relancer ?"}
    ]
    result = second["messages"][-1]["content"][0]
    assert result["type"] == "tool_result" and result["tool_use_id"] == "t1"
    data = json.loads(result["content"])["candidatures"][0]
    assert data["a_relancer"] is True and data["ligne_orp_incomplete"] is True
    # Jamais les coordonnées d'un contact.
    assert "Marie" not in result["content"] and "+41" not in result["content"]

    detail = (await client.get(f"/api/assistant/conversations/{conversation_id}")).json()
    assert [m["role"] for m in detail["messages"]] == ["user", "assistant"]
    assert detail["messages"][1]["content"] == "Je regarde.\n\nRelance Exemple SA."
    async with runtime.sessionmaker() as session:
        purposes = list(await session.scalars(select(LlmCall.purpose)))
    assert purposes == ["chat", "chat"]

    # Suite de la discussion : l'historique est renvoyé, sans les lectures de données.
    fake.turns = [turn([{"type": "text", "text": "Avec plaisir."}], "end_turn")]
    again = await client.post(
        "/api/assistant/messages",
        json={"conversation_id": conversation_id, "text": "Merci"},
    )
    assert again.status_code == 200
    roles = [m["role"] for m in fake.calls[-1]["messages"]]
    assert roles == ["user", "assistant", "user"]
    listed = (await client.get("/api/assistant/conversations")).json()
    assert [c["id"] for c in listed] == [conversation_id]

    assert (
        await client.delete(f"/api/assistant/conversations/{conversation_id}")
    ).status_code == 204
    assert (await client.get(f"/api/assistant/conversations/{conversation_id}")).status_code == 404
    missing = await client.post(
        "/api/assistant/messages", json={"conversation_id": conversation_id, "text": "Encore"}
    )
    assert missing.status_code == 409
    await reset(runtime)


async def test_refusal_and_round_limit(
    client: AsyncClient, runtime: Runtime, monkeypatch: pytest.MonkeyPatch, llm: None
) -> None:
    await reset(runtime)
    fake = FakeChat([turn([], "refusal")])
    monkeypatch.setattr(service, "make_chat_client", lambda _settings: fake)
    found = events((await client.post("/api/assistant/messages", json={"text": "?"})).text)
    assert ("error", {"message": "l'IA a refusé de répondre à cette question"}) in found

    loop = {"type": "tool_use", "id": "t", "name": "situation", "input": {}}
    fake.turns = [turn([loop], "tool_use") for _ in range(service.MAX_ROUNDS)]
    found = events((await client.post("/api/assistant/messages", json={"text": "?"})).text)
    assert found[-2][0] == "error" and "précise ta demande" in found[-2][1]["message"]
    await reset(runtime)


async def test_tools_read_data(runtime: Runtime) -> None:
    await reset(runtime)
    now = datetime.now(UTC)
    async with runtime.sessionmaker.begin() as session:
        offer = Offer(
            fingerprint="assistant-1",
            title="SRE",
            company="Exemple SA",
            location="Lausanne",
            status="to_review",
            first_seen_at=now,
            last_seen_at=now,
            description="Exploiter Kubernetes.",
        )
        session.add(offer)
        await session.flush()
        session.add(
            Evaluation(
                offer_id=offer.id,
                filter_passed=True,
                criteria_hash="x",
                score=82,
                summary_role="SRE cloud",
                strengths=["Kubernetes"],
                gaps=["Go"],
            )
        )
        offer_id = offer.id
    async with runtime.sessionmaker() as session:
        listed, error = await tools.run(session, 1, "offres_a_examiner", {"limite": 5})
        assert not error and json.loads(listed)[0] == {
            "id": offer_id,
            "titre": "SRE",
            "entreprise": "Exemple SA",
            "lieu": "Lausanne",
            "note": 82,
            "poste": "SRE cloud",
            "recue_le": json.loads(listed)[0]["recue_le"],
        }
        detail, _ = await tools.run(session, 1, "offre", {"id": offer_id})
        assert json.loads(detail)["manques"] == ["Go"]
        assert (await tools.run(session, 1, "offre", {"id": "x"}))[1] is True
        assert (await tools.run(session, 1, "offres_a_examiner", {"limite": 99}))[1] is True
        assert (await tools.run(session, 1, "preuves_orp", {"mois": "2026-13"}))[1] is True
        assert (await tools.run(session, 1, "inconnue", {}))[1] is True
        orp, _ = await tools.run(session, 1, "preuves_orp", {"mois": "2026-10"})
        assert json.loads(orp)["a_remettre_avant"] == date(2026, 11, 5).isoformat()
        for name in ("situation", "alertes", "retours_entretien", "profil", "formations"):
            assert (await tools.run(session, 1, name, {}))[1] is False
        assert (await tools.run(session, 1, "actualites", {}))[1] is False
    assert set(tools.LABELS) == {t["name"] for t in tools.TOOLS}
    await reset(runtime)


async def test_purge_after_30_days(runtime: Runtime) -> None:
    await reset(runtime)
    now = datetime.now(UTC)
    async with runtime.sessionmaker.begin() as session:
        session.add(ChatConversation(title="ancienne", updated_at=now - timedelta(days=31)))
        session.add(ChatConversation(title="récente", updated_at=now - timedelta(days=2)))
    assert await service.purge(runtime) == 1
    async with runtime.sessionmaker() as session:
        assert list(await session.scalars(select(ChatConversation.title))) == ["récente"]
    await reset(runtime)
