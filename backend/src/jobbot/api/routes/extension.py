"""Extension du navigateur (docs/25) : routes appelées par l'extension, et ses jetons.

`/api/extension/…` : réservé à l'extension, avec son jeton (`Authorization: Bearer …`,
vérifié par le middleware). `/api/extension-tokens` : gestion des jetons depuis les
Réglages, avec la session habituelle.
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select

from jobbot.api.routes import applications as application_routes
from jobbot.api.routes import cvs as cv_routes
from jobbot.api.routes import letters as letter_routes
from jobbot.db.models import Application, DraftKind, ExtensionToken, Offer
from jobbot.extension import service
from jobbot.letters.service import current_draft, load_identity
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api/extension", tags=["extension"])
tokens_router = APIRouter(prefix="/api/extension-tokens", tags=["extension"])


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


# --- Pour l'extension ---------------------------------------------------------------------


class ExtensionMe(BaseModel):
    platform: str
    version: str


class OfferBrief(BaseModel):
    id: int
    title: str
    company: str | None
    applied: bool


class MatchOut(BaseModel):
    offer: OfferBrief | None
    choices: list[OfferBrief]


class FillIdentity(BaseModel):
    name: str | None
    street: str | None
    postcode: str | None
    city: str | None
    phone: str | None
    email: str | None
    linkedin: str | None
    website: str | None
    availability: str | None
    salary: str | None
    permit: str | None


class FillOut(BaseModel):
    """Tout ce que l'extension met dans le formulaire (docs/25 §3.2)."""

    offer: OfferBrief
    identity: FillIdentity
    letter_text: str | None
    has_letter: bool
    has_cv: bool
    letter_filename: str
    cv_filename: str


class SentIn(BaseModel):
    url: Annotated[str, Field(max_length=1000)] | None = None


class SentOut(BaseModel):
    application_id: int
    orp_month: str


class QuestionIn(BaseModel):
    offer_id: int
    question: Annotated[str, Field(min_length=2, max_length=1000)]

    @field_validator("question")
    @classmethod
    def _strip(cls, value: str) -> str:
        return " ".join(value.split())


class AnswerOut(BaseModel):
    text: str


def _brief(offer: Offer) -> OfferBrief:
    return OfferBrief(
        id=offer.id, title=offer.title, company=offer.company, applied=offer.status == "applied"
    )


def _company(offer: Offer) -> str:
    return "".join(c for c in (offer.company or "employeur") if c.isalnum() or c in " -").strip()[
        :60
    ]


async def _offer(request: Request, offer_id: int) -> Offer:
    async with _runtime(request).sessionmaker() as session:
        offer = await session.get(Offer, offer_id)
    if offer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "offre introuvable")
    return offer


@router.get("/me", operation_id="extensionMe")
async def me(request: Request) -> ExtensionMe:
    """Vérifie le jeton au moment de relier l'extension."""
    return ExtensionMe(platform="job-bot", version=_runtime(request).settings.version)


@router.get("/match", operation_id="extensionMatch")
async def match(request: Request, url: Annotated[str, Query(max_length=2000)]) -> MatchOut:
    async with _runtime(request).sessionmaker() as session:
        found, choices = await service.match(session, url)
    return MatchOut(offer=_brief(found) if found else None, choices=[_brief(o) for o in choices])


@router.get("/offers/{offer_id}", operation_id="extensionFill")
async def fill(request: Request, offer_id: int) -> FillOut:
    async with _runtime(request).sessionmaker() as session:
        offer = await session.get(Offer, offer_id)
        if offer is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "offre introuvable")
        identity = await load_identity(session)
        letter = await current_draft(session, offer_id, DraftKind.LETTER)
        cv = await current_draft(session, offer_id, DraftKind.CV)
    paragraphs = (
        [p.get("text", "") for p in (letter.content.get("paragraphs") or [])] if letter else []
    )
    company = _company(offer)
    return FillOut(
        offer=_brief(offer),
        identity=FillIdentity(**identity.__dict__),
        letter_text="\n\n".join(p for p in paragraphs if p) or None,
        has_letter=letter is not None,
        has_cv=cv is not None,
        letter_filename=f"Lettre - {company}.pdf",
        cv_filename=f"CV - {company}.pdf",
    )


