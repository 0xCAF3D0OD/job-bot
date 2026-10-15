"""Formations (docs/16 §5) : catalogue filtré selon « Mon domaine », suggestions de l'IA, suivi."""

from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.db.models import ChunkKind, Profile, ProfileChunk, Training, TrainingMark
from jobbot.letters.service import load_identity
from jobbot.news import domain
from jobbot.profiles import service as profiles
from jobbot.runtime import Runtime
from jobbot.trainings import funding, service
from jobbot.trainings.service import SuggestUnavailable

router = APIRouter(prefix="/api/trainings", tags=["trainings"])

Kind = Literal["certification", "cours", "parcours", "atelier"]
Format = Literal["self_paced", "live", "in_person", "exam", "exam_online"]
Level = Literal["beginner", "intermediate", "advanced"]
Price = Literal["free", "paid"]
Status = Literal["interested", "in_progress", "done"]
FundingStatus = Literal["requested", "accepted", "refused"]
KIND_ORDER = {kind: index for index, kind in enumerate(service.KINDS)}

# Le catalogue du dépôt est recopié en base une fois par démarrage de l'API.
_synced = False


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


class TrainingMarkOut(BaseModel):
    status: Status
    progress: str | None
    done_at: date | None
    certified: bool | None
    # Bloc de profil créé depuis la formation (docs/37 §1).
    chunk_id: int | None = None
    # Demande de financement à l'ORP (docs/37 §2).
    funding_status: FundingStatus | None = None
    funding_requested_at: date | None = None


class TrainingOut(BaseModel):
    id: int
    title: str
    provider: str
    kind: Kind
    format: Format
    language: str
    price: Price
    duration: str | None
    level: Level | None
    url: str
    tags: list[str]
    description: str | None
    prep: str | None
    origin: Literal["catalog", "ai"]
    # Suggestion de l'IA pas encore gardée : « à vérifier ».
    verified: bool
    # Mots de « Mon domaine » trouvés, pour les surligner.
    matched: list[str]
    mark: TrainingMarkOut | None


class TrainingPage(BaseModel):
    items: list[TrainingOut]
    domain_keywords: list[str]
    languages: list[str]
    # Suggestions de l'IA possibles (clé API configurée).
    can_suggest: bool


class TrainingMarkIn(BaseModel):
    status: Status
    progress: Annotated[str, Field(max_length=80)] | None = None
    done_at: date | None = None
    certified: bool | None = None


class TrainingReview(BaseModel):
    """Suggestion de l'IA : la garder (vérifiée) ou l'écarter (ne plus la proposer)."""

    keep: bool


class SuggestResult(BaseModel):
    added: int


async def _ensure_catalog(runtime: Runtime) -> None:
    global _synced
    if _synced:
        return
    async with runtime.sessionmaker.begin() as session:
        await service.sync_catalog(session)
    _synced = True


@router.get("", operation_id="listTrainings")
async def list_trainings(request: Request, domain_only: bool = False) -> TrainingPage:
    runtime = _runtime(request)
    await _ensure_catalog(runtime)
    async with runtime.sessionmaker.begin() as session:
        # « Mon domaine », suggestions et suivi du profil choisi (docs/17 §4).
        profile = await profiles.resolve(session, request.headers.get(profiles.HEADER))
        keywords = await domain.keywords(session, profile.id)
        rows = (
            await session.execute(
                select(Training, TrainingMark)
                .outerjoin(
                    TrainingMark,
                    (TrainingMark.training_id == Training.id)
                    & (TrainingMark.profile_id == profile.id),
                )
                .where(
                    Training.dismissed.is_(False),
                    or_(Training.profile_id.is_(None), Training.profile_id == profile.id),
                )
            )
        ).all()
    items: list[TrainingOut] = []
    for training, mark in rows:
        matched = domain.matched(
            keywords,
            training.title,
            training.description,
            training.prep,
            " · ".join(training.tags),
        )
        # Une formation suivie reste visible, même hors de « Mon domaine ».
        if domain_only and not matched and mark is None:
            continue
        items.append(
            TrainingOut(
                id=training.id,
                title=training.title,
                provider=training.provider,
                kind=training.kind,
                format=training.format,
                language=training.language,
                price=training.price,
                duration=training.duration,
                level=training.level,
                url=training.url,
                tags=training.tags,
                description=training.description,
                prep=training.prep,
                origin=training.origin,
                verified=training.verified,
                matched=matched,
                mark=TrainingMarkOut(
                    status=mark.status,
                    progress=mark.progress,
                    done_at=mark.done_at,
                    certified=mark.certified,
                    chunk_id=mark.chunk_id,
                    funding_status=mark.funding_status,
                    funding_requested_at=mark.funding_requested_at,
                )
                if mark
                else None,
            )
        )
    # Les plus proches de ton domaine d'abord, puis certifications, cours, parcours, ateliers.
    items.sort(key=lambda t: (-len(t.matched), KIND_ORDER.get(t.kind, 9), t.title.casefold()))
    return TrainingPage(
        items=items,
        domain_keywords=keywords,
        languages=sorted({t.language for t in items}),
        can_suggest=runtime.settings.llm_configured,
    )


