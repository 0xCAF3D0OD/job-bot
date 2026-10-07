"""CV adapté à une offre : sélection et ordre des blocs par l'IA, retouches, Word (docs/08 §4).

Comme pour la lettre, les coordonnées de Kevin sont ajoutées ici et jamais envoyées à l'IA.
"""

from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Literal
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.api.routes import writing
from jobbot.db.models import Draft, DraftKind, Offer
from jobbot.letters.cv_document import CvDocument, assemble_cv, cv_to_docx, section_of
from jobbot.letters.document import Identity
from jobbot.letters.pdf import cv_to_pdf
from jobbot.letters.service import load_identity
from jobbot.llm import cv as cv_llm
from jobbot.llm.scoring import InvalidScore, ProfileChunkData
from jobbot.log import get_logger
from jobbot.runtime import Runtime
from jobbot.scoring.service import active_profile

router = APIRouter(prefix="/api", tags=["cvs"])
log = get_logger(__name__)
# Estimation prudente (docs/08 §6) : moins de texte produit que pour la lettre.
CV_ESTIMATE_USD = Decimal("0.05")
DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
Language = Literal["fr", "en", "de"]
Section = Literal["experience", "competence", "formation", "langues"]


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


class SegmentOut(BaseModel):
    text: str
    strong: bool


class CvItemOut(BaseModel):
    chunk_id: int
    title: str | None
    content: list[SegmentOut]


class CvSectionOut(BaseModel):
    key: Section
    heading: str
    items: list[CvItemOut]


class CvDocumentOut(BaseModel):
    language: Language
    name: str
    headline: str
    contacts: list[str]
    summary_heading: str
    summary: str
    sections: list[CvSectionOut]
    missing_identity: list[str]


class CvBlock(BaseModel):
    """Un bloc de profil qui peut figurer dans le CV ; cochés d'abord, dans l'ordre du CV."""

    id: int
    title: str
    section: Section
    selected: bool


class CvOut(BaseModel):
    id: int
    offer_id: int
    version: int
    language: Language
    headline: str
    summary: str
    chunk_ids: list[int]
    keywords: list[str]
    instruction: str | None
    model: str | None
    created_at: datetime
    edited_at: datetime | None
    blocks: list[CvBlock]
    document: CvDocumentOut


class CvRequest(BaseModel):
    language: Language | None = None
    instruction: Annotated[str, Field(max_length=500)] | None = None
    base_draft_id: int | None = None


class CvEdit(BaseModel):
    headline: Annotated[str, Field(max_length=120)]
    summary: Annotated[str, Field(max_length=1500)]
    chunk_ids: list[int] = Field(min_length=1, max_length=40)
    keywords: list[Annotated[str, Field(max_length=60)]] | None = Field(default=None, max_length=30)


def _eligible(chunks: list[ProfileChunkData]) -> dict[int, ProfileChunkData]:
    return {c.id: c for c in chunks if c.kind in cv_llm.CV_KINDS}


def _document(draft: Draft, chunks: dict[int, ProfileChunkData], identity: Identity) -> CvDocument:
    content = draft.content
    return assemble_cv(
        identity,
        chunks,
        content["chunk_ids"],
        language=draft.language,
        headline=content.get("headline", ""),
        summary=content.get("summary", ""),
        keywords=content.get("keywords", []),
    )


async def _render(session: AsyncSession, draft: Draft) -> CvOut:
    chunks = _eligible(await active_profile(session))
    identity = await load_identity(session)
    selected = [i for i in draft.content["chunk_ids"] if i in chunks]
    rest = [c for c in chunks.values() if c.id not in selected]
    blocks = [
        CvBlock(id=c.id, title=c.title, section=section_of(c), selected=c.id in selected)
        for c in [chunks[i] for i in selected] + rest
    ]
    return CvOut(
        id=draft.id,
        offer_id=draft.offer_id,
        version=draft.version,
        language=draft.language,
        headline=draft.content.get("headline", ""),
        summary=draft.content.get("summary", ""),
        chunk_ids=selected,
        keywords=draft.content.get("keywords", []),
        instruction=draft.instruction,
        model=draft.model,
        created_at=draft.created_at,
        edited_at=draft.edited_at,
        blocks=blocks,
        document=CvDocumentOut.model_validate(asdict(_document(draft, chunks, identity))),
    )


@router.get("/offers/{offer_id}/cvs", operation_id="listCvs")
async def list_cvs(request: Request, offer_id: int) -> list[CvOut]:
    """Toutes les versions, la plus récente d'abord."""
    async with _runtime(request).sessionmaker() as session:
        if await session.get(Offer, offer_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "offre introuvable")
        drafts = await session.scalars(
            select(Draft)
            .where(Draft.offer_id == offer_id, Draft.kind == DraftKind.CV)
            .order_by(Draft.version.desc())
        )
        return [await _render(session, d) for d in drafts]