@router.get(
    "/offers/{offer_id}/letter.pdf",
    operation_id="extensionLetterPdf",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
async def letter_pdf(request: Request, offer_id: int) -> Response:
    await _offer(request, offer_id)
    async with _runtime(request).sessionmaker() as session:
        draft = await current_draft(session, offer_id, DraftKind.LETTER)
    if draft is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "aucune lettre pour cette offre")
    return await letter_routes.download_letter_pdf(request, draft.id)


@router.get(
    "/offers/{offer_id}/cv.pdf",
    operation_id="extensionCvPdf",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
async def cv_pdf(request: Request, offer_id: int) -> Response:
    await _offer(request, offer_id)
    async with _runtime(request).sessionmaker() as session:
        draft = await current_draft(session, offer_id, DraftKind.CV)
    if draft is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "aucun CV pour cette offre")
    return await cv_routes.download_cv_pdf(request, draft.id)


@router.post("/offers/{offer_id}/sent", operation_id="extensionSent")
async def sent(request: Request, offer_id: int, body: SentIn) -> SentOut:
    """« J'ai envoyé » : comme « Marquer comme envoyée », avec l'adresse du formulaire."""
    async with _runtime(request).sessionmaker() as session:
        existing = await session.scalar(select(Application).where(Application.offer_id == offer_id))
    if existing is not None:
        return SentOut(application_id=existing.id, orp_month=existing.orp_month)
    prefill = await application_routes.get_application_prefill(request, offer_id)
    values = prefill.model_dump()
    if body.url and body.url.startswith(("http://", "https://")):
        values["application_url"] = body.url
    created = await application_routes.create_application(
        request, application_routes.ApplicationIn(**values)
    )
    return SentOut(application_id=created.id, orp_month=created.orp_month)


@router.post("/answer", operation_id="extensionAnswer")
async def answer(request: Request, body: QuestionIn) -> AnswerOut:
    try:
        result = await service.answer(_runtime(request), body.offer_id, body.question)
    except service.AnswerUnavailable as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from None
    return AnswerOut(text=result.text)


# --- Jetons (Réglages) --------------------------------------------------------------------


class TokenOut(BaseModel):
    id: int
    name: str
    created_at: datetime
    last_used_at: datetime | None


class TokenCreated(TokenOut):
    # Montré une seule fois : seule son empreinte est gardée.
    token: str


class TokenIn(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=80)] = "Mon navigateur"


def _token_out(row: ExtensionToken) -> TokenOut:
    return TokenOut(
        id=row.id, name=row.name, created_at=row.created_at, last_used_at=row.last_used_at
    )


@tokens_router.get("", operation_id="listExtensionTokens")
async def list_tokens(request: Request) -> list[TokenOut]:
    async with _runtime(request).sessionmaker() as session:
        rows = await session.scalars(
            select(ExtensionToken)
            .where(ExtensionToken.revoked_at.is_(None))
            .order_by(ExtensionToken.id.desc())
        )
        return [_token_out(r) for r in rows]


@tokens_router.post("", operation_id="createExtensionToken", status_code=status.HTTP_201_CREATED)
async def create_token(request: Request, body: TokenIn) -> TokenCreated:
    async with _runtime(request).sessionmaker.begin() as session:
        row, token = await service.create_token(session, body.name.strip() or "Mon navigateur")
        await session.refresh(row)
        return TokenCreated(**_token_out(row).model_dump(), token=token)


@tokens_router.delete(
    "/{token_id}", operation_id="revokeExtensionToken", status_code=status.HTTP_204_NO_CONTENT
)
async def revoke_token(request: Request, token_id: int) -> None:
    async with _runtime(request).sessionmaker.begin() as session:
        row = await session.get(ExtensionToken, token_id)
        if row is not None and row.revoked_at is None:
            row.revoked_at = datetime.now(UTC)
