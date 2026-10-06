"""Actualités (docs/15 §2) : articles et vidéos, sources, nouveautés depuis la dernière visite."""

from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.db.models import NewsItem, NewsSource, Setting
from jobbot.news.service import SourceError, resolve
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api/news", tags=["news"])
Kind = Literal["articles", "videos"]
SEEN_KEY = "news_seen_at"


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


class NewsItemOut(BaseModel):
    id: int
    kind: Kind
    source: str
    title: str
    url: str
    summary: str | None
    has_image: bool
    published_at: datetime


class NewsPage(BaseModel):
    items: list[NewsItemOut]
    # Nouveautés depuis la dernière visite de la page, par rubrique.
    new_articles: int
    new_videos: int


class NewsSourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: Kind
    name: str
    url: str
    feed_url: str
    match: str | None
    active: bool
    fetched_at: datetime | None
    error: str | None


class NewsSourceIn(BaseModel):
    url: Annotated[str, Field(min_length=9, max_length=500)]
    name: Annotated[str, Field(max_length=80)] | None = None
    match: Annotated[str, Field(max_length=80)] | None = None


class NewsSourceActive(BaseModel):
    active: bool


async def _seen_at(session: AsyncSession) -> datetime | None:
    value = await session.scalar(select(Setting.value).where(Setting.key == SEEN_KEY))
    return datetime.fromisoformat(value) if isinstance(value, str) else None


@router.get("", operation_id="listNews")
async def list_news(
    request: Request,
    kind: Kind | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 40,
) -> NewsPage:
    async with _runtime(request).sessionmaker() as session:
        query = (
            select(NewsItem, NewsSource.kind, NewsSource.name)
            .join(NewsSource, NewsSource.id == NewsItem.source_id)
            .order_by(NewsItem.published_at.desc(), NewsItem.id.desc())
            .limit(limit)
        )
        if kind:
            query = query.where(NewsSource.kind == kind)
        rows = (await session.execute(query)).all()
        seen = await _seen_at(session)
        counts = dict(
            (
                await session.execute(
                    select(NewsSource.kind, func.count())
                    .join(NewsItem, NewsItem.source_id == NewsSource.id)
                    .where(NewsItem.created_at > (seen or datetime(1970, 1, 1, tzinfo=UTC)))
                    .group_by(NewsSource.kind)
                )
            ).all()
        )
    return NewsPage(
        items=[
            NewsItemOut(
                id=item.id,
                kind=item_kind,
                source=name,
                title=item.title,
                url=item.url,
                summary=item.summary,
                has_image=bool(item.image_key),
                published_at=item.published_at,
            )
            for item, item_kind, name in rows
        ],
        new_articles=counts.get("articles", 0),
        new_videos=counts.get("videos", 0),
    )


@router.post("/seen", operation_id="markNewsSeen", status_code=status.HTTP_204_NO_CONTENT)
async def mark_seen(request: Request) -> None:
    now = datetime.now(UTC).isoformat()
    async with _runtime(request).sessionmaker.begin() as session:
        await session.execute(
            insert(Setting)
            .values(key=SEEN_KEY, value=now)
            .on_conflict_do_update(index_elements=["key"], set_={"value": now})
        )


@router.get(
    "/items/{item_id}/image",
    operation_id="getNewsImage",
    response_class=Response,
    responses={200: {"content": {"image/*": {}}}, 404: {"description": "Pas de miniature"}},
)
async def get_news_image(request: Request, item_id: int) -> Response:
    runtime = _runtime(request)
    async with runtime.sessionmaker() as session:
        key = await session.scalar(select(NewsItem.image_key).where(NewsItem.id == item_id))
    if not key:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "pas de miniature")
    try:
        data = runtime.storage.get(key)
    except FileNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "pas de miniature") from None
    extension = key.rsplit(".", 1)[-1]
    media_type = {
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
        "ico": "image/x-icon",
    }.get(extension, "application/octet-stream")
    return Response(
        data,
        media_type=media_type,
        headers={"Cache-Control": "private, max-age=86400", "X-Content-Type-Options": "nosniff"},
    )


async def _sources(runtime: Runtime) -> list[NewsSourceOut]:
    async with runtime.sessionmaker() as session:
        rows = await session.scalars(select(NewsSource).order_by(NewsSource.kind, NewsSource.id))
        return [NewsSourceOut.model_validate(s) for s in rows]


@router.get("/sources", operation_id="listNewsSources")
async def list_sources(request: Request) -> list[NewsSourceOut]:
    return await _sources(_runtime(request))


@router.post(
    "/sources",
    operation_id="addNewsSource",
    status_code=status.HTTP_201_CREATED,
    responses={422: {"description": "Aucun flux lisible à cette adresse"}},
)
async def add_source(request: Request, body: NewsSourceIn) -> list[NewsSourceOut]:
    """Site, flux RSS ou chaîne YouTube : le flux est trouvé et vérifié avant l'ajout."""
    runtime = _runtime(request)
    try:
        found = await resolve(body.url)
    except SourceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None
    async with runtime.sessionmaker.begin() as session:
        if await session.scalar(select(NewsSource.id).where(NewsSource.feed_url == found.feed_url)):
            raise HTTPException(status.HTTP_409_CONFLICT, "cette source est déjà suivie")
        session.add(
            NewsSource(
                kind=found.kind,
                name=(body.name or "").strip() or found.name[:80],
                url=found.url,
                feed_url=found.feed_url,
                match=(body.match or "").strip() or None,
            )
        )
    return await _sources(runtime)


@router.patch("/sources/{source_id}", operation_id="setNewsSourceActive")
async def set_source_active(
    request: Request, source_id: int, body: NewsSourceActive
) -> list[NewsSourceOut]:
    runtime = _runtime(request)
    async with runtime.sessionmaker.begin() as session:
        source = await session.get(NewsSource, source_id)
        if source is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "source introuvable")
        source.active = body.active
    return await _sources(runtime)


@router.delete("/sources/{source_id}", operation_id="deleteNewsSource")
async def delete_source(request: Request, source_id: int) -> list[NewsSourceOut]:
    runtime = _runtime(request)
    async with runtime.sessionmaker.begin() as session:
        source = await session.get(NewsSource, source_id)
        if source is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "source introuvable")
        await session.delete(source)
    return await _sources(runtime)
