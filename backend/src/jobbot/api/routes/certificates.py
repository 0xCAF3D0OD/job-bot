"""Les certificats de travail, décodés (docs/87) : marquer un document, lire sans IA, puis en
détail avec l'IA sur demande."""

from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from jobbot.certificates import formulas, service
from jobbot.db.models import CertificateReading, Document
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api", tags=["certificates"])

AdviceKey = Literal["attach", "on_request", "correct"]


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


class KindIn(BaseModel):
    kind: Literal["certificate"] | None


class PassageOut(BaseModel):
    text: str
    meaning: str
    tone: Literal["good", "neutral", "bad"]
    category: str
    level: int | None = None


class NoteOut(BaseModel):
    text: str
    tone: Literal["good", "neutral", "bad"]


class AiReadingOut(BaseModel):
    grade: int | None
    explanation: str
    missing: list[str]
    order: str | None
    advice: AdviceKey
    advice_text: str


class CertificateOut(BaseModel):
    document_id: int
    filename: str
    # Pas de texte lisible (PDF scanné) : rien n'a pu être lu.
    readable: bool
    language: str | None
    grade: int | None
    grade_label: str | None
    explanation: str
    advice: AdviceKey
    advice_label: str
    passages: list[PassageOut]
    notes: list[NoteOut]
    ai: AiReadingOut | None
    ai_at: datetime | None


class CertificatesPage(BaseModel):
    certificates: list[CertificateOut]
    # « Joins A et B. Pour C, demande d'abord une correction. »
    summary: str | None


def _label(filename: str) -> str:
    return filename.rsplit(".", 1)[0]


def _summary(items: list[CertificateOut]) -> str | None:
    if not items:
        return None
    groups: dict[str, list[str]] = {"attach": [], "on_request": [], "correct": []}
    for item in items:
        groups[item.advice].append(f"« {_label(item.filename)} »")

    def join(names: list[str]) -> str:
        return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " et " + names[-1]

    parts = []
    if groups["attach"]:
        parts.append(f"Joins {join(groups['attach'])}.")
    if groups["correct"]:
        parts.append(f"Pour {join(groups['correct'])}, demande d'abord une correction.")
    if groups["on_request"]:
        parts.append(f"{join(groups['on_request'])} : seulement si on te le demande.")
    return " ".join(parts)


async def _page(runtime: Runtime) -> CertificatesPage:
    async with runtime.sessionmaker.begin() as session:
        documents = list(
            await session.scalars(
                select(Document)
                .where(Document.kind == service.CERTIFICATE)
                .order_by(Document.uploaded_at.desc())
            )
        )
        readings = {
            r.document_id: r
            for r in await session.scalars(select(CertificateReading))
            if r.rules_version == formulas.VERSION
        }
        items: list[CertificateOut] = []
        for document in documents:
            reading = readings.get(document.id) or await service.save(session, document)
            local = service.read(document.extracted_text or "")
            ai = AiReadingOut(**reading.ai) if isinstance(reading.ai, dict) else None
            grade = ai.grade if ai and ai.grade else reading.grade
            items.append(
                CertificateOut(
                    document_id=document.id,
                    filename=document.filename,
                    readable=bool((document.extracted_text or "").strip()),
                    language=reading.language,
                    grade=grade,
                    grade_label=service.GRADES.get(grade) if grade else None,
                    explanation=ai.explanation if ai and ai.explanation else service.explain(local),
                    advice=reading.advice,
                    advice_label=service.ADVICE[reading.advice],
                    passages=[PassageOut(**p) for p in reading.passages],
                    notes=[NoteOut(**n) for n in reading.notes],
                    ai=ai,
                    ai_at=reading.ai_at,
                )
            )
    return CertificatesPage(certificates=items, summary=_summary(items))


@router.get("/certificates", operation_id="listCertificates")
async def list_certificates(request: Request) -> CertificatesPage:
    return await _page(_runtime(request))


@router.put(
    "/documents/{document_id}/kind",
    operation_id="setDocumentKind",
    responses={404: {"description": "Document introuvable"}},
)
async def set_document_kind(request: Request, document_id: int, body: KindIn) -> CertificatesPage:
    """Marquer un document comme certificat de travail (il est lu aussitôt, sans IA), ou non."""
    runtime = _runtime(request)
    async with runtime.sessionmaker.begin() as session:
        document = await session.get(Document, document_id)
        if document is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "document introuvable")
        document.kind = body.kind
        if body.kind == service.CERTIFICATE:
            await service.save(session, document)
        else:
            found = await session.scalar(
                select(CertificateReading).where(CertificateReading.document_id == document_id)
            )
            if found is not None:
                await session.delete(found)
    return await _page(runtime)


@router.post(
    "/certificates/{document_id}/lecture",
    operation_id="readCertificate",
    responses={409: {"description": "IA indisponible, plafond atteint, ou texte illisible"}},
)
async def read_certificate(
    request: Request, document_id: Annotated[int, Field(ge=1)]
) -> CertificatesPage:
    """La lecture détaillée par l'IA (environ 0,03 CHF), gardée avec le certificat."""
    runtime = _runtime(request)
    try:
        await service.read_with_ai(runtime, document_id)
    except service.ReadingUnavailable as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from None
    return await _page(runtime)