@router.post(
    "/offers/{offer_id}/cvs",
    operation_id="writeCv",
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {
            "description": "IA non configurée, profil vide, budget atteint ou compte indisponible"
        },
        502: {"description": "Réponse de l'IA inutilisable"},
        503: {"description": "IA momentanément indisponible"},
    },
)
async def write_cv(request: Request, offer_id: int, body: CvRequest) -> CvOut:
    """L'IA choisit et ordonne les blocs, et écrit le titre et le résumé."""
    runtime = _runtime(request)
    settings = runtime.settings
    instruction = (body.instruction or "").strip() or None
    ctx = await writing.prepare(
        runtime,
        offer_id,
        DraftKind.CV,
        base_draft_id=body.base_draft_id,
        instruction=instruction,
        estimate_usd=CV_ESTIMATE_USD,
    )
    params = cv_llm.request_params(
        settings.llm_model,
        settings.llm_writing_effort,
        ctx.chunks,
        ctx.offer,
        language=body.language,
        assessment=ctx.assessment,
        previous=ctx.previous,
        instruction=instruction,
    )
    raw = await writing.call(runtime, params, offer_id=offer_id, kind=DraftKind.CV, rate=ctx.rate)
    try:
        output = cv_llm.parse_output(raw.text, ctx.chunks)
    except InvalidScore:
        raise writing.unusable() from None

    async with runtime.sessionmaker.begin() as session:
        draft = await writing.add_version(
            session,
            offer_id,
            DraftKind.CV,
            language=output.language,
            content=output.model_dump(exclude={"language"}),
            instruction=instruction,
            model=raw.model,
            prompt_version=cv_llm.PROMPT_VERSION,
        )
        out = await _render(session, draft)
    log.info("cv_written", offer_id=offer_id, version=out.version, blocks=len(out.chunk_ids))
    return out


@router.put("/cvs/{draft_id}", operation_id="editCv")
async def edit_cv(request: Request, draft_id: int, body: CvEdit) -> CvOut:
    """Retouches de Kevin : blocs cochés et leur ordre, titre, résumé."""
    async with _runtime(request).sessionmaker.begin() as session:
        draft = await writing.get_draft(session, draft_id, DraftKind.CV)
        eligible = _eligible(await active_profile(session))
        ids = list(dict.fromkeys(i for i in body.chunk_ids if i in eligible))
        if not ids:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, "aucun bloc de profil valide coché"
            )
        draft.content = {
            **draft.content,
            "headline": body.headline.strip(),
            "summary": body.summary.strip(),
            "chunk_ids": ids,
            **(
                {"keywords": [k.strip() for k in body.keywords if k.strip()]}
                if body.keywords is not None
                else {}
            ),
        }
        draft.edited_at = datetime.now(UTC)
        await session.flush()
        await session.refresh(draft)
        return await _render(session, draft)


@router.get(
    "/cvs/{draft_id}/docx",
    operation_id="downloadCvDocx",
    response_class=Response,
    responses={200: {"content": {DOCX_TYPE: {}}}},
)
async def download_cv_docx(request: Request, draft_id: int) -> Response:
    async with _runtime(request).sessionmaker() as session:
        draft = await writing.get_draft(session, draft_id, DraftKind.CV)
        offer = await session.get(Offer, draft.offer_id)
        assert offer is not None
        chunks = _eligible(await active_profile(session))
        document = _document(draft, chunks, await load_identity(session))
    company = "".join(c for c in (offer.company or "employeur") if c.isalnum() or c in " -")
    filename = f"CV - {company.strip()[:60]}.docx"
    return Response(
        cv_to_docx(document),
        media_type=DOCX_TYPE,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


@router.get(
    "/cvs/{draft_id}/pdf",
    operation_id="downloadCvPdf",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
async def download_cv_pdf(request: Request, draft_id: int) -> Response:
    """Le même CV en PDF, à joindre aux formulaires en ligne (docs/25 §3.4)."""
    async with _runtime(request).sessionmaker() as session:
        draft = await writing.get_draft(session, draft_id, DraftKind.CV)
        offer = await session.get(Offer, draft.offer_id)
        assert offer is not None
        chunks = _eligible(await active_profile(session))
        document = _document(draft, chunks, await load_identity(session))
    company = "".join(c for c in (offer.company or "employeur") if c.isalnum() or c in " -")
    filename = f"CV - {company.strip()[:60]}.pdf"
    return Response(
        cv_to_pdf(document, title=filename[:-4]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )
