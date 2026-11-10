"""Documents déposés et blocs de profil (docs/04-profil-prerequis.md §5).

Les noms de fichiers et les contenus sont personnels : ils ne sont jamais journalisés,
seuls l'identifiant et la taille le sont.
"""

import hashlib
import uuid
from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, File, HTTPException, Request, Response, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from jobbot import accounts
from jobbot.core.extract import (
    CONTENT_TYPES,
    MAX_SIZE,
    DocumentType,
    TextStatus,
    UnsupportedDocument,
    extract,
)
from jobbot.db.models import ChunkKind, Document, ProfileChunk
from jobbot.llm import proposals
from jobbot.log import get_logger
from jobbot.profile import reading
from jobbot.runtime import Runtime
from jobbot.worker.queue import enqueue
from jobbot.worker.tasks.cv_read import CV_READ_JOB
from jobbot.worker.tasks.score import SCORE_JOB

router = APIRouter(prefix="/api", tags=["profile"])
log = get_logger(__name__)


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    doc_type: DocumentType
    size: int
    text_status: TextStatus
    uploaded_at: datetime
    chunk_count: int = 0
    # « certificate » : un certificat de travail (docs/87).
    kind: str | None = None
    # La lecture du CV (PR 21) : NULL (jamais demandée), « reading », « done », « unavailable »,
    # « unreadable ». `read_at` : fin de la dernière lecture ; pour un CV lu avant, la date du
    # premier élément repris de lui. `found` : les éléments proposés encore à choisir, par sorte.
    read_state: str | None = None
    read_at: datetime | None = None
    found: dict[str, int] | None = None


def _document_out(
    document: Document, chunk_count: int, first_chunk: datetime | None
) -> DocumentOut:
    result = document.read_result if isinstance(document.read_result, list) else None
    found: dict[str, int] | None = None
    if result is not None:
        found = {}
        for item in result:
            if isinstance(item, dict) and item.get("duplicate_of") is None:
                kind = str(item.get("kind"))
                found[kind] = found.get(kind, 0) + 1
    return DocumentOut.model_validate(document).model_copy(
        update={
            "chunk_count": chunk_count,
            "read_state": reading.state_of(document),
            "read_at": document.read_at or (first_chunk if chunk_count else None),
            "found": found,
        }
    )


class DocumentText(BaseModel):
    id: int
    text_status: TextStatus
    text: str


class ChunkIn(BaseModel):
    kind: ChunkKind
    title: Annotated[str, Field(min_length=1, max_length=200)]
    content: Annotated[str, Field(min_length=1, max_length=20_000)]
    tags: list[Annotated[str, Field(min_length=1, max_length=40)]] = Field(
        default_factory=list, max_length=20
    )
    active: bool = True
    document_id: int | None = None

    @field_validator("title", "content")
    @classmethod
    def _strip(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("ne doit pas être vide")
        return stripped

    @field_validator("tags")
    @classmethod
    def _tags(cls, values: list[str]) -> list[str]:
        seen: dict[str, str] = {}
        for value in values:
            tag = value.strip()
            if tag:
                seen.setdefault(tag.casefold(), tag)
        return list(seen.values())


class ChunkOut(ChunkIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    # « correction » : ajouté en corrigeant une note (docs/114).
    origin: str | None = None


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


# --- Documents ------------------------------------------------------------------------


@router.get("/documents", operation_id="listDocuments")
async def list_documents(request: Request) -> list[DocumentOut]:
    async with _runtime(request).sessionmaker() as session:
        documents = list(
            await session.scalars(select(Document).order_by(Document.uploaded_at.desc()))
        )
        rows = (
            await session.execute(
                select(
                    ProfileChunk.document_id,
                    func.count(),
                    func.min(ProfileChunk.created_at),
                ).group_by(ProfileChunk.document_id)
            )
        ).all()
    counts = {row[0]: (int(row[1]), row[2]) for row in rows if row[0] is not None}
    return [_document_out(d, *counts.get(d.id, (0, None))) for d in documents]


@router.post(
    "/documents",
    operation_id="uploadDocument",
    status_code=status.HTTP_201_CREATED,
    responses={
        200: {"description": "Document déjà déposé : le même, remis en tête", "model": DocumentOut},
        409: {"description": "Document déjà déposé"},
        415: {"description": "Refusé"},
    },
)
async def upload_document(
    request: Request, response: Response, file: Annotated[UploadFile, File()]
) -> DocumentOut:
    runtime = _runtime(request)
    data = await file.read(MAX_SIZE + 1)
    filename = (file.filename or "document").rsplit("/", 1)[-1][:200]
    try:
        extracted = extract(filename, data)
    except UnsupportedDocument as exc:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, str(exc)) from None

    digest = hashlib.sha256(data).hexdigest()
    # Le même fichier redéposé (test du 10 novembre) : plus de refus. Le document existant revient,
    # remis en tête avec son texte relu, pour que la lecture du CV reparte (un CV déposé quand la
    # lecture échouait n'était jamais relu). Rien n'est copié dans le stockage. Lu sous la RLS
    # du compte en cours (C-5) : l'empreinte d'un autre compte n'est jamais trouvée.
    async with runtime.sessionmaker.begin() as session:
        existing = await session.scalar(select(Document).where(Document.sha256 == digest))
        if existing is not None:
            existing.filename = filename
            existing.text_status = extracted.status
            existing.extracted_text = extracted.text
            existing.uploaded_at = datetime.now(UTC)
            await session.flush()
            # Le nombre d'éléments repris dit à la page si ce CV a déjà été lu (PR 24).
            count, first = (
                await session.execute(
                    select(func.count(), func.min(ProfileChunk.created_at)).where(
                        ProfileChunk.document_id == existing.id
                    )
                )
            ).one()
            again = _document_out(existing, int(count), first)
    if existing is not None:
        response.status_code = status.HTTP_200_OK
        log.info("document_uploaded_again", document_id=again.id, text_status=again.text_status)
        return again
    # Un dossier par compte (docs/65 §1) ; les documents d'avant gardent leur emplacement.
    key = f"accounts/{accounts.current()}/documents/{uuid.uuid4().hex}.{extracted.type.value}"
    runtime.storage.put(key, data)
    try:
        async with runtime.sessionmaker.begin() as session:
            document = Document(
                filename=filename,
                doc_type=extracted.type,
                size=len(data),
                sha256=digest,
                storage_key=key,
                text_status=extracted.status,
                extracted_text=extracted.text,
            )
            session.add(document)
            await session.flush()
            out = DocumentOut.model_validate(document)
    except IntegrityError:
        runtime.storage.delete(key)
        raise HTTPException(status.HTTP_409_CONFLICT, "ce document est déjà déposé") from None
    log.info("document_uploaded", document_id=out.id, size=out.size, text_status=out.text_status)
    return out


async def _get_document(runtime: Runtime, document_id: int) -> Document:
    async with runtime.sessionmaker() as session:
        document = await session.get(Document, document_id)
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "document introuvable")
    return document


@router.get("/documents/{document_id}/text", operation_id="getDocumentText")
async def get_document_text(request: Request, document_id: int) -> DocumentText:
    document = await _get_document(_runtime(request), document_id)
    return DocumentText(
        id=document.id,
        text_status=TextStatus(document.text_status),
        text=document.extracted_text,
    )


@router.get(
    "/documents/{document_id}/file",
    operation_id="getDocumentFile",
    response_class=Response,
    responses={200: {"content": {"application/octet-stream": {}}}},
)
async def get_document_file(request: Request, document_id: int) -> Response:
    runtime = _runtime(request)
    document = await _get_document(runtime, document_id)
    doc_type = DocumentType(document.doc_type)
    # Un PDF s'affiche ; un texte déposé se télécharge, sans jamais être pris pour une page
    # (docs/78 §2).
    disposition = "inline" if doc_type is DocumentType.PDF else "attachment"
    return Response(
        runtime.storage.get(document.storage_key),
        media_type=CONTENT_TYPES[doc_type],
        headers={"Content-Disposition": disposition, "Cache-Control": "no-store"},
    )


@router.delete(
    "/documents/{document_id}",
    operation_id="deleteDocument",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(request: Request, document_id: int) -> None:
    """Supprime le fichier et son texte ; les blocs créés à partir de lui sont gardés."""
    runtime = _runtime(request)
    async with runtime.sessionmaker.begin() as session:
        document = await session.get(Document, document_id)
        if document is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "document introuvable")
        key = document.storage_key
        await session.delete(document)
    runtime.storage.delete(key)
    log.info("document_deleted", document_id=document_id)


# --- Propositions de blocs par l'IA (0.4.1) ---------------------------------------------


class ChunkProposal(BaseModel):
    kind: ChunkKind
    title: str
    content: str
    tags: list[str]
    # Bloc existant qui dit déjà la même chose, s'il y en a un.
    duplicate_of: int | None


async def _propose(
    request: Request, document_id: int, *, understand: bool = False
) -> tuple[list[ChunkProposal], str]:
    """L'IA lit le document : les blocs proposés, et la réponse brute (pour `understood`)."""
    try:
        found, text = await reading.propose(_runtime(request), document_id, understand=understand)
    except reading.ReadingFailed as exc:
        raise HTTPException(exc.status_code, exc.message) from None
    return [ChunkProposal(**p.model_dump()) for p in found], text


@router.post(
    "/documents/{document_id}/propose-chunks",
    operation_id="proposeChunks",
    responses={
        409: {"description": "IA non configurée, budget atteint ou compte API indisponible"},
        422: {"description": "Document sans texte lisible"},
        502: {"description": "Réponse de l'IA inutilisable"},
    },
)
async def propose_chunks(request: Request, document_id: int) -> list[ChunkProposal]:
    """L'IA lit le document et propose des blocs. Rien n'est enregistré : c'est l'interface
    qui crée les blocs que Kevin accepte."""
    chunks, _ = await _propose(request, document_id)
    return chunks


