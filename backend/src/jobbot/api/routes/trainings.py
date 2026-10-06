"""Formations (docs/16 §5) : catalogue filtré selon « Mon domaine », suggestions de l'IA, suivi."""

from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from jobbot.db.models import Training, TrainingMark
from jobbot.news import domain
from jobbot.profiles import service as profiles
from jobbot.runtime import Runtime
from jobbot.trainings import service
from jobbot.trainings.service import SuggestUnavailable

router = APIRouter(prefix="/api/trainings", tags=["trainings"])

Kind = Literal["certification", "cours", "parcours", "atelier"]
Format = Literal["self_paced", "live", "in_person", "exam", "exam_online"]
Level = Literal["beginner", "intermediate", "advanced"]
Price = Literal["free", "paid"]
Status = Literal["interested", "in_progress", "done"]
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
        # « Mon domaine » du profil choisi (docs/17) ; le suivi par profil vient en 0.10.0-b.
        profile = await profiles.resolve(session, request.headers.get(profiles.HEADER))
        keywords = await domain.keywords(session, profile.id)
        rows = (
            await session.execute(
                select(Training, TrainingMark)
                .outerjoin(TrainingMark, TrainingMark.training_id == Training.id)
                .where(Training.dismissed.is_(False))
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


@router.put("/{training_id}/mark", operation_id="markTraining")
async def mark_training(
    request: Request, training_id: int, body: TrainingMarkIn
) -> TrainingMarkOut:
    async with _runtime(request).sessionmaker.begin() as session:
        if await session.get(Training, training_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "formation introuvable")
        values = {
            "status": body.status,
            "progress": (body.progress or "").strip() or None
            if body.status == "in_progress"
            else None,
            "done_at": body.done_at if body.status == "done" else None,
            "certified": body.certified if body.status == "done" else None,
        }
        await session.execute(
            insert(TrainingMark)
            .values(training_id=training_id, **values)
            .on_conflict_do_update(index_elements=["training_id"], set_=values)
        )
    return TrainingMarkOut(**values)


@router.delete(
    "/{training_id}/mark", operation_id="unmarkTraining", status_code=status.HTTP_204_NO_CONTENT
)
async def unmark_training(request: Request, training_id: int) -> None:
    async with _runtime(request).sessionmaker.begin() as session:
        mark = await session.get(TrainingMark, training_id)
        if mark is not None:
            await session.delete(mark)


@router.post(
    "/{training_id}/review", operation_id="reviewTraining", status_code=status.HTTP_204_NO_CONTENT
)
async def review_training(request: Request, training_id: int, body: TrainingReview) -> None:
    async with _runtime(request).sessionmaker.begin() as session:
        training = await session.get(Training, training_id)
        if training is None or training.origin != "ai":
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
