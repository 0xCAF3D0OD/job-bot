"""Candidatures spontanées (docs/39) : une offre créée par toi, sans annonce.

Elle réutilise toute la préparation (lettre, CV, contacts, fiche du formulaire) ; elle n'est
ni notée, ni comparée aux doublons, ni vérifiée chez l'employeur.
"""

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Request, status
from pydantic import BaseModel, Field, field_validator

from jobbot.db.models import EnrichStatus, Offer, OfferStatus
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api", tags=["offers"])


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


class SpontaneousIn(BaseModel):
    company: Annotated[str, Field(min_length=1, max_length=200)]
    title: Annotated[str, Field(min_length=1, max_length=200)]
    # « Pourquoi elle » : ce qui rend la lettre propre à cette entreprise.
    reason: Annotated[str, Field(min_length=1, max_length=1500)]
    website: Annotated[str, Field(max_length=300)] | None = None

    @field_validator("company", "title", "reason")
    @classmethod
    def _strip(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("ne doit pas être vide")
        return stripped

    @field_validator("website")
    @classmethod
    def _website(cls, value: str | None) -> str | None:
        value = (value or "").strip()
        if not value:
            return None
        return value if value.startswith(("http://", "https://")) else f"https://{value}"


class SpontaneousOut(BaseModel):
    id: int


def description(body: SpontaneousIn) -> str:
    """Le « texte de l'annonce » que liront la lettre et le CV."""
    lines = [
        "Candidature spontanée : aucune annonce publiée.",
        f"Poste visé : {body.title}",
        f"Pourquoi cette entreprise : {body.reason}",
    ]
    if body.website:
        lines.append(f"Site : {body.website}")
    return "\n".join(lines)


@router.post(
    "/offers/spontaneous",
    operation_id="createSpontaneousApplication",
    status_code=status.HTTP_201_CREATED,
)
async def create_spontaneous(request: Request, body: SpontaneousIn) -> SpontaneousOut:
    now = datetime.now(UTC)
    async with _runtime(request).sessionmaker.begin() as session:
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
            spontaneous_reason=body.reason,
        )
        session.add(offer)
        await session.flush()
        return SpontaneousOut(id=offer.id)