@router.post(
    "/documents/{document_id}/read",
    operation_id="startCvReading",
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_reading(request: Request, document_id: int) -> DocumentOut:
    """« Relire mon CV » (PR 21) : la lecture part sur le serveur et continue quand on quitte la
    page ; la cloche prévient à la fin. Le document est relu sous la RLS du compte (C-5)."""
    runtime = _runtime(request)
    async with runtime.sessionmaker.begin() as session:
        document = await session.get(Document, document_id)
        if document is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "document introuvable")
        readable = document.text_status == TextStatus.OK and document.extracted_text.strip()
        document.read_state = reading.READING if readable else reading.UNREADABLE
        document.read_started_at = datetime.now(UTC)
        document.read_result = None
        await session.flush()
        out = _document_out(document, 0, None)
    if readable:
        await enqueue(runtime.settings, CV_READ_JOB)
    log.info("cv_reading_requested", document_id=document_id, readable=bool(readable))
    return out


@router.get("/documents/{document_id}/read", operation_id="getCvReading")
async def get_reading(request: Request, document_id: int) -> list[ChunkProposal]:
    """Les éléments trouvés par la dernière lecture, à choisir (« Choisir les éléments »)."""
    document = await _get_document(_runtime(request), document_id)
    result = document.read_result if isinstance(document.read_result, list) else []
    return [ChunkProposal.model_validate(item) for item in result]


@router.delete(
    "/documents/{document_id}/read",
    operation_id="clearCvReading",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def clear_reading(request: Request, document_id: int) -> None:
    """Les éléments choisis (ou écartés) : la liste proposée n'est plus gardée."""
    async with _runtime(request).sessionmaker.begin() as session:
        document = await session.get(Document, document_id)
        if document is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "document introuvable")
        document.read_result = None


class Understanding(BaseModel):
    """Le CV lu à l'accueil (docs/121 §A) : les blocs proposés, et ce que le CV dit de la
    recherche (postes, taux, langues, télétravail), seulement s'il le dit."""

    chunks: list[ChunkProposal]
    roles: list[str]
    min_rate: int | None
    languages: list[str]
    remote: Literal["remote", "onsite"] | None


@router.post(
    "/documents/{document_id}/understand",
    operation_id="understandCv",
    responses={
        409: {"description": "IA non configurée, budget atteint ou compte API indisponible"},
        422: {"description": "Document sans texte lisible"},
        502: {"description": "Réponse de l'IA inutilisable"},
    },
)
async def understand_cv(request: Request, document_id: int) -> Understanding:
    """Rien n'est enregistré : l'accueil montre ce qui a été compris, la personne valide."""
    chunks, text = await _propose(request, document_id, understand=True)
    found = proposals.parse_understood(text)
    return Understanding(chunks=chunks, **found.model_dump())


# --- Blocs de profil ------------------------------------------------------------------


async def _check_document(runtime: Runtime, document_id: int | None) -> None:
    if document_id is not None:
        await _get_document(runtime, document_id)


@router.get("/profile-chunks", operation_id="listProfileChunks")
async def list_chunks(request: Request) -> list[ChunkOut]:
    async with _runtime(request).sessionmaker() as session:
        rows = await session.scalars(
            select(ProfileChunk).order_by(ProfileChunk.kind, ProfileChunk.created_at)
        )
        return [ChunkOut.model_validate(row) for row in rows]


@router.post(
    "/profile-chunks", operation_id="createProfileChunk", status_code=status.HTTP_201_CREATED
)
async def create_chunk(request: Request, body: ChunkIn) -> ChunkOut:
    runtime = _runtime(request)
    await _check_document(runtime, body.document_id)
    async with runtime.sessionmaker.begin() as session:
        was_empty = body.active and not await session.scalar(
            select(ProfileChunk.id).where(ProfileChunk.active.is_(True)).limit(1)
        )
        chunk = ProfileChunk(**body.model_dump())
        session.add(chunk)
        await session.flush()
        await session.refresh(chunk)
        out = ChunkOut.model_validate(chunk)
    # Premier élément du profil (PR 17, « Compléter mon profil ») : les offres restées sans note
    # faute de profil sont notées tout de suite, sans attendre la relève des 10 minutes.
    if was_empty and runtime.settings.llm_configured:
        await enqueue(runtime.settings, SCORE_JOB)
    return out


@router.put("/profile-chunks/{chunk_id}", operation_id="updateProfileChunk")
async def update_chunk(request: Request, chunk_id: int, body: ChunkIn) -> ChunkOut:
    runtime = _runtime(request)
    await _check_document(runtime, body.document_id)
    async with runtime.sessionmaker.begin() as session:
        chunk = await session.get(ProfileChunk, chunk_id)
        if chunk is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "bloc introuvable")
        for key, value in body.model_dump().items():
            setattr(chunk, key, value)
        await session.flush()
        await session.refresh(chunk)
        return ChunkOut.model_validate(chunk)


@router.delete(
    "/profile-chunks/{chunk_id}",
    operation_id="deleteProfileChunk",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_chunk(request: Request, chunk_id: int) -> None:
    async with _runtime(request).sessionmaker.begin() as session:
        chunk = await session.get(ProfileChunk, chunk_id)
        if chunk is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "bloc introuvable")
        await session.delete(chunk)
