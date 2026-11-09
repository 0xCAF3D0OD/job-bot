"""Extension du navigateur (docs/25, docs/70) : routes appelées par l'extension, et ses jetons.

`/api/extension/…` : réservé à l'extension, avec son jeton (`Authorization: Bearer …`,
vérifié par le middleware). `/api/extension-tokens` : gestion des jetons depuis les
Réglages, avec la session habituelle.
"""

from datetime import UTC, date, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select

from jobbot import accounts, manual_offers
from jobbot.alerts import service as alert_service
from jobbot.api.routes import applications as application_routes
from jobbot.api.routes import cvs as cv_routes
from jobbot.api.routes import letters as letter_routes
from jobbot.api.routes.orp import application_data
from jobbot.auth.service import Window
from jobbot.core.orp import job_room_fill, shift_month
from jobbot.db.models import AlertSearch, Application, DraftKind, ExtensionToken, Offer, Site
from jobbot.extension import announce, service
from jobbot.followups.service import local_today
from jobbot.letters.service import current_draft, load_identity
from jobbot.log import get_logger
from jobbot.mail import addresses, site_codes
from jobbot.runtime import Runtime
from jobbot.sources.sites import followed

log = get_logger(__name__)

router = APIRouter(prefix="/api/extension", tags=["extension"])
tokens_router = APIRouter(prefix="/api/extension-tokens", tags=["extension"])


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


# --- Pour l'extension ---------------------------------------------------------------------


class ExtensionMe(BaseModel):
    platform: str
    version: str
    # Ce que cette plateforme sait faire avec l'extension (docs/71 §5) : l'extension, mise à
    # jour par la boutique, peut être plus récente que la plateforme.
    features: list[str]


# Formulaires des employeurs (docs/25), Job-Room (docs/70).
# Les codes des sites (docs/112) : l'extension remplit le code de vérification.
# Envoyer une annonce (docs/142 §3).
# Le formulaire d'alerte des sites (docs/142 §4).
FEATURES = ["forms", "job-room", "codes", "announce", "alerts"]


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
    return ExtensionMe(
        platform="jobA1", version=_runtime(request).settings.version, features=FEATURES
    )


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


# --- Job-Room (docs/70) --------------------------------------------------------------------


class JobRoomItem(BaseModel):
    id: int
    company: str
    job_title: str
    sent_at: date
    orp_month: str


class JobRoomList(BaseModel):
    """Les candidatures à déclarer : du mois précédent et du mois en cours, les plus anciennes
    d'abord."""

    items: list[JobRoomItem]


class JobRoomFillOut(BaseModel):
    date: str
    channel: str
    company: str
    street: str
    number: str
    po_box: str
    postcode_city: str
    contact: str
    email: str
    phone: str
    job_title: str
    url: str
    assigned: bool
    rate: str
    interview: bool
    result: str


async def _to_declare(request: Request) -> JobRoomList:
    since = shift_month(f"{local_today():%Y-%m}", -1)
    async with _runtime(request).sessionmaker() as session:
        rows = await session.scalars(
            select(Application)
            .where(Application.job_room_at.is_(None), Application.orp_month >= since)
            .order_by(Application.sent_at, Application.id)
        )
        return JobRoomList(
            items=[
                JobRoomItem(
                    id=a.id,
                    company=a.company,
                    job_title=a.job_title,
                    sent_at=a.sent_at,
                    orp_month=a.orp_month,
                )
                for a in rows
            ]
        )


@router.get("/job-room", operation_id="extensionJobRoomList")
async def job_room_list(request: Request) -> JobRoomList:
    return await _to_declare(request)


@router.get("/applications/{application_id}/job-room", operation_id="extensionJobRoomFill")
async def job_room_values(request: Request, application_id: int) -> JobRoomFillOut:
    async with _runtime(request).sessionmaker() as session:
        application = await session.get(Application, application_id)
        if application is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "candidature introuvable")
        values = job_room_fill(application_data(application))
    return JobRoomFillOut(**values.__dict__)


@router.put("/applications/{application_id}/job-room", operation_id="extensionJobRoomDeclared")
async def job_room_declared(request: Request, application_id: int) -> JobRoomList:
    """« C'est déclaré » : renvoie celles qui restent, pour proposer la suivante."""
    async with _runtime(request).sessionmaker.begin() as session:
        await application_routes.declare_in_job_room(session, application_id, True)
    return await _to_declare(request)


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
    # « Relier ce navigateur » : à lire par l'extension dans les 2 minutes (docs/76 §1).
    link: bool = False


