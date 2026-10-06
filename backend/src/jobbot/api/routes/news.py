"""Actualités (docs/15 §2, docs/16) : articles et vidéos, sources, filtres, nouveautés."""

from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.db.models import NewsItem, NewsSource, Profile, ProfileSource
from jobbot.log import get_logger
from jobbot.news import catalog, domain
from jobbot.news.language import LANGUAGES
from jobbot.news.service import SourceError, resolve
from jobbot.profiles import service as profiles
from jobbot.runtime import Runtime
from jobbot.worker.queue import enqueue
from jobbot.worker.tasks.news import NEWS_JOB

router = APIRouter(prefix="/api/news", tags=["news"])
log = get_logger(__name__)
Kind = Literal["articles", "videos"]
# Pays : code ISO à deux lettres, ou INT pour international.
Country = Annotated[str, Field(pattern=r"^([A-Z]{2}|INT)$")]
Language = Annotated[str, Field(pattern=r"^[a-z]{2}$")]
# Fenêtre lue pour filtrer sur « Mon domaine » (le filtre se fait hors de la base).
DOMAIN_WINDOW = 1500


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
    country: str | None
    language: str | None
    labour_market: bool
    # Mots de « Mon domaine » trouvés dans le titre ou le résumé, pour les surligner.
    matched: list[str]


class NewsPage(BaseModel):
    items: list[NewsItemOut]
    # Nouveautés depuis la dernière visite de la page, par rubrique.
    new_articles: int
    new_videos: int
    # Dernier relevé réussi d'une source active ; relevé en attente ou en cours.
    fetched_at: datetime | None
    refreshing: bool
    # Valeurs présentes dans les sources actives, pour les listes de filtres.
    countries: list[str]
    languages: list[str]


class NewsSourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: Kind
    name: str
    url: str
    feed_url: str
    match: str | None
    active: bool
    country: str | None
    language: str | None
    labour_market: bool
    # Veille par recherche : mots-clés suivis dans Google Actualités.
    query: str | None
    fetched_at: datetime | None
    error: str | None


class NewsSourceIn(BaseModel):
    # Adresse https, ou ID de chaîne YouTube (UC…).
    url: Annotated[str, Field(min_length=9, max_length=500)]
    name: Annotated[str, Field(max_length=80)] | None = None
    match: Annotated[str, Field(max_length=80)] | None = None
    # Sans valeur : déduits du domaine et du flux.
    country: Country | None = None
    language: Language | None = None
    labour_market: bool = False


class NewsSourceUpdate(BaseModel):
    """Champs à modifier ; ceux absents restent inchangés. Une valeur vide efface pays ou langue."""

    active: bool | None = None
    country: Country | Literal[""] | None = None
    language: Language | Literal[""] | None = None
    labour_market: bool | None = None


class NewsSearchIn(BaseModel):
    """Veille par recherche (docs/16 §4.2) : seuls ces trois champs partent chez Google."""

    query: Annotated[str, Field(min_length=2, max_length=100)]
    country: Country
    language: Language


class CatalogSourceOut(BaseModel):
    id: str
    name: str
    kind: Kind
    url: str
    domains: list[str]
    country: str
    language: str | None
    labour_market: bool
    description: str
    # Déjà dans tes sources (même flux).
    added: bool


class NewsCatalog(BaseModel):
    # Identifiant → libellé (« devops » → « DevOps et Kubernetes »).
    domains: dict[str, str]
    sources: list[CatalogSourceOut]


class NewsRefresh(BaseModel):
    queued: bool


class NewsPreferences(BaseModel):
    """« Mon domaine » et filtres de la page, retenus d'une visite à l'autre (docs/16 §2-3)."""

    domain_keywords: list[Annotated[str, Field(min_length=1, max_length=40)]] = Field(
        max_length=domain.MAX_KEYWORDS
    )
    domain_only: bool
    countries: list[Country] = Field(max_length=30)
    languages: list[Language] = Field(max_length=len(LANGUAGES))

    @field_validator("domain_keywords")
    @classmethod
    def _dedupe(cls, values: list[str]) -> list[str]:
        seen: dict[str, str] = {}
        for value in values:
            stripped = value.strip()
            if stripped and stripped.casefold() not in seen:
                seen[stripped.casefold()] = stripped
        return list(seen.values())


