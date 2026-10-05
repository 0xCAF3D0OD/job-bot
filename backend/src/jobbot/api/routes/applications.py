"""Tri manuel des offres, candidatures envoyées et coordonnées (docs/08-candidatures.md).

Les coordonnées de Kevin servent à l'en-tête des documents (0.5.0-b) : elles restent en base
locale et ne sont jamais envoyées à l'IA.
"""

from dataclasses import asdict
from datetime import UTC, date, datetime
from typing import Annotated, Literal
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from jobbot.api.routes.orp import mark_changed
from jobbot.db.models import (
    Application,
    ApplicationMethod,
    ApplicationStatus,
    DraftKind,
    Offer,
    OfferStatus,
    Setting,
)
from jobbot.letters.service import IDENTITY_KEYS, current_draft, load_identity
from jobbot.log import get_logger
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api", tags=["applications"])
log = get_logger(__name__)
LOCAL_TZ = ZoneInfo("Europe/Zurich")

ShortText = Annotated[str, Field(max_length=300)]


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


# --- Tri manuel des offres --------------------------------------------------------------


class OfferStatusIn(BaseModel):
    # « applied » se pose en créant une candidature, pas ici.
    status: Literal["to_review", "later", "ignored", "preparing"]


class OfferStatusOut(BaseModel):
    id: int
    status: OfferStatus


@router.patch("/offers/{offer_id}/status", operation_id="setOfferStatus")
async def set_offer_status(request: Request, offer_id: int, body: OfferStatusIn) -> OfferStatusOut:
    async with _runtime(request).sessionmaker.begin() as session:
        offer = await session.get(Offer, offer_id)
        if offer is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "offre introuvable")
        has_application = await session.scalar(
            select(Application.id).where(Application.offer_id == offer_id)
        )
        if has_application:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "une candidature est enregistrée pour cette offre : la supprimer d'abord",
            )
        offer.status = body.status
    return OfferStatusOut(id=offer_id, status=OfferStatus(body.status))


class OfferExpiryIn(BaseModel):
    expired: bool


class OfferExpiryOut(BaseModel):
    id: int
    expired_at: datetime | None
    expiry_source: str | None
    expiry_override: str | None


@router.patch(
    "/offers/{offer_id}/expiry",
    operation_id="setOfferExpiry",
    responses={409: {"description": "Candidature déjà envoyée"}},
)
async def set_offer_expiry(request: Request, offer_id: int, body: OfferExpiryIn) -> OfferExpiryOut:
    """« Signaler comme expirée » ou « Pas expirée » (docs/11 §1) : le choix de Kevin passe
    avant la détection automatique, dans les deux sens."""
    async with _runtime(request).sessionmaker.begin() as session:
        offer = await session.get(Offer, offer_id)
        if offer is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "offre introuvable")
        if offer.status == OfferStatus.APPLIED:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "candidature envoyée : l'offre n'est plus modifiée"
            )
        if body.expired:
            offer.expired_at = datetime.now(UTC)
            offer.expiry_source, offer.expiry_override = "manual", "expired"
        else:
            offer.expired_at = offer.expiry_source = None
            offer.expiry_override = "alive"
        return OfferExpiryOut(
            id=offer.id,
            expired_at=offer.expired_at,
            expiry_source=offer.expiry_source,
            expiry_override=offer.expiry_override,
        )


class OfferAddressIn(BaseModel):
    # None ou vide : efface l'adresse.
    address: Annotated[str, Field(max_length=300)] | None = None


class OfferAddressOut(BaseModel):
    id: int
    company_address: str | None
    company_address_source: str | None


@router.patch("/offers/{offer_id}/address", operation_id="setOfferAddress")
async def set_offer_address(
    request: Request, offer_id: int, body: OfferAddressIn
) -> OfferAddressOut:
    """Adresse corrigée ou saisie par Kevin : prioritaire sur toute source automatique."""
    address = "\n".join(line.strip() for line in (body.address or "").splitlines() if line.strip())
    async with _runtime(request).sessionmaker.begin() as session:
        offer = await session.get(Offer, offer_id)
        if offer is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "offre introuvable")
        offer.company_address = address or None
        offer.company_address_source = "manual" if address else None
        return OfferAddressOut(
            id=offer.id,
            company_address=offer.company_address,
            company_address_source=offer.company_address_source,
        )


# --- Candidatures ---------------------------------------------------------------------


class ApplicationBase(BaseModel):
    sent_at: date
    method: ApplicationMethod = ApplicationMethod.ELECTRONIQUE
    assigned_by_orp: bool = False
    company: Annotated[str, Field(min_length=1, max_length=300)]
    company_address: ShortText | None = None
    contact_name: ShortText | None = None
    contact_phone: ShortText | None = None
    job_title: Annotated[str, Field(min_length=1, max_length=300)]
    location: ShortText | None = None
    rate_text: ShortText | None = None

    @field_validator("company", "job_title")
    @classmethod
    def _required(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("ne doit pas être vide")
        return stripped

    @field_validator("company_address", "contact_name", "contact_phone", "location", "rate_text")
    @classmethod
    def _strip(cls, value: str | None) -> str | None:
        return _clean(value)


class ApplicationIn(ApplicationBase):
    offer_id: int | None = None


class ApplicationUpdate(ApplicationBase):
    status: ApplicationStatus = ApplicationStatus.EN_ATTENTE
    status_reason: ShortText | None = None
    status_at: date | None = None
    interview_at: datetime | None = None


class ApplicationOut(ApplicationUpdate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    offer_id: int | None
    letter_draft_id: int | None
    cv_draft_id: int | None
    orp_month: str
    reminded_at: datetime | None
    created_at: datetime


class ApplicationPrefill(ApplicationBase):
    offer_id: int


class MonthSummary(BaseModel):
    month: str
    count: int
    # Objectif fixé par le conseiller ORP (Réglages) ; None s'il n'est pas saisi.
    target: int | None


def _rate_text(offer: Offer) -> str | None:
    if offer.rate_min is None or offer.rate_max is None:
        return None
    if offer.rate_max >= 100:
        if offer.rate_min >= 100:
            return "plein temps"
        return f"plein temps ou temps partiel ({offer.rate_min}-{offer.rate_max} %)"
    if offer.rate_min == offer.rate_max:
        return f"temps partiel ({offer.rate_max} %)"
    return f"temps partiel ({offer.rate_min}-{offer.rate_max} %)"


def _today() -> date:
    return datetime.now(UTC).astimezone(LOCAL_TZ).date()


@router.get("/offers/{offer_id}/application-prefill", operation_id="getApplicationPrefill")
async def get_application_prefill(request: Request, offer_id: int) -> ApplicationPrefill:
    """Valeurs proposées pour « Marquer comme envoyée »."""
    async with _runtime(request).sessionmaker() as session:
        offer = await session.get(Offer, offer_id)
        letter = await current_draft(session, offer_id)
    if offer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "offre introuvable")
    # Coordonnées de l'employeur relevées par l'IA dans l'annonce, pendant la rédaction.
    employer = (letter.content.get("employer") if letter else None) or {}
    return ApplicationPrefill(
        offer_id=offer.id,
        sent_at=_today(),
        # Adresse connue de l'offre (annonce, registre, saisie), sinon celle relevée par l'IA.
        company_address=offer.company_address or employer.get("address"),
        contact_name=employer.get("contact_name"),
        contact_phone=employer.get("contact_phone"),
        company=offer.company or "Entreprise non indiquée",
        job_title=offer.title,
        location=offer.location,
        rate_text=_rate_text(offer),
    )


@router.get("/applications", operation_id="listApplications")
async def list_applications(
    request: Request,
    month: Annotated[str | None, Query(pattern=r"^\d{4}-\d{2}$")] = None,
) -> list[ApplicationOut]:
    query = select(Application).order_by(Application.sent_at.desc(), Application.id.desc())
    if month:
        query = query.where(Application.orp_month == month)
    async with _runtime(request).sessionmaker() as session:
        return [ApplicationOut.model_validate(a) for a in await session.scalars(query)]


@router.get("/applications/summary", operation_id="getApplicationsSummary")
async def get_applications_summary(
    request: Request,
    month: Annotated[str | None, Query(pattern=r"^\d{4}-\d{2}$")] = None,
) -> MonthSummary:
    month = month or _today().strftime("%Y-%m")
    async with _runtime(request).sessionmaker() as session:
        count = await session.scalar(
            select(func.count()).select_from(Application).where(Application.orp_month == month)
        )
        target = await session.scalar(
            select(Setting.value).where(Setting.key == "orp_monthly_target")
        )
    return MonthSummary(month=month, count=count or 0, target=int(target) if target else None)


@router.post(
    "/applications",
    operation_id="createApplication",
    status_code=status.HTTP_201_CREATED,
    responses={409: {"description": "Candidature déjà enregistrée pour cette offre"}},
)
async def create_application(request: Request, body: ApplicationIn) -> ApplicationOut:
    async with _runtime(request).sessionmaker.begin() as session:
        if body.offer_id is not None:
            offer = await session.get(Offer, body.offer_id)
            if offer is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "offre introuvable")
            existing = await session.scalar(
                select(Application.id).where(Application.offer_id == body.offer_id)
            )
            if existing:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    "une candidature est déjà enregistrée pour cette offre",
                )
            offer.status = OfferStatus.APPLIED
            letter = await current_draft(session, body.offer_id, DraftKind.LETTER)
            cv = await current_draft(session, body.offer_id, DraftKind.CV)
        else:
            letter = cv = None
        application = Application(
            **body.model_dump(),
            orp_month=body.sent_at.strftime("%Y-%m"),
            letter_draft_id=letter.id if letter else None,
            cv_draft_id=cv.id if cv else None,
        )
        session.add(application)
        await mark_changed(session, {application.orp_month})
        await session.flush()
        await session.refresh(application)
        out = ApplicationOut.model_validate(application)
    log.info("application_created", application_id=out.id, offer_id=out.offer_id)
    return out


@router.put("/applications/{application_id}", operation_id="updateApplication")
async def update_application(
    request: Request, application_id: int, body: ApplicationUpdate
) -> ApplicationOut:
    async with _runtime(request).sessionmaker.begin() as session:
        application = await session.get(Application, application_id)
        if application is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "candidature introuvable")
        before = application.orp_month
        values = body.model_dump()
        if values["status"] != application.status and values["status_at"] is None:
            values["status_at"] = _today()
        for key, value in values.items():
            setattr(application, key, value)
        application.orp_month = body.sent_at.strftime("%Y-%m")
        await mark_changed(session, {before, application.orp_month})
        await session.flush()
        await session.refresh(application)
        return ApplicationOut.model_validate(application)


@router.delete(
    "/applications/{application_id}",
    operation_id="deleteApplication",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_application(request: Request, application_id: int) -> None:
    """Annule une candidature enregistrée par erreur ; l'offre revient « en préparation »."""
    async with _runtime(request).sessionmaker.begin() as session:
        application = await session.get(Application, application_id)
        if application is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "candidature introuvable")
        if application.offer_id is not None:
            offer = await session.get(Offer, application.offer_id)
            if offer is not None:
                offer.status = OfferStatus.PREPARING
        await mark_changed(session, {application.orp_month})
        await session.delete(application)


# --- Coordonnées ----------------------------------------------------------------------


class Identity(BaseModel):
    name: ShortText | None = None
    street: ShortText | None = None
    # NPA suisse : quatre chiffres.
    postcode: Annotated[str, Field(max_length=20)] | None = None
    city: ShortText | None = None
    phone: ShortText | None = None
    email: ShortText | None = None

    @field_validator("name", "street", "postcode", "city", "phone", "email")
    @classmethod
    def _strip(cls, value: str | None) -> str | None:
        return _clean(value)

    @field_validator("postcode")
    @classmethod
    def _postcode(cls, value: str | None) -> str | None:
        if value is not None and not (len(value) == 4 and value.isdigit()):
            raise ValueError("NPA attendu : quatre chiffres")
        return value


@router.get("/identity", operation_id="getIdentity")
async def get_identity(request: Request) -> Identity:
    async with _runtime(request).sessionmaker() as session:
        identity = await load_identity(session)
    return Identity(**asdict(identity))


@router.put("/identity", operation_id="saveIdentity")
async def put_identity(request: Request, body: Identity) -> Identity:
    async with _runtime(request).sessionmaker.begin() as session:
        for field, key in IDENTITY_KEYS.items():
            value = getattr(body, field)
            await session.execute(
                insert(Setting)
                .values(key=key, value=value)
                .on_conflict_do_update(index_elements=["key"], set_={"value": value})
            )
    return body
