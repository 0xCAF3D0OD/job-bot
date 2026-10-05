"""Documents déposés et blocs de profil (docs/04-profil-prerequis.md §5).

Les noms de fichiers et les contenus sont personnels : ils ne sont jamais journalisés,
seuls l'identifiant et la taille le sont.
"""

import hashlib
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Request, Response, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from jobbot.core.extract import (
    CONTENT_TYPES,
    MAX_SIZE,
    DocumentType,
    TextStatus,
    UnsupportedDocument,
    extract,
)
from jobbot.db.models import ChunkKind, Document, ProfileChunk
from jobbot.log import get_logger
from jobbot.runtime import Runtime

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
        chunks = list(await session.scalars(select(ProfileChunk.document_id)))
    counts = {doc_id: chunks.count(doc_id) for doc_id in {d.id for d in documents}}
    return [
        DocumentOut.model_validate(d).model_copy(update={"chunk_count": counts.get(d.id, 0)})
        for d in documents
    ]


@router.post(
    "/documents",
    operation_id="uploadDocument",
    status_code=status.HTTP_201_CREATED,
    responses={409: {"description": "Document déjà déposé"}, 415: {"description": "Refusé"}},
)
async def upload_document(request: Request, file: Annotated[UploadFile, File()]) -> DocumentOut:
    runtime = _runtime(request)
    data = await file.read(MAX_SIZE + 1)
    filename = (file.filename or "document").rsplit("/", 1)[-1][:200]
    try:
        extracted = extract(filename, data)
    except UnsupportedDocument as exc:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, str(exc)) from None

    digest = hashlib.sha256(data).hexdigest()
    key = f"documents/{uuid.uuid4().hex}.{extracted.type.value}"
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
    return Response(
        runtime.storage.get(document.storage_key),
        media_type=CONTENT_TYPES[DocumentType(document.doc_type)],
        headers={"Content-Disposition": "inline", "Cache-Control": "no-store"},
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
        chunk = ProfileChunk(**body.model_dump())
        session.add(chunk)
        await session.flush()
        await session.refresh(chunk)
        return ChunkOut.model_validate(chunk)


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