async def _profile(request: Request) -> Profile:
    """Profil choisi par le navigateur (docs/17), sinon le principal."""
    async with _runtime(request).sessionmaker.begin() as session:
        return await profiles.resolve(session, request.headers.get(profiles.HEADER))


def _followed(profile_id: int, *, active_only: bool = True) -> Any:
    """Identifiants des sources suivies par le profil (sous-requête)."""
    query = select(ProfileSource.source_id).where(ProfileSource.profile_id == profile_id)
    return query.where(ProfileSource.active.is_(True)) if active_only else query


async def _preferences(runtime: Runtime, profile: Profile) -> NewsPreferences:
    """Réglages du profil ; à la première lecture du profil principal, « Mon domaine » est
    pré-rempli depuis les offres postulées ou bien notées, une seule fois."""
    saved = profile.preferences if isinstance(profile.preferences, dict) else {}
    if "domain_keywords" in saved or not profile.is_main:
        return NewsPreferences.model_validate({**profiles.DEFAULT_PREFERENCES, **saved})
    async with runtime.sessionmaker.begin() as session:
        preferences = NewsPreferences.model_validate(
            {**profiles.DEFAULT_PREFERENCES, "domain_keywords": await domain.suggest(session)}
        )
        stored = await session.get(Profile, profile.id)
        if stored is not None:
            stored.preferences = preferences.model_dump()
    return preferences


async def _refreshing(session: AsyncSession) -> bool:
    """Un relevé attend son tour ou tourne (file procrastinate, verrou du nom de la tâche)."""
    found = await session.scalar(
        text(
            "SELECT 1 FROM procrastinate_jobs WHERE queueing_lock = :name"
            " AND status IN ('todo', 'doing') LIMIT 1"
        ).bindparams(name=NEWS_JOB)
    )
    return found is not None


async def _enqueue_news(runtime: Runtime) -> bool:
    """Met un relevé en file ; une erreur de file ne doit pas casser la page."""
    try:
        await enqueue(runtime.settings, NEWS_JOB)
    except Exception:
        log.exception("news_enqueue_failed")
        return False
    return True


@router.get("", operation_id="listNews")
async def list_news(
    request: Request,
    kind: Kind | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 40,
    # Filtres (docs/16) : « Mon domaine », pays des sources, langue des contenus.
    domain_only: bool = False,
    country: Annotated[list[str] | None, Query()] = None,
    language: Annotated[list[str] | None, Query()] = None,
) -> NewsPage:
    runtime = _runtime(request)
    profile = await _profile(request)
    preferences = await _preferences(runtime, profile)
    keywords = preferences.domain_keywords
    followed = _followed(profile.id)
    async with runtime.sessionmaker() as session:
        query = (
            select(NewsItem, NewsSource)
            .join(NewsSource, NewsSource.id == NewsItem.source_id)
            .where(NewsSource.id.in_(followed))
            .order_by(NewsItem.published_at.desc(), NewsItem.id.desc())
            .limit(DOMAIN_WINDOW if domain_only else limit)
        )
        if kind:
            query = query.where(NewsSource.kind == kind)
        if country:
            query = query.where(NewsSource.country.in_(country))
        if language:
            # Une langue inconnue n'est pas cachée : mieux vaut un contenu de trop.
            query = query.where(or_(NewsItem.language.in_(language), NewsItem.language.is_(None)))
        rows = (await session.execute(query)).all()
        found = [
            (item, source, domain.matched(keywords, item.title, item.summary))
            for item, source in rows
        ]
        if domain_only:
            found = [row for row in found if row[2] or row[1].labour_market][:limit]
        seen = profile.news_seen_at
        counts = dict(
            (
                await session.execute(
                    select(NewsSource.kind, func.count())
                    .join(NewsItem, NewsItem.source_id == NewsSource.id)
                    .where(
                        NewsSource.id.in_(followed),
                        NewsItem.created_at > (seen or datetime(1970, 1, 1, tzinfo=UTC)),
                    )
                    .group_by(NewsSource.kind)
                )
            ).all()
        )
        active = list(await session.scalars(select(NewsSource).where(NewsSource.id.in_(followed))))
        languages = set(
            await session.scalars(
                select(NewsItem.language)
                .where(NewsItem.source_id.in_(followed), NewsItem.language.is_not(None))
                .distinct()
            )
        )
        refreshing = await _refreshing(session)
    fetched = [s.fetched_at for s in active if s.fetched_at and not s.error]
    # Page vide après la mise à jour : un premier relevé part tout de suite (docs/16 §1).
    if active and not any(s.fetched_at for s in active) and not refreshing:
        refreshing = await _enqueue_news(runtime)
    return NewsPage(
        items=[
            NewsItemOut(
                id=item.id,
                kind=source.kind,
                source=source.name,
                title=item.title,
                url=item.url,
                summary=item.summary,
                has_image=bool(item.image_key),
                published_at=item.published_at,
                country=source.country,
                language=item.language,
                labour_market=source.labour_market,
                matched=matches,
            )
            for item, source, matches in found
        ],
        new_articles=counts.get("articles", 0),
        new_videos=counts.get("videos", 0),
        fetched_at=max(fetched) if fetched else None,
        refreshing=refreshing,
        countries=sorted({s.country for s in active if s.country}),
        languages=sorted(language for language in languages if language),
    )


