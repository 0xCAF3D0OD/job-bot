"""Cloche des alertes (docs/15 §1) : dernières alertes, non lues, lecture."""

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select, update

from jobbot.db.models import Notification
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api/inbox", tags=["inbox"])
SHOWN = 20


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    title: str
    message: str
    link: str | None
    created_at: datetime
    read_at: datetime | None


class Inbox(BaseModel):
    unread: int
    items: list[NotificationOut]


async def _inbox(runtime: Runtime) -> Inbox:
    async with runtime.sessionmaker() as session:
        unread = await session.scalar(
            select(func.count()).select_from(Notification).where(Notification.read_at.is_(None))
        )
        rows = await session.scalars(
            select(Notification)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .limit(SHOWN)
        )
        return Inbox(unread=unread or 0, items=[NotificationOut.model_validate(r) for r in rows])


@router.get("", operation_id="getInbox")
async def get_inbox(request: Request) -> Inbox:
    return await _inbox(_runtime(request))


@router.post("/{notification_id}/read", operation_id="readNotification")
async def read_notification(request: Request, notification_id: int) -> Inbox:
    runtime = _runtime(request)
    async with runtime.sessionmaker.begin() as session:
        notification = await session.get(Notification, notification_id)
        if notification is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "alerte introuvable")
        notification.read_at = notification.read_at or datetime.now(UTC)
    return await _inbox(runtime)


@router.post("/read-all", operation_id="readAllNotifications")
async def read_all(request: Request) -> Inbox:
    runtime = _runtime(request)
    async with runtime.sessionmaker.begin() as session:
        await session.execute(
            update(Notification)
            .where(Notification.read_at.is_(None))
            .values(read_at=datetime.now(UTC))
        )
    return await _inbox(runtime)
