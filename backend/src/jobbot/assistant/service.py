"""Assistant (docs/24) : discussion au fil de l'écriture, fonctions de lecture, conservation.

L'IA ne reçoit pas les données d'avance : elle appelle les fonctions de `tools` au besoin.
Seul le texte des répliques est gardé, 30 jours ; les 20 dernières répliques sont renvoyées.
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from importlib import resources
from typing import Any

import anthropic
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.assistant import tools
from jobbot.db.models import Application, ChatConversation, ChatMessage, Offer
from jobbot.llm.client import ChatTurn, chat_client_factory
from jobbot.log import get_logger
from jobbot.runtime import Runtime
from jobbot.scoring.service import account_problem, budget_state, record_call

log = get_logger(__name__)

MODEL = "claude-sonnet-5"
MAX_TOKENS = 2_000
# Une question appelle quelques fonctions : au-delà, on s'arrête (coût borné).
MAX_ROUNDS = 6
HISTORY = 20
KEEP = timedelta(days=30)
# Estimation prudente d'un tour (question + données lues), pour respecter le plafond.
ESTIMATE_USD = Decimal("0.02")
TITLE_LENGTH = 60
INSTRUCTIONS = resources.files("jobbot.llm").joinpath("prompts/assistant-v2.md").read_text("utf-8")

# Remplaçable en test par un faux client.
make_chat_client = chat_client_factory


class AssistantUnavailable(Exception):
    """IA non configurée, plafond atteint ou discussion introuvable."""


@dataclass(frozen=True)
class Event:
    """Un morceau du flux renvoyé au navigateur."""

    type: str  # conversation | text | tool | done | error
    data: dict[str, Any]


def _title(text: str) -> str:
    line = " ".join(text.split())
    return line if len(line) <= TITLE_LENGTH else line[: TITLE_LENGTH - 1].rstrip() + "…"


def _tools() -> list[dict[str, Any]]:
    return [{**tool, "eager_input_streaming": True} for tool in tools.TOOLS]


def _params(messages: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        # Le guide et les fonctions ne changent pas d'une question à l'autre : mis en cache.
        "system": [{"type": "text", "text": INSTRUCTIONS, "cache_control": {"type": "ephemeral"}}],
        "tools": _tools(),
        "messages": messages,
    }


@dataclass(frozen=True)
class Focus:
    """Élément choisi sur la page (docs/24 §2.2) : une offre, une candidature, un jour, un mois."""

    offer_id: int | None = None
    application_id: int | None = None
    day: date | None = None
    month: str | None = None


async def describe(session: AsyncSession, page: str | None, focus: Focus | None) -> str | None:
    """Ligne de contexte jointe à la question : la page et l'élément choisi, avec leur id.

    Seulement des repères (titre, entreprise) : l'IA lit le détail avec ses fonctions.
    """
    parts = [page] if page else []
    if focus:
        if focus.offer_id and (offer := await session.get(Offer, focus.offer_id)):
            parts.append(
                f"offre choisie : id {offer.id}, « {offer.title} » chez {offer.company or '?'}"
            )
        if focus.application_id and (
            application := await session.get(Application, focus.application_id)
        ):
            parts.append(
                f"candidature choisie : id {application.id}, « {application.job_title} » "
                f"chez {application.company}"
            )
        if focus.day:
            parts.append(f"jour choisi dans le calendrier : {focus.day.isoformat()}")
        if focus.month:
            parts.append(f"mois affiché : {focus.month}")
    return " ; ".join(parts)[:500] or None


def _user_text(text: str, page: str | None) -> str:
    return f"[Page ouverte : {page}]\n{text}" if page else text


async def history(session: AsyncSession, conversation_id: int) -> list[ChatMessage]:
    rows = await session.scalars(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.id.desc())
        .limit(HISTORY)
    )
    return list(reversed(list(rows)))


def _api_messages(rows: list[ChatMessage]) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    for row in rows:
        content = _user_text(row.content, row.page) if row.role == "user" else row.content
        if messages and messages[-1]["role"] == row.role:
            # Deux répliques de suite du même côté (réponse interrompue) : on les joint.
            messages[-1]["content"] += "\n\n" + content
        else:
            messages.append({"role": row.role, "content": content})
    # L'API commence par la personne.
    while messages and messages[0]["role"] != "user":
        messages.pop(0)
    return messages


async def answer(
    runtime: Runtime,
    *,
    conversation_id: int | None,
    text: str,
    page: str | None,
    profile_id: int,
    focus: Focus | None = None,
) -> AsyncIterator[Event]:
    """Enregistre la question, fait répondre l'IA au fil de l'eau, enregistre la réponse."""
    settings = runtime.settings
    if not settings.llm_configured:
        raise AssistantUnavailable("IA non configurée (réglage d'installation, voir le README)")
    now = datetime.now(UTC)
    async with runtime.sessionmaker.begin() as session:
        spend, budget, rate = await budget_state(session, now)
        if spend + ESTIMATE_USD * rate > budget:
            raise AssistantUnavailable("plafond mensuel de l'IA atteint")
        if conversation_id is None:
            conversation = ChatConversation(title=_title(text), created_at=now, updated_at=now)
            session.add(conversation)
            await session.flush()
        else:
            found = await session.get(ChatConversation, conversation_id)
            if found is None:
                raise AssistantUnavailable("discussion introuvable")
            conversation = found
            conversation.updated_at = now
        context = await describe(session, page, focus)
        session.add(
            ChatMessage(
                conversation_id=conversation.id,
                role="user",
                content=text,
                page=context,
                created_at=now,
            )
        )
        await session.flush()
        conversation_id = conversation.id
        messages = _api_messages(await history(session, conversation.id))
    yield Event("conversation", {"id": conversation_id, "title": conversation.title})

    client = make_chat_client(settings)
    written: list[str] = []
    problem: str | None = None
    for _ in range(MAX_ROUNDS):
        turn: ChatTurn | None = None
        try:
            async for item in client.stream(_params(messages)):
                if isinstance(item, ChatTurn):
                    turn = item
                else:
                    written.append(item)
                    yield Event("text", {"text": item})
        except anthropic.APIStatusError as exc:
            problem = account_problem(exc) or "l'IA ne répond pas, réessaie dans un moment"
            log.warning("assistant_api_error", status=exc.status_code)
            break
        except anthropic.APIConnectionError:
            problem = "l'IA ne répond pas, réessaie dans un moment"
            break
        if turn is None:
            problem = "réponse incomplète, réessaie"
            break
        async with runtime.sessionmaker.begin() as session:
            await record_call(session, turn.raw, offer_id=None, rate=rate, purpose="chat")
        stop = turn.raw.stop_reason
        if stop == "tool_use":
            messages.append({"role": "assistant", "content": turn.content})
            results = []
            async with runtime.sessionmaker() as session:
                for block in turn.content:
                    if block.get("type") != "tool_use":
                        continue
                    name = str(block.get("name"))
                    yield Event("tool", {"name": name, "label": tools.LABELS.get(name, name)})
                    output, error = await tools.run(session, profile_id, name, block.get("input"))
                    result = {"type": "tool_result", "tool_use_id": block["id"], "content": output}
                    results.append(result | {"is_error": True} if error else result)
            messages.append({"role": "user", "content": results})
            if written and not written[-1].endswith("\n"):
                written.append("\n\n")
                yield Event("text", {"text": "\n\n"})
            continue
        if stop == "pause_turn":
            messages.append({"role": "assistant", "content": turn.content})
            continue
        if stop == "refusal":
            problem = "l'IA a refusé de répondre à cette question"
        elif stop == "max_tokens":
            note = "\n\n(réponse coupée : trop longue)"
            written.append(note)
            yield Event("text", {"text": note})
        break
    else:
        problem = "trop de données consultées pour une seule question, précise ta demande"

    reply = "".join(written).strip()
    async with runtime.sessionmaker.begin() as session:
        if reply:
            session.add(
                ChatMessage(conversation_id=conversation_id, role="assistant", content=reply)
            )
        found = await session.get(ChatConversation, conversation_id)
        if found is not None:
            found.updated_at = datetime.now(UTC)
    if problem:
        yield Event("error", {"message": problem})
    yield Event("done", {})


async def purge(runtime: Runtime, now: datetime | None = None) -> int:
    """Discussions sans réplique depuis 30 jours (tâche quotidienne `reminders`)."""
    limit = (now or datetime.now(UTC)) - KEEP
    async with runtime.sessionmaker.begin() as session:
        result = await session.execute(
            delete(ChatConversation).where(ChatConversation.updated_at < limit)
        )
    return int(result.rowcount or 0)  # type: ignore[attr-defined]
