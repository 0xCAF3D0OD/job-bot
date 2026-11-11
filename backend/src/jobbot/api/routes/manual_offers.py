"""Ajouter une offre trouvée ailleurs (docs/111) : lire l'annonce, puis l'ajouter.

La lecture ne crée rien : elle rend une fiche à relire. L'ajout crée l'offre, qui passe par
le filtre et la note comme une offre reçue. Dans la démo, le garde des écritures refuse les
deux (docs/72).
"""

import asyncio
from typing import Annotated, Any, Literal

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select

from jobbot import accounts, manual_offers
from jobbot.auth.service import Window
from jobbot.db.models import Evaluation, Offer
from jobbot.log import get_logger
from jobbot.runtime import Runtime

log = get_logger(__name__)

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
    # Le contrat lu sur la page, sinon vide : « Non précisé » à l'écran.
    contract: str | None = None
    read_by: Literal["page", "ia"]
    trade: str | None
    matches_trade: bool
    existing_offer_id: int | None
    # Les champs vides de l'offre déjà là que cette annonce peut remplir.
    fillable: list[Literal["company", "location", "description", "url"]] = []


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
    contract: Annotated[str, Field(max_length=100)] | None = None
    read_by: Literal["page", "ia", "main"] = "main"
    # Déjà là : compléter ses champs vides avec cette fiche, sans rien remplacer.
    fill: bool = False

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
    # Les champs de l'offre déjà là remplis par cette fiche.
    filled: list[str] = []


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
            contract=draft.contract,
            read_by="ia" if draft.read_by == "ia" else "page",
            trade=draft.trade,
            matches_trade=draft.matches_trade,
            existing_offer_id=draft.existing_offer_id,
            fillable=draft.fillable,
        )
    )


class ManualPdfOut(BaseModel):
    # Le texte du PDF, à relire dans le champ comme un texte collé ; sinon ce qui l'a empêché.
    text: str | None = None
    # « no-text » : un scan, sans texte ; « too-big » : plus de 5 Mo ; « not-pdf » ; « unreadable ».
    problem: Literal["no-text", "too-big", "not-pdf", "unreadable"] | None = None


# « Importer le PDF de l'annonce » : 20 fichiers par heure et par compte (en mémoire, comme les
# autres limites de auth.service).
pdf_per_account = Window(limit=20, period_s=3600)
PDF_RESPONSES: dict[int | str, dict[str, Any]] = {
    429: {"description": "Trop de fichiers : « Réessaie dans n minutes »"},
}


@router.post("/pdf", operation_id="readManualOfferPdf", responses=PDF_RESPONSES)
async def read_pdf(request: Request, file: Annotated[UploadFile, File()]) -> ManualPdfOut:
    """Le texte du PDF d'une annonce (paquet du 11 novembre, PR 38). Lu sur le serveur, sans IA ;
    le fichier n'est ni rangé ni journalisé (E-5, J-1) : seul son texte revient à la personne,
    qui le relit avant « Ajouter l'offre ». Rien n'est créé ici."""
    account = f"compte-{accounts.current()}"
    if wait := pdf_per_account.take(account):
        minutes = max(1, -(-wait // 60))
        word = "minute" if minutes == 1 else "minutes"
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, f"Réessaie dans {minutes} {word}.")
    data = await file.read(manual_offers.MAX_PDF_BYTES + 1)
    try:
        text = await asyncio.to_thread(manual_offers.pdf_text, data)
    except manual_offers.ReadProblem as exc:
        log.info("manual_offer_pdf_refused", reason=exc.reason, size=len(data))
        return ManualPdfOut(problem=exc.reason)
    log.info("manual_offer_pdf_read", size=len(data), chars=len(text))
    return ManualPdfOut(text=text)


@router.post("", operation_id="addManualOffer", status_code=status.HTTP_201_CREATED)
async def add(request: Request, body: ManualAddIn) -> ManualAddOut:
    runtime = _runtime(request)
    draft = manual_offers.Draft(
        title=body.title,
        company=body.company,
        location=body.location,
        description=(body.description or "").strip() or None,
        url=body.url,
        contract=(body.contract or "").strip() or None,
        read_by=body.read_by,
    )
    filled: list[str] = []
    async with runtime.sessionmaker() as session:
        existing = (await manual_offers._complete(session, draft)).existing_offer_id
    if existing is None:
        try:
            offer_id = await manual_offers.add(runtime, draft)
        except manual_offers.ReadProblem as exc:
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, exc.message) from exc
    else:
        offer_id = existing
        if body.fill:
            filled = await manual_offers.fill(runtime, existing, draft)
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
            filled=filled,
        )
