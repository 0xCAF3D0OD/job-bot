"""Tes données (docs/65 §6) : ce qui est gardé, l'export complet, la suppression du compte.

L'export rassemble tout ce qui appartient au compte : les lignes de chaque table rangée par
compte (la base ne rend que les siennes), ses documents déposés et les e-mails d'alerte reçus
pour lui. La suppression efface le compte, toutes ses lignes et son dossier de fichiers.
"""

import io
import json
import re
import zipfile
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select, text

from jobbot import accounts, platform
from jobbot.api.owner import require_owner
from jobbot.auth import passwords
from jobbot.auth.middleware import session_cookie
from jobbot.db.models import (
    Application,
    ChatConversation,
    Document,
    Notification,
    Offer,
    ProfileChunk,
    Search,
    User,
)
from jobbot.log import get_logger
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api", tags=["account"])
log = get_logger(__name__)

# Rien de ce qui sert à se connecter ou à joindre un service : empreintes de jetons.
LEFT_OUT = {"user_id", "token_hash"}
PRIVACY_KEY = "privacy_contact"


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


class DataSummary(BaseModel):
    offers: int
    applications: int
    documents: int
    profile_blocks: int
    alert_emails: int
    conversations: int
    notifications: int
    # Le compte de l'exploitant ne se supprime pas depuis la plateforme.
    can_delete: bool


class Privacy(BaseModel):
    """Les mentions de l'exploitant (responsable, contact, hébergeur), écrites par lui."""

    contact: str | None


class DeleteIn(BaseModel):
    password: Annotated[str, Field(min_length=1, max_length=200)]


class PrivacyIn(BaseModel):
    contact: Annotated[str, Field(max_length=4000)]


async def _count(session: Any, model: type) -> int:
    return int(await session.scalar(select(func.count()).select_from(model)) or 0)


@router.get("/account/data", operation_id="getAccountData")
async def get_data(request: Request) -> DataSummary:
    runtime = _runtime(request)
    async with runtime.sessionmaker() as session:
        owner = await accounts.is_owner(session)
        return DataSummary(
            offers=await _count(session, Offer),
            applications=await _count(session, Application),
            documents=await _count(session, Document),
            profile_blocks=await _count(session, ProfileChunk),
            alert_emails=await _count(session, Search),
            conversations=await _count(session, ChatConversation),
            notifications=await _count(session, Notification),
            can_delete=not owner and runtime.settings.auth_enabled,
        )


async def account_tables(session: Any) -> list[str]:
    """Les tables rangées par compte : celles qui ont `user_id` et la séparation."""
    rows = await session.scalars(
        text(
            "select c.relname from pg_class c join pg_attribute a on a.attrelid = c.oid "
            "where c.relrowsecurity and a.attname = 'user_id' and c.relkind = 'r' "
            "and c.relnamespace = 'public'::regnamespace order by 1"
        )
    )
    return [str(r) for r in rows]


def _safe(name: str) -> str:
    return re.sub(r"[^\w.\- ]+", "_", name).strip() or "fichier"


README = """Export de ton compte jobA1 (docs/65 §6)

data/<table>.json   tes données, table par table (offres, candidatures, profil, réglages…)
documents/          les documents que tu as déposés (CV, certificats)
emails/             les e-mails d'alerte reçus pour toi, tels quels

Rien d'autre n'est gardé sur toi. Les empreintes des jetons (agenda, extension) ne sont pas
reprises : elles ne servent qu'à les reconnaître.
"""


@router.get(
    "/account/export",
    operation_id="exportAccount",
    responses={200: {"content": {"application/zip": {}}, "description": "Archive ZIP"}},
)
async def export_account(request: Request) -> Response:
    runtime = _runtime(request)
    buffer = io.BytesIO()
    async with runtime.sessionmaker() as session:
        username = await session.scalar(select(User.username).where(User.id == accounts.current()))
        tables = await account_tables(session)
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("LISEZ-MOI.txt", README)
            for table in tables:
                rows = await session.scalar(
                    text(f"select coalesce(json_agg(t), '[]'::json) from {table} t")
                )
                cleaned = [
                    {k: v for k, v in row.items() if k not in LEFT_OUT} for row in rows or []
                ]
                archive.writestr(
                    f"data/{table}.json", json.dumps(cleaned, ensure_ascii=False, indent=1)
                )
            for document in await session.scalars(select(Document).order_by(Document.id)):
                if runtime.storage.exists(document.storage_key):
                    archive.writestr(
                        f"documents/{document.id}-{_safe(document.filename)}",
                        runtime.storage.get(document.storage_key),
                    )
            for search in await session.scalars(select(Search).order_by(Search.id)):
                if runtime.storage.exists(search.raw_key):
                    archive.writestr(f"emails/{search.id}.eml", runtime.storage.get(search.raw_key))
    day = datetime.now(UTC).strftime("%Y-%m-%d")
    name = f"jobA1-{_safe(username or 'compte')}-{day}.zip"
    log.info("account_exported", tables=len(tables))
    return Response(
        buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )


@router.post(
    "/account/delete",
    operation_id="deleteOwnAccount",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        403: {"description": "Mot de passe incorrect"},
        409: {"description": "Compte de l'exploitant"},
    },
)
async def delete_own_account(request: Request, body: DeleteIn, response: Response) -> None:
    """Le compte et toutes ses données, fichiers compris, après le mot de passe."""
    runtime = _runtime(request)
    account = accounts.current()
    async with runtime.sessionmaker() as session:
        if not runtime.settings.auth_enabled or await accounts.is_owner(session):
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "le compte de l'exploitant ne se supprime pas depuis la plateforme",
            )
        user = await session.get(User, account)
        if user is None or not passwords.verify_password(body.password, user.password_hash):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "mot de passe incorrect")
    async with runtime.sessionmaker.begin() as session:
        await session.execute(delete(User).where(User.id == account))
    runtime.storage.delete_folder(f"accounts/{account}")
    log.info("own_account_deleted", account=account)
    headers = {k.lower(): v for k, v in request.headers.items()}
    response.headers["set-cookie"] = session_cookie("", headers, clear=True)


@router.get("/privacy", operation_id="getPrivacy")
async def get_privacy(request: Request) -> Privacy:
    """Public : la page « Tes données » se lit avant même d'accepter une invitation."""
    async with _runtime(request).sessionmaker() as session:
        contact = await platform.get(session, PRIVACY_KEY)
    return Privacy(contact=str(contact) if contact else None)


@router.put(
    "/privacy",
    operation_id="savePrivacy",
    responses={403: {"description": "Exploitant seul"}},
)
async def save_privacy(request: Request, body: PrivacyIn) -> Privacy:
    runtime = _runtime(request)
    await require_owner(runtime)
    async with runtime.sessionmaker.begin() as session:
        await platform.put(session, PRIVACY_KEY, body.contact.strip())
    return await get_privacy(request)