@router.post("/refresh", operation_id="refreshNews")
async def refresh_news(request: Request) -> NewsRefresh:
    """« Relever maintenant » : relevé de toutes les sources actives, en arrière-plan."""
    return NewsRefresh(queued=await _enqueue_news(_runtime(request)))


@router.get("/preferences", operation_id="getNewsPreferences")
async def get_preferences(request: Request) -> NewsPreferences:
    return await _preferences(_runtime(request), await _profile(request))


@router.put("/preferences", operation_id="saveNewsPreferences")
async def save_preferences(request: Request, body: NewsPreferences) -> NewsPreferences:
    profile = await _profile(request)
    async with _runtime(request).sessionmaker.begin() as session:
        stored = await session.get(Profile, profile.id)
        if stored is not None:
            stored.preferences = body.model_dump()
    return body


@router.post("/seen", operation_id="markNewsSeen", status_code=status.HTTP_204_NO_CONTENT)
async def mark_seen(request: Request) -> None:
    profile = await _profile(request)
    async with _runtime(request).sessionmaker.begin() as session:
        stored = await session.get(Profile, profile.id)
        if stored is not None:
            stored.news_seen_at = datetime.now(UTC)


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


async def _sources(runtime: Runtime, profile_id: int) -> list[NewsSourceOut]:
    """Sources suivies par le profil ; « active » est celle du profil (pause par profil)."""
    async with runtime.sessionmaker() as session:
        rows = (
            await session.execute(
                select(NewsSource, ProfileSource.active)
                .join(ProfileSource, ProfileSource.source_id == NewsSource.id)
                .where(ProfileSource.profile_id == profile_id)
                .order_by(NewsSource.kind, NewsSource.id)
            )
        ).all()
    return [
        NewsSourceOut.model_validate(
            {
                **{c: getattr(s, c) for c in NewsSourceOut.model_fields if c != "active"},
                "active": active,
            }
        )
        for s, active in rows
    ]


@router.get("/sources", operation_id="listNewsSources")
async def list_sources(request: Request) -> list[NewsSourceOut]:
    return await _sources(_runtime(request), (await _profile(request)).id)


@router.post(
    "/sources",
    operation_id="addNewsSource",
    status_code=status.HTTP_201_CREATED,
    responses={422: {"description": "Aucun flux lisible à cette adresse"}},
)
async def add_source(request: Request, body: NewsSourceIn) -> list[NewsSourceOut]:
    """Site, flux RSS ou chaîne YouTube : le flux est trouvé et vérifié avant l'ajout."""
    try:
        found = await resolve(body.url)
    except SourceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None
    # Ses contenus arrivent tout de suite, sans attendre le relevé des 6 heures (dans _add).
    return await _add(
        request,
        NewsSource(
            kind=found.kind,
            name=(body.name or "").strip() or found.name[:80],
            url=found.url,
            feed_url=found.feed_url,
            match=(body.match or "").strip() or None,
            country=body.country or found.country,
            language=body.language or found.language,
            labour_market=body.labour_market,
        ),
    )


async def _add(request: Request, source: NewsSource) -> list[NewsSourceOut]:
    """Le profil suit la source ; une source déjà connue (suivie par un autre profil) est
    réutilisée, avec ses contenus déjà relevés."""
    runtime = _runtime(request)
    profile = await _profile(request)
    async with runtime.sessionmaker.begin() as session:
        existing = await session.scalar(
            select(NewsSource).where(NewsSource.feed_url == source.feed_url)
        )
        if existing is None:
            session.add(source)
            await session.flush()
            existing = source
        elif await session.get(ProfileSource, (profile.id, existing.id)) is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "cette source est déjà suivie")
        await profiles.subscribe(session, profile.id, existing.id)
    await _enqueue_news(runtime)
    return await _sources(runtime, profile.id)


