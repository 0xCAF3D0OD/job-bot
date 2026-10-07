"""Assistant (docs/24) : discussions, réponse au fil de l'écriture (flux SSE)."""

import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import delete, select

from jobbot.assistant import service
from jobbot.db.models import ChatConversation, ChatMessage
from jobbot.profiles import service as profiles
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


class AssistantStatus(BaseModel):
    available: bool
    model: str


class ConversationOut(BaseModel):
    id: int
    title: str
    updated_at: datetime


class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime


class ConversationDetail(ConversationOut):
    messages: list[ChatMessageOut]


class QuestionIn(BaseModel):
    conversation_id: int | None = None
    text: Annotated[str, Field(min_length=1, max_length=4000)]
    # Chemin de la page ouverte (/candidatures/suivi?jour=…), sans domaine.
    page: Annotated[str, Field(max_length=300)] | None = None

    @field_validator("text")
    @classmethod
    def _strip(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("question vide")
        return value

    @field_validator("page")
    @classmethod
    def _path(cls, value: str | None) -> str | None:
        return value if value and value.startswith("/") else None


@router.get("/status", operation_id="getAssistantStatus")
async def get_status(request: Request) -> AssistantStatus:
    return AssistantStatus(available=_runtime(request).settings.llm_configured, model=service.MODEL)


@router.get("/conversations", operation_id="listConversations")
async def list_conversations(request: Request) -> list[ConversationOut]:
    async with _runtime(request).sessionmaker() as session:
        rows = await session.scalars(
            select(ChatConversation)
            .where(ChatConversation.updated_at >= datetime.now(UTC) - service.KEEP)
            .order_by(ChatConversation.updated_at.desc())
            .limit(50)
        )
        return [ConversationOut(id=c.id, title=c.title, updated_at=c.updated_at) for c in rows]


@router.get("/conversations/{conversation_id}", operation_id="getConversation")
async def get_conversation(request: Request, conversation_id: int) -> ConversationDetail:
    async with _runtime(request).sessionmaker() as session:
        conversation = await session.get(ChatConversation, conversation_id)
        if conversation is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "discussion introuvable")
        rows = await session.scalars(
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.id)
        )
        return ConversationDetail(
            id=conversation.id,
            title=conversation.title,
            updated_at=conversation.updated_at,
            messages=[
                ChatMessageOut(id=m.id, role=m.role, content=m.content, created_at=m.created_at)
                for m in rows
            ],
        )


@router.delete(
    "/conversations/{conversation_id}",
    operation_id="deleteConversation",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_conversation(request: Request, conversation_id: int) -> None:
    async with _runtime(request).sessionmaker.begin() as session:
        await session.execute(
            delete(ChatConversation).where(ChatConversation.id == conversation_id)
        )


@router.delete(
    "/conversations", operation_id="deleteConversations", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_conversations(request: Request) -> None:
    async with _runtime(request).sessionmaker.begin() as session:
        await session.execute(delete(ChatConversation))


def _sse(event: service.Event) -> str:
    return f"event: {event.type}\ndata: {json.dumps(event.data, ensure_ascii=False)}\n\n"


@router.post(
    "/messages",
    operation_id="askAssistant",
    response_class=StreamingResponse,
    responses={200: {"content": {"text/event-stream": {}}}},
)
async def ask(request: Request, body: QuestionIn) -> StreamingResponse:
    """Réponse en flux SSE : conversation, text (morceaux), tool (lecture), error, done."""
    runtime = _runtime(request)
    async with runtime.sessionmaker() as session:
        profile = await profiles.resolve(session, request.headers.get(profiles.HEADER))
    events = service.answer(
        runtime,
        conversation_id=body.conversation_id,
        text=body.text,
        page=body.page,
        profile_id=profile.id,
    )
    # Les refus (IA absente, plafond, discussion introuvable) avant tout envoi : erreur HTTP.
    try:
        first = await anext(events)
    except service.AssistantUnavailable as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from None

    async def stream() -> AsyncIterator[str]:
        yield _sse(first)
        async for event in events:
            yield _sse(event)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