async def _visible(session: AsyncSession, request: Request, training_id: int) -> Profile:
    """Profil choisi, si la formation lui est visible (catalogue ou sa propre suggestion)."""
    profile = await profiles.resolve(session, request.headers.get(profiles.HEADER))
    training = await session.get(Training, training_id)
    if training is None or training.profile_id not in (None, profile.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "formation introuvable")
    return profile


@router.put("/{training_id}/mark", operation_id="markTraining")
async def mark_training(
    request: Request, training_id: int, body: TrainingMarkIn
) -> TrainingMarkOut:
    async with _runtime(request).sessionmaker.begin() as session:
        profile = await _visible(session, request, training_id)
        values = {
            "status": body.status,
            "progress": (body.progress or "").strip() or None
            if body.status == "in_progress"
            else None,
            "done_at": body.done_at if body.status == "done" else None,
            "certified": body.certified if body.status == "done" else None,
        }
        kept = (
            await session.execute(
                insert(TrainingMark)
                .values(profile_id=profile.id, training_id=training_id, **values)
                .on_conflict_do_update(index_elements=["profile_id", "training_id"], set_=values)
                .returning(
                    TrainingMark.chunk_id,
                    TrainingMark.funding_status,
                    TrainingMark.funding_requested_at,
                )
            )
        ).one()
    return TrainingMarkOut(
        **values,
        chunk_id=kept.chunk_id,
        funding_status=kept.funding_status,
        funding_requested_at=kept.funding_requested_at,
    )


@router.delete(
    "/{training_id}/mark", operation_id="unmarkTraining", status_code=status.HTTP_204_NO_CONTENT
)
async def unmark_training(request: Request, training_id: int) -> None:
    async with _runtime(request).sessionmaker.begin() as session:
        profile = await profiles.resolve(session, request.headers.get(profiles.HEADER))
        mark = await session.get(TrainingMark, (profile.id, training_id))
        if mark is not None:
            await session.delete(mark)


@router.post(
    "/{training_id}/review", operation_id="reviewTraining", status_code=status.HTTP_204_NO_CONTENT
)
async def review_training(request: Request, training_id: int, body: TrainingReview) -> None:
    async with _runtime(request).sessionmaker.begin() as session:
        profile = await profiles.resolve(session, request.headers.get(profiles.HEADER))
        training = await session.get(Training, training_id)
        if training is None or training.origin != "ai" or training.profile_id != profile.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "suggestion introuvable")
        training.verified = body.keep
        training.dismissed = not body.keep


@router.post(
    "/suggest",
    operation_id="suggestTrainings",
    responses={409: {"description": "IA indisponible, plafond atteint ou domaine vide"}},
)
async def suggest_trainings(request: Request) -> SuggestResult:
    """Recherche de formations par l'IA (environ 0,02 à 0,05 $), dans le plafond mensuel."""
    runtime = _runtime(request)
    await _ensure_catalog(runtime)
    try:
        async with runtime.sessionmaker.begin() as session:
            profile = await profiles.resolve(session, request.headers.get(profiles.HEADER))
        added = await service.suggest(runtime, profile.id)
    except SuggestUnavailable as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from None
    return SuggestResult(added=added)


