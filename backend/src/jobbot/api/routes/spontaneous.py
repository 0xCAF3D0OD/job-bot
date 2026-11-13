"""Candidatures spontanées (docs/39) : une offre créée par toi, sans annonce.

Elle réutilise toute la préparation (lettre, CV, contacts, fiche du formulaire) ; elle n'est
ni notée, ni groupée avec les doublons, ni vérifiée chez l'employeur. À la création, une offre
déjà là chez la même entreprise est signalée, avec le lien pour l'ouvrir : on ne crée qu'après
« Créer quand même ».
"""

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.normalize import normalize_company, normalize_title
from jobbot.db.models import EnrichStatus, Offer, OfferStatus
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api", tags=["offers"])


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


class SpontaneousIn(BaseModel):
    company: Annotated[str, Field(min_length=1, max_length=200)]
    title: Annotated[str, Field(min_length=1, max_length=200)]
    # « Pourquoi cette entreprise ? » : ce qui rend la lettre propre à cette entreprise. Facultatif
    # (paquet du 11 novembre, PR 38).
    reason: Annotated[str, Field(max_length=1500)] = ""
    website: Annotated[str, Field(max_length=300)] | None = None
    # Une offre chez cette entreprise est déjà là, et on crée quand même.
    force: bool = False

    @field_validator("company", "title")
    @classmethod
    def _strip(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("ne doit pas être vide")
        return stripped

    @field_validator("reason")
    @classmethod
    def _reason(cls, value: str) -> str:
        return value.strip()

    @field_validator("website")
    @classmethod
    def _website(cls, value: str | None) -> str | None:
        value = (value or "").strip()
        if not value:
            return None
        return value if value.startswith(("http://", "https://")) else f"https://{value}"


class ExistingOffer(BaseModel):
    id: int
    title: str
    company: str | None
    spontaneous: bool


class SpontaneousOut(BaseModel):
    # None : rien n'est créé, une offre chez cette entreprise est déjà là (`existing`).
    id: int | None
    existing: ExistingOffer | None = None


async def same_company(session: AsyncSession, company: str, title: str) -> Offer | None:
    """L'offre déjà là chez la même entreprise : le même poste d'abord, sinon la plus récente."""
    key = normalize_company(company)
    if not key:
        return None
    offers = await session.scalars(
        select(Offer)
        .where(Offer.company.is_not(None), Offer.duplicate_of.is_(None))
        .order_by(Offer.first_seen_at.desc(), Offer.id.desc())
    )
    found = [o for o in offers if normalize_company(o.company) == key]
    wanted = normalize_title(title)
    return next((o for o in found if normalize_title(o.title) == wanted), None) or (
        found[0] if found else None
    )


def description(body: SpontaneousIn) -> str:
    """Le « texte de l'annonce » que liront la lettre et le CV."""
    lines = [
        "Candidature spontanée : aucune annonce publiée.",
        f"Poste visé : {body.title}",
    ]
    if body.reason:
        lines.append(f"Pourquoi cette entreprise : {body.reason}")
    if body.website:
        lines.append(f"Site : {body.website}")
    return "\n".join(lines)


@router.post(
    "/offers/spontaneous",
    operation_id="createSpontaneousApplication",
    status_code=status.HTTP_201_CREATED,
)
async def create_spontaneous(
    request: Request, response: Response, body: SpontaneousIn
) -> SpontaneousOut:
    now = datetime.now(UTC)
    async with _runtime(request).sessionmaker.begin() as session:
        if not body.force and (found := await same_company(session, body.company, body.title)):
            response.status_code = status.HTTP_200_OK
            return SpontaneousOut(
                id=None,
                existing=ExistingOffer(
                    id=found.id,
                    title=found.title,
                    company=found.company,
                    spontaneous=found.spontaneous,
                ),
            )
        offer = Offer(
            fingerprint=f"spontaneous:{uuid.uuid4()}",
            title=body.title,
            company=body.company,
            status=OfferStatus.PREPARING,
            first_seen_at=now,
            last_seen_at=now,
            enrich_status=EnrichStatus.SKIPPED,
            description=description(body),
            company_website=body.website,
            spontaneous=True,
            spontaneous_reason=body.reason or None,
        )
        session.add(offer)
        await session.flush()
        return SpontaneousOut(id=offer.id)