@router.get("/catalog", operation_id="getNewsCatalog")
async def get_catalog(request: Request) -> NewsCatalog:
    """Sources suggérées, vérifiées, classées par domaine, pays et langue."""
    found = catalog.load()
    profile = await _profile(request)
    async with _runtime(request).sessionmaker() as session:
        followed = set(
            await session.scalars(
                select(NewsSource.feed_url).where(
                    NewsSource.id.in_(_followed(profile.id, active_only=False))
                )
            )
        )
    return NewsCatalog(
        domains=found.domains,
        sources=[
            CatalogSourceOut(
                id=s.id,
                name=s.name,
                kind=s.kind,
                url=s.url,
                domains=s.domains,
                country=s.country,
                language=s.language,
                labour_market=s.labour_market,
                description=s.description,
                added=s.feed_url in followed,
            )
            for s in found.sources
        ],
    )


@router.post(
    "/catalog/{catalog_id}",
    operation_id="addNewsCatalogSource",
    status_code=status.HTTP_201_CREATED,
    responses={404: {"description": "Suggestion inconnue"}, 409: {"description": "Déjà suivie"}},
)
async def add_catalog_source(request: Request, catalog_id: str) -> list[NewsSourceOut]:
    entry = catalog.load().get(catalog_id)
    if entry is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "suggestion inconnue")
    return await _add(
        request,
        NewsSource(
            kind=entry.kind,
            name=entry.name,
            url=entry.url,
            feed_url=entry.feed_url,
            match=entry.match,
            country=entry.country,
            language=entry.language,
            labour_market=entry.labour_market,
        ),
    )


@router.post(
    "/searches",
    operation_id="addNewsSearch",
    status_code=status.HTTP_201_CREATED,
    responses={409: {"description": "Veille déjà suivie"}},
)
async def add_search(request: Request, body: NewsSearchIn) -> list[NewsSourceOut]:
    """Veille par recherche : mots-clés, pays et langue, relevés dans Google Actualités."""
    query = " ".join(body.query.split())
    return await _add(
        request,
        NewsSource(
            kind="articles",
            name=f"Veille : {query}"[:80],
            url="https://news.google.com/",
            feed_url=catalog.search_feed(query, body.country, body.language),
            country=body.country,
            language=body.language,
            query=query,
        ),
    )


@router.patch("/sources/{source_id}", operation_id="updateNewsSource")
async def update_source(
    request: Request, source_id: int, body: NewsSourceUpdate
) -> list[NewsSourceOut]:
    runtime = _runtime(request)
    profile = await _profile(request)
    async with runtime.sessionmaker.begin() as session:
        source = await session.get(NewsSource, source_id)
        subscription = await session.get(ProfileSource, (profile.id, source_id))
        if source is None or subscription is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "source introuvable")
        # La pause vaut pour ce profil ; pays, langue et « marché de l'emploi » décrivent la
        # source elle-même, pour tous les profils.
        if body.active is not None:
            subscription.active = body.active
        if body.country is not None:
            source.country = body.country or None
        if body.language is not None:
            source.language = body.language or None
        if body.labour_market is not None:
            source.labour_market = body.labour_market
    return await _sources(runtime, profile.id)


@router.delete("/sources/{source_id}", operation_id="deleteNewsSource")
async def delete_source(request: Request, source_id: int) -> list[NewsSourceOut]:
    """Le profil ne suit plus la source ; suivie par personne, elle est effacée avec ses
    contenus."""
    runtime = _runtime(request)
    profile = await _profile(request)
    async with runtime.sessionmaker.begin() as session:
        subscription = await session.get(ProfileSource, (profile.id, source_id))
        if subscription is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "source introuvable")
        await session.delete(subscription)
        await session.flush()
        others = await session.scalar(
            select(func.count())
            .select_from(ProfileSource)
            .where(ProfileSource.source_id == source_id)
        )
        if not others:
            source = await session.get(NewsSource, source_id)
            if source is not None:
                await session.delete(source)
    return await _sources(runtime, profile.id)