class ProfileBlockIn(BaseModel):
    """Bloc « formation » proposé depuis une formation terminée, relu avant l'envoi."""

    title: Annotated[str, Field(min_length=1, max_length=200)]
    content: Annotated[str, Field(min_length=1, max_length=20_000)]
    tags: list[Annotated[str, Field(min_length=1, max_length=40)]] = Field(
        default_factory=list, max_length=20
    )


@router.post(
    "/{training_id}/profile-block",
    operation_id="addTrainingToProfile",
    status_code=status.HTTP_201_CREATED,
)
async def add_to_profile(
    request: Request, training_id: int, body: ProfileBlockIn
) -> TrainingMarkOut:
    """Une formation terminée entre dans Mon parcours (docs/37 §1). Rien n'est renoté :
    les notes existantes sont « faites avec un ancien profil » jusqu'à « Renoter »."""
    async with _runtime(request).sessionmaker.begin() as session:
        profile = await _visible(session, request, training_id)
        if not profile.is_main:
            # Les blocs servent aux lettres et aux CV : ils appartiennent au profil principal.
            raise HTTPException(
                status.HTTP_409_CONFLICT, "les blocs de profil appartiennent au profil principal"
            )
        mark = await session.get(TrainingMark, (profile.id, training_id))
        if mark is None or mark.status != "done":
            raise HTTPException(status.HTTP_409_CONFLICT, "formation pas encore terminée")
        tags: dict[str, str] = {}
        for tag in body.tags:
            if cleaned := tag.strip():
                tags.setdefault(cleaned.casefold(), cleaned)
        chunk = ProfileChunk(
            kind=ChunkKind.FORMATION,
            title=body.title.strip(),
            content=body.content.strip(),
            tags=list(tags.values()),
        )
        session.add(chunk)
        await session.flush()
        mark.chunk_id = chunk.id
        return _mark_out(mark)


def _mark_out(mark: TrainingMark) -> TrainingMarkOut:
    return TrainingMarkOut(
        status=mark.status,
        progress=mark.progress,
        done_at=mark.done_at,
        certified=mark.certified,
        chunk_id=mark.chunk_id,
        funding_status=mark.funding_status,
        funding_requested_at=mark.funding_requested_at,
    )


# --- Demande de financement à l'ORP (docs/37 §2) ------------------------------------------


class FundingExample(BaseModel):
    title: str
    company: str | None


class FundingRequest(BaseModel):
    """De quoi écrire la demande : l'argument tiré de tes offres et ton nom."""

    offers: int
    matched: list[str]
    examples: list[FundingExample]
    sender: str | None


class FundingIn(BaseModel):
    # Sans valeur : la demande est retirée.
    status: FundingStatus | None


@router.get("/{training_id}/funding-request", operation_id="trainingFundingRequest")
async def funding_request(request: Request, training_id: int) -> FundingRequest:
    async with _runtime(request).sessionmaker() as session:
        await _visible(session, request, training_id)
        training = await session.get(Training, training_id)
        assert training is not None
        found = await funding.argument(session, training)
        identity = await load_identity(session)
    return FundingRequest(
        offers=found.offers,
        matched=found.matched,
        examples=[FundingExample(title=e.title, company=e.company) for e in found.examples],
        sender=identity.name,
    )


@router.put("/{training_id}/funding", operation_id="setTrainingFunding")
async def set_funding(request: Request, training_id: int, body: FundingIn) -> TrainingMarkOut:
    async with _runtime(request).sessionmaker.begin() as session:
        profile = await _visible(session, request, training_id)
        mark = await session.get(TrainingMark, (profile.id, training_id))
        if mark is None:
            raise HTTPException(status.HTTP_409_CONFLICT, "marque d'abord la formation")
        if body.status == "requested" and mark.funding_status != "requested":
            mark.funding_requested_at = funding.local_today()
            mark.funding_reminded_at = None
        if body.status is None:
            mark.funding_requested_at = None
            mark.funding_reminded_at = None
        mark.funding_status = body.status
        return _mark_out(mark)
