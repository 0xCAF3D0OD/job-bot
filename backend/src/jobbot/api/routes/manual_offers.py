"""Ajouter une offre trouvée ailleurs (docs/111) : lire l'annonce, puis l'ajouter.

La lecture ne crée rien : elle rend une fiche à relire. L'ajout crée l'offre, qui passe par
le filtre et la note comme une offre reçue. Dans la démo, le garde des écritures refuse les
deux (docs/72).
"""

from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select

from jobbot import manual_offers
from jobbot.db.models import Evaluation, Offer
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api/offers/manual", tags=["offers"])


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


def _url(value: str | None) -> str | None:
    value = (value or "").strip()
    if not value:
        return None
    return value if value.startswith(("http://", "https://")) else f"https://{value}"


class ManualContext(BaseModel):
    # Le métier, pour les exemples du formulaire ; les offres ajoutées sur 24 heures.
    trade: str | None
    added_today: int
    daily_limit: int


class ManualReadIn(BaseModel):
    url: Annotated[str, Field(max_length=2000)] | None = None
    text: Annotated[str, Field(max_length=manual_offers.MAX_TEXT)] | None = None

    @field_validator("url")
    @classmethod
    def _clean_url(cls, value: str | None) -> str | None:
        return _url(value)


class ManualDraft(BaseModel):
    title: str
    company: str | None
    location: str | None
    description: str | None
    url: str | None
    read_by: Literal["page", "ia"]
    trade: str | None
    matches_trade: bool
    existing_offer_id: int | None


class ManualReadOut(BaseModel):
    draft: ManualDraft | None = None
    # Ce qui a empêché la lecture ; `paste` : proposer de coller le texte de l'annonce.
    problem: str | None = None
    paste: bool = False


class ManualAddIn(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=300)]
    company: Annotated[str, Field(max_length=300)] | None = None
    location: Annotated[str, Field(max_length=300)] | None = None
    description: Annotated[str, Field(max_length=manual_offers.MAX_TEXT)] | None = None
    url: Annotated[str, Field(max_length=2000)] | None = None
    read_by: Literal["page", "ia", "main"] = "main"

    @field_validator("url")
    @classmethod
    def _clean_url(cls, value: str | None) -> str | None:
        return _url(value)

    @field_validator("title")
    @classmethod
    def _title(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("ne doit pas être vide")
        return value.strip()


class ManualAddOut(BaseModel):
    id: int
    # Déjà là : on ouvre celle qui existe.
    existing: bool
    status: str
    # La raison, quand les critères l'écartent (elle est gardée quand même).
    reasons: list[str]


@router.get("", operation_id="getManualOfferContext")
async def context(request: Request) -> ManualContext:
    async with _runtime(request).sessionmaker() as session:
        trade, _words = await manual_offers.trade(session)
        added = await manual_offers.added_today(session)
    return ManualContext(trade=trade, added_today=added, daily_limit=manual_offers.DAILY_LIMIT)


@router.post("/read", operation_id="readManualOffer")
async def read(request: Request, body: ManualReadIn) -> ManualReadOut:
    try:
        draft = await manual_offers.read(_runtime(request), body.url, body.text)
    except manual_offers.ReadProblem as exc:
        return ManualReadOut(problem=exc.message, paste=exc.paste)
    return ManualReadOut(
        draft=ManualDraft(
            title=draft.title,
            company=draft.company,
            location=draft.location,
            description=draft.description,
            url=draft.url,
            read_by="ia" if draft.read_by == "ia" else "page",
            trade=draft.trade,
            matches_trade=draft.matches_trade,
            existing_offer_id=draft.existing_offer_id,
        )
    )


@router.post("", operation_id="addManualOffer", status_code=status.HTTP_201_CREATED)
async def add(request: Request, body: ManualAddIn) -> ManualAddOut:
    runtime = _runtime(request)
    draft = manual_offers.Draft(
        title=body.title,
        company=body.company,
        location=body.location,
        description=(body.description or "").strip() or None,
        url=body.url,
        read_by=body.read_by,
    )
    async with runtime.sessionmaker() as session:
        existing = (await manual_offers._complete(session, draft)).existing_offer_id
    if existing is None:
        try:
            offer_id = await manual_offers.add(runtime, draft)
        except manual_offers.ReadProblem as exc:
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, exc.message) from exc
    else:
        offer_id = existing
    async with runtime.sessionmaker() as session:
        offer = await session.get(Offer, offer_id)
        found = await session.scalar(
            select(Evaluation.filter_reasons).where(Evaluation.offer_id == offer_id)
        )
        reasons = [
            str(r["message"]) for r in found or [] if isinstance(r, dict) and r.get("message")
        ]
        return ManualAddOut(
            id=offer_id,
            existing=existing is not None,
            status=offer.status if offer is not None else "new",
            reasons=reasons,
        )
