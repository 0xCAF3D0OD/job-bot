"""Lettre de motivation : rédaction par l'IA, versions, relecture, export Word (docs/08 §3).

Les coordonnées de Kevin ne partent jamais vers l'IA : elles sont ajoutées par
`letters.document.assemble`, à l'affichage comme dans le Word.
"""

from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Literal
from urllib.parse import quote
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.api.routes import writing
from jobbot.db.models import Application, Draft, DraftKind, Offer
from jobbot.letters.document import Identity, LetterDocument, Recipient, assemble, to_docx
from jobbot.letters.service import load_identity
from jobbot.llm import letter as letter_llm
from jobbot.llm.scoring import InvalidScore
from jobbot.log import get_logger
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api", tags=["letters"])
log = get_logger(__name__)
LOCAL_TZ = ZoneInfo("Europe/Zurich")
# Estimation prudente d'une rédaction (docs/08 §6), pour ne pas dépasser le plafond.
LETTER_ESTIMATE_USD = Decimal("0.10")
Language = Literal["fr", "en", "de"]
DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


class LetterParagraph(BaseModel):
    text: Annotated[str, Field(min_length=1, max_length=4000)]
    chunk_ids: list[int] = Field(default_factory=list)


class EmployerOut(BaseModel):
    address: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None


class LetterDocumentOut(BaseModel):
    """La lettre telle qu'elle sera envoyée, en-tête compris."""

    model_config = ConfigDict(from_attributes=True)

    language: Language
    sender: list[str]
    place_date: str
    recipient: list[str]
    subject_line: str
    salutation: str
    paragraphs: list[str]
    closing: str
    signature: str
    enclosure: str
    # Coordonnées manquantes dans les Réglages (en-tête incomplet).
    missing_identity: list[str]


class LetterOut(BaseModel):
    id: int
    offer_id: int
    version: int
    language: Language
    subject: str
    paragraphs: list[LetterParagraph]
    employer: EmployerOut
    instruction: str | None
    model: str | None
    created_at: datetime
    edited_at: datetime | None
    document: LetterDocumentOut


class LetterRequest(BaseModel):
    # None : langue de l'annonce.
    language: Language | None = None
    # Consigne pour une nouvelle version (« plus court », « insiste sur Kubernetes »).
    instruction: Annotated[str, Field(max_length=500)] | None = None
    # Version à retravailler ; par défaut la plus récente.
    base_draft_id: int | None = None


class LetterEdit(BaseModel):
    subject: Annotated[str, Field(min_length=1, max_length=200)]
    paragraphs: list[LetterParagraph] = Field(min_length=1, max_length=10)
    language: Language | None = None


async def _recipient(session: AsyncSession, offer: Offer, draft: Draft) -> Recipient:
    """La candidature enregistrée fait foi ; sinon l'offre et ce que l'IA a relevé."""
    application = await session.scalar(select(Application).where(Application.offer_id == offer.id))
    if application is not None:
        return Recipient(application.company, application.company_address, application.contact_name)
    employer = draft.content.get("employer") or {}
    return Recipient(offer.company, employer.get("address"), employer.get("contact_name"))


def _document(identity: Identity, recipient: Recipient, draft: Draft) -> LetterDocument:
    day = (draft.edited_at or draft.created_at).astimezone(LOCAL_TZ).date()
    return assemble(
        identity,
        recipient,
        draft.language,
        draft.content["subject"],
        [p["text"] for p in draft.content["paragraphs"]],
        day,
    )


def _out(draft: Draft, document: LetterDocument) -> LetterOut:
    return LetterOut(
        id=draft.id,
        offer_id=draft.offer_id,
        version=draft.version,
        language=draft.language,
        subject=draft.content["subject"],
        paragraphs=[LetterParagraph(**p) for p in draft.content["paragraphs"]],
        employer=EmployerOut(**(draft.content.get("employer") or {})),
        instruction=draft.instruction,
        model=draft.model,
        created_at=draft.created_at,
        edited_at=draft.edited_at,
        document=LetterDocumentOut(**asdict(document)),
    )


async def _render(session: AsyncSession, draft: Draft) -> LetterOut:
    offer = await session.get(Offer, draft.offer_id)
    assert offer is not None  # suppression en cascade
    identity = await load_identity(session)
    return _out(draft, _document(identity, await _recipient(session, offer, draft), draft))