def _token_out(row: ExtensionToken) -> TokenOut:
    return TokenOut(
        id=row.id, name=row.name, created_at=row.created_at, last_used_at=row.last_used_at
    )


@tokens_router.get("", operation_id="listExtensionTokens")
async def list_tokens(request: Request) -> list[TokenOut]:
    async with _runtime(request).sessionmaker() as session:
        rows = await session.scalars(
            select(ExtensionToken).where(service.usable()).order_by(ExtensionToken.id.desc())
        )
        return [_token_out(r) for r in rows]


@tokens_router.post("", operation_id="createExtensionToken", status_code=status.HTTP_201_CREATED)
async def create_token(request: Request, body: TokenIn) -> TokenCreated:
    async with _runtime(request).sessionmaker.begin() as session:
        row, token = await service.create_token(
            session, body.name.strip() or "Mon navigateur", link=body.link
        )
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


# --- Les codes des sites (docs/112) -----------------------------------------------------------


class ExtensionCode(BaseModel):
    site: str
    code: str
    received_at: datetime


class ExtensionCodeOut(BaseModel):
    # Vide : pas encore arrivé (l'extension redemande quelques secondes plus tard).
    code: ExtensionCode | None


@router.post("/codes/expect", operation_id="extensionExpectCode")
async def extension_expect_code(request: Request) -> ExtensionCodeOut:
    """La page d'un site demande un code : le relevé rapide de la boîte commence."""
    await site_codes.expect(_runtime(request))
    return ExtensionCodeOut(code=None)


@router.get("/codes", operation_id="extensionCode")
async def extension_code(
    request: Request, site: Annotated[str, Query(pattern=r"^[a-z0-9]{2,30}$")]
) -> ExtensionCodeOut:
    """Le code de ce site reçu il y a moins de 10 minutes, pour ce compte."""
    found = await site_codes.latest(_runtime(request), site)
    if found is None:
        return ExtensionCodeOut(code=None)
    return ExtensionCodeOut(
        code=ExtensionCode(site=found.site, code=found.code, received_at=found.received_at)
    )


# --- Envoyer une annonce (docs/142 §3) ----------------------------------------------------

# 30 envois par jour et par compte (en mémoire, comme les autres limites de auth.service).
ANNOUNCE_LIMIT = 30
announce_window = Window(limit=ANNOUNCE_LIMIT, period_s=24 * 3600)


class AnnounceIn(BaseModel):
    """Seulement l'annonce : son adresse, le balisage JobPosting s'il existe, et son texte
    (la description du JobPosting, sinon le texte principal de la page)."""

    url: Annotated[str, Field(min_length=8, max_length=2000)]
    title: Annotated[str, Field(max_length=300)] | None = None
    company: Annotated[str, Field(max_length=300)] | None = None
    location: Annotated[str, Field(max_length=300)] | None = None
    text: Annotated[str, Field(min_length=1, max_length=manual_offers.MAX_TEXT * 2)]
    # La réponse à « C'est bien cette offre ? » : « fill » (avec l'id montré) ou « new ».
    choice: Literal["fill", "new"] | None = None
    offer_id: int | None = None

    @field_validator("url")
    @classmethod
    def _https(cls, value: str) -> str:
        value = value.strip()
        if not value.startswith(("https://", "http://")):
            raise ValueError("adresse de page web attendue")
        return value


class KnownOffer(BaseModel):
    id: int
    title: str
    company: str | None
    received_at: datetime
    # Le site de l'alerte qui l'a apportée (« jobs.ch »), s'il y en a une.
    site: str | None


class AnnounceOut(BaseModel):
    # « filled » : l'offre déjà là est complétée ; « added » : nouvelle offre ;
    # « confirm » : même poste chez la même entreprise, à confirmer.
    outcome: Literal["filled", "added", "confirm"]
    offer_id: int | None = None
    score: int | None = None
    # Les mots de la note (« Proche »).
    label: str | None = None
    filled: list[str] = []
    known: KnownOffer | None = None


@router.post(
    "/announce",
    operation_id="extensionAnnounce",
    responses={
        409: {"description": "L'offre à compléter n'est pas celle trouvée"},
        422: {"description": "Pas d'annonce lisible"},
        429: {"description": "30 envois par jour au plus"},
    },
)
async def announce_offer(request: Request, body: AnnounceIn) -> AnnounceOut:
    """« Envoyer à jobA1 » : compléter l'offre de ce lien, demander pour le même poste chez la
    même entreprise, sinon ajouter l'offre ; puis la renoter. Le texte n'est jamais journalisé."""
    key = f"announce:{accounts.current()}"
    # La réponse à « C'est bien cette offre ? » ne compte pas comme un nouvel envoi.
    if body.choice is None and announce_window.take(key):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"{ANNOUNCE_LIMIT} annonces envoyées aujourd'hui : c'est le maximum. Réessaie demain.",
        )
    page = announce.Page(
        url=body.url, text=body.text, title=body.title, company=body.company, location=body.location
    )
    try:
        sent = await announce.send(_runtime(request), page, body.choice, body.offer_id)
    except announce.ChoiceMismatch:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "ce n'est plus la même offre : renvoie l'annonce"
        ) from None
    except announce.SendProblem as exc:
        code = (
            status.HTTP_429_TOO_MANY_REQUESTS
            if exc.limit
            else status.HTTP_422_UNPROCESSABLE_CONTENT
        )
        raise HTTPException(code, exc.message) from None
    known = sent.known
    return AnnounceOut(
        outcome=sent.outcome,
        offer_id=sent.offer_id,
        score=sent.score,
        label=sent.label,
        filled=sent.filled,
        known=KnownOffer(
            id=known.id,
            title=known.title,
            company=known.company,
            received_at=known.received_at,
            site=known.site,
        )
        if known
        else None,
    )


# --- Le formulaire « Créer une alerte » des sites (docs/142 §4) ------------------------------

# Les sites dont l'extension remplit le formulaire d'alerte.
ALERT_SITES = ("jobup", "jobsch", "linkedin")


class AlertAddressOut(BaseModel):
    # L'adresse jobA1 à donner aux sites (None : pas de boîte configurée).
    address: str | None
    # Les recherches suivies qui n'ont pas encore d'alerte, par site.
    todo: dict[str, int]


class AlertCreatedOut(BaseModel):
    site: str
    # Les recherches marquées « créée » sur ce site.
    marked: int


@router.get("/alerts", operation_id="extensionAlertAddress")
async def alert_address(request: Request) -> AlertAddressOut:
    """L'adresse jobA1 du compte, à mettre dans le champ e-mail du formulaire d'alerte."""
    runtime = _runtime(request)
    async with runtime.sessionmaker.begin() as session:
        address = await addresses.account_address(session, runtime.settings)
        sites = list(
            await session.scalars(select(Site).where(followed(), Site.slug.in_(ALERT_SITES)))
        )
        todo = dict.fromkeys((s.slug for s in sites), 0)
        for search in await session.scalars(
            select(AlertSearch).where(AlertSearch.active.is_(True))
        ):
            for cell in await alert_service.cells(session, search, sites):
                if cell.status == "todo":
                    todo[cell.site] += 1
    return AlertAddressOut(address=address, todo=todo)


@router.put(
    "/alerts/{site}",
    operation_id="extensionAlertCreated",
    responses={404: {"description": "Site inconnu"}},
)
async def alert_created(request: Request, site: str) -> AlertCreatedOut:
    """« J'ai créé l'alerte » depuis l'extension : comme le bouton de l'assistant des alertes
    (`alerts.service.mark_created`), pour les recherches suivies encore à faire sur ce site."""
    if site not in ALERT_SITES:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "site inconnu")
    async with _runtime(request).sessionmaker.begin() as session:
        searches = list(
            await session.scalars(select(AlertSearch.id).where(AlertSearch.active.is_(True)))
        )
        try:
            marked = await alert_service.mark_created(session, searches, site)
        except alert_service.UnknownSite:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "site inconnu") from None
    if marked:
        # Comme le bouton de l'assistant : le relevé rapide (docs/144).
        await site_codes.expect(_runtime(request))
    log.info("extension_alert_created", site=site, searches=len(marked))
    return AlertCreatedOut(site=site, marked=len(marked))