async def _get_draft(session: AsyncSession, draft_id: int) -> Draft:
    return await writing.get_draft(session, draft_id, DraftKind.LETTER)


@router.get("/offers/{offer_id}/letters", operation_id="listLetters")
async def list_letters(request: Request, offer_id: int) -> list[LetterOut]:
    """Toutes les versions, la plus récente d'abord."""
    async with _runtime(request).sessionmaker() as session:
        if await session.get(Offer, offer_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "offre introuvable")
        drafts = await session.scalars(
            select(Draft)
            .where(Draft.offer_id == offer_id, Draft.kind == DraftKind.LETTER)
            .order_by(Draft.version.desc())
        )
        return [await _render(session, d) for d in drafts]


@router.post(
    "/offers/{offer_id}/letters",
    operation_id="writeLetter",
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {
            "description": "IA non configurée, profil vide, budget atteint ou compte indisponible"
        },
        502: {"description": "Réponse de l'IA inutilisable"},
        503: {"description": "IA momentanément indisponible"},
    },
)
async def write_letter(request: Request, offer_id: int, body: LetterRequest) -> LetterOut:
    """L'IA rédige une nouvelle version (quelques dizaines de secondes)."""
    runtime = _runtime(request)
    settings = runtime.settings
    instruction = (body.instruction or "").strip() or None
    ctx = await writing.prepare(
        runtime,
        offer_id,
        DraftKind.LETTER,
        base_draft_id=body.base_draft_id,
        instruction=instruction,
        estimate_usd=LETTER_ESTIMATE_USD,
    )
    params = letter_llm.request_params(
        settings.llm_model,
        settings.llm_writing_effort,
        ctx.chunks,
        ctx.offer,
        language=body.language,
        assessment=ctx.assessment,
        previous=ctx.previous,
        instruction=instruction,
    )
    raw = await writing.call(
        runtime, params, offer_id=offer_id, kind=DraftKind.LETTER, rate=ctx.rate
    )
    try:
        output = letter_llm.parse_output(raw.text, ctx.chunks)
    except InvalidScore:
        raise writing.unusable() from None

    async with runtime.sessionmaker.begin() as session:
        draft = await writing.add_version(
            session,
            offer_id,
            DraftKind.LETTER,
            language=output.language,
            content=output.model_dump(exclude={"language"}),
            instruction=instruction,
            model=raw.model,
            prompt_version=letter_llm.PROMPT_VERSION,
        )
        out = await _render(session, draft)
    log.info("letter_written", offer_id=offer_id, version=out.version, language=out.language)
    return out


@router.put("/letters/{draft_id}", operation_id="editLetter")
async def edit_letter(request: Request, draft_id: int, body: LetterEdit) -> LetterOut:
    """Corrections de Kevin : la version modifiée devient celle qui compte."""
    async with _runtime(request).sessionmaker.begin() as session:
        draft = await _get_draft(session, draft_id)
        draft.content = {
            **draft.content,
            "subject": body.subject.strip(),
            "paragraphs": [
                {"text": p.text.strip(), "chunk_ids": p.chunk_ids}
                for p in body.paragraphs
                if p.text.strip()
            ],
        }
        if body.language:
            draft.language = body.language
        draft.edited_at = datetime.now(UTC)
        await session.flush()
        await session.refresh(draft)
        return await _render(session, draft)


@router.get(
    "/letters/{draft_id}/docx",
    operation_id="downloadLetterDocx",
    response_class=Response,
    responses={200: {"content": {DOCX_TYPE: {}}}},
)
async def download_letter_docx(request: Request, draft_id: int) -> Response:
    async with _runtime(request).sessionmaker() as session:
        draft = await _get_draft(session, draft_id)
        offer = await session.get(Offer, draft.offer_id)
        assert offer is not None
        document = _document(
            await load_identity(session), await _recipient(session, offer, draft), draft
        )
    company = "".join(c for c in (offer.company or "employeur") if c.isalnum() or c in " -")
    filename = f"Lettre - {company.strip()[:60]}.docx"
    return Response(
        to_docx(document),
        media_type=DOCX_TYPE,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )
