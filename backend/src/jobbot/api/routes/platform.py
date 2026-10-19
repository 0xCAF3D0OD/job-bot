"""Plateforme (docs/65 §2, §4, §5) : les comptes et les réglages de l'installation.

Réservé à l'exploitant. Il voit de chaque compte son usage (connexion, dépense de l'IA,
offres reçues ce mois), jamais ses données ; il invite, réinitialise, suspend, supprime.
"""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select, text, update

from jobbot import accounts, backup, platform
from jobbot.api.owner import require_owner
from jobbot.auth import links
from jobbot.auth.service import end_all_sessions
from jobbot.db.base import connected_as_admin
from jobbot.db.models import AccountLink, CalendarToken, ExtensionToken, User
from jobbot.log import get_logger
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api/platform", tags=["platform"])
log = get_logger(__name__)


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


class AccountOut(BaseModel):
    id: int
    username: str
    is_owner: bool
    created_at: datetime
    last_login_at: datetime | None
    suspended: bool
    # Compte créé d'office, sans mot de passe : `jobbot set-password` lui en donne un.
    has_password: bool
    ai_budget_chf: Decimal
    month_spend_chf: Decimal
    month_offers: int


class InvitationOut(BaseModel):
    id: int
    created_at: datetime
    expires_at: datetime


class BackupOut(BaseModel):
    """Les sauvegardes (docs/82) : réglées ou non, la dernière, le dernier essai."""

    configured: bool
    folder: str
    count: int
    last_at: datetime | None
    last_size: int | None
    last_error: str | None
    test_at: datetime | None
    test_ok: bool | None
    test_error: str | None
    # Dernière réussie il y a plus de 36 heures, ou dernière en échec : en rouge.
    late: bool


class PlatformOut(BaseModel):
    accounts: list[AccountOut]
    invitations: list[InvitationOut]
    ai_total_budget_chf: Decimal
    ai_month_spend_chf: Decimal
    auth_enabled: bool
    # L'API se connecte à la base en administrateur (docs/78 §3.1) : à corriger dans les réglages.
    database_admin: bool = False
    backup: BackupOut | None = None


class LinkCreated(BaseModel):
    """Le jeton n'est montré qu'une fois : l'adresse est à transmettre par toi-même."""

    id: int
    token: str
    expires_at: datetime


class AccountChange(BaseModel):
    suspended: bool | None = None
    ai_budget_chf: Annotated[Decimal | None, Field(ge=0, le=1000)] = None


class PlatformSettingsIn(BaseModel):
    ai_total_budget_chf: Annotated[Decimal, Field(ge=0, le=10000)]


def _month_start() -> datetime:
    return datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)


@router.get("", operation_id="getPlatform", responses={403: {"description": "Exploitant seul"}})
async def get_platform(request: Request) -> PlatformOut:
    runtime = _runtime(request)
    await require_owner(runtime)
    start = _month_start()
    async with runtime.sessionmaker() as session:
        owner = await accounts.owner_id(session)
        users = list(await session.scalars(select(User).order_by(User.id)))
        usage = {
            int(row.user_id): row
            for row in await session.execute(
                text("select user_id, spend_chf, offers from account_usage(:start)"),
                {"start": start},
            )
        }
        invitations = list(
            await session.scalars(
                select(AccountLink)
                .where(
                    AccountLink.kind == "invite",
                    AccountLink.used_at.is_(None),
                    AccountLink.expires_at > func.now(),
                )
                .order_by(AccountLink.created_at)
            )
        )
        # Celui de l'exploitant est le sien, dans ses Réglages (rubrique IA).
        own_cap = await session.scalar(
            text("select value from settings where key = 'llm_monthly_budget_chf'")
        )
        total = await platform.total_ai_budget(session)
        spend = await session.scalar(select(func.platform_month_spend(start))) or 0
        database_admin = await connected_as_admin(session)
        saved_status = await platform.get(session, backup.STATUS_KEY, {})
    return PlatformOut(
        accounts=[
            AccountOut(
                id=u.id,
                username=u.username,
                is_owner=u.id == owner,
                created_at=u.created_at,
                last_login_at=u.last_login_at,
                suspended=u.suspended_at is not None,
                has_password=u.password_hash != accounts.UNUSABLE_PASSWORD,
                ai_budget_chf=(
                    Decimal(str(own_cap if own_cap is not None else 10))
                    if u.id == owner
                    else u.ai_budget_chf
                    if u.ai_budget_chf is not None
                    else platform.ACCOUNT_AI_BUDGET_CHF
                ),
                month_spend_chf=Decimal(str(usage[u.id].spend_chf)).quantize(Decimal("0.01"))
                if u.id in usage
                else Decimal("0.00"),
                month_offers=int(usage[u.id].offers) if u.id in usage else 0,
            )
            for u in users
        ],
        invitations=[
            InvitationOut(id=i.id, created_at=i.created_at, expires_at=i.expires_at)
            for i in invitations
        ],
        ai_total_budget_chf=total,
        ai_month_spend_chf=Decimal(str(spend)).quantize(Decimal("0.01")),
        auth_enabled=runtime.settings.auth_enabled,
        database_admin=database_admin,
        backup=_backup(runtime, saved_status if isinstance(saved_status, dict) else {}),
    )


def _backup(runtime: Runtime, status: dict[str, object]) -> BackupOut:
    settings = runtime.settings

    def when(key: str) -> datetime | None:
        value = status.get(key)
        return datetime.fromisoformat(value) if isinstance(value, str) else None

    size = status.get("last_size")
    ok = status.get("test_ok")
    error, test_error = status.get("last_error"), status.get("test_error")
    return BackupOut(
        configured=settings.backup_configured,
        folder=str(settings.backup_path),
        count=len(backup.saved(settings)),
        last_at=when("last_at"),
        last_size=size if isinstance(size, int) else None,
        last_error=error if isinstance(error, str) else None,
        test_at=when("test_at"),
        test_ok=ok if isinstance(ok, bool) else None,
        test_error=test_error if isinstance(test_error, str) else None,
        late=settings.backup_configured and backup.late(status, datetime.now(UTC)),
    )


@router.post(
    "/invitations",
    operation_id="createInvitation",
    status_code=status.HTTP_201_CREATED,
    responses={403: {"description": "Exploitant seul"}},
)
async def create_invitation(request: Request) -> LinkCreated:
    runtime = _runtime(request)
    await require_owner(runtime)
    async with runtime.sessionmaker.begin() as session:
        created = await links.create(session, "invite")
    log.info("invitation_created", link_id=created.link.id)
    return LinkCreated(id=created.link.id, token=created.token, expires_at=created.link.expires_at)


@router.delete(
    "/invitations/{link_id}",
    operation_id="deleteInvitation",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={403: {"description": "Exploitant seul"}},
)
async def delete_invitation(request: Request, link_id: int) -> None:
    runtime = _runtime(request)
    await require_owner(runtime)
    async with runtime.sessionmaker.begin() as session:
        await session.execute(
            delete(AccountLink).where(AccountLink.id == link_id, AccountLink.kind == "invite")
        )


async def _other_account(runtime: Runtime, account_id: int) -> None:
    """Un compte qui existe, et pas celui de l'exploitant (il ne se suspend ni ne se supprime)."""
    async with runtime.sessionmaker() as session:
        if await session.get(User, account_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "compte introuvable")
        if account_id == await accounts.owner_id(session):
            raise HTTPException(
                status.HTTP_409_CONFLICT, "le compte de l'exploitant : jobbot set-password"
            )


@router.post(
    "/accounts/{account_id}/reset",
    operation_id="createResetLink",
    status_code=status.HTTP_201_CREATED,
    responses={403: {"description": "Exploitant seul"}, 404: {"description": "Compte"}},
)
async def create_reset(request: Request, account_id: int) -> LinkCreated:
    runtime = _runtime(request)
    await require_owner(runtime)
    await _other_account(runtime, account_id)
    async with runtime.sessionmaker.begin() as session:
        created = await links.create(session, "reset", account_id)
    log.info("reset_link_created", account=account_id)
    return LinkCreated(id=created.link.id, token=created.token, expires_at=created.link.expires_at)


@router.patch(
    "/accounts/{account_id}",
    operation_id="updateAccount",
    responses={403: {"description": "Exploitant seul"}, 404: {"description": "Compte"}},
)
async def update_account(request: Request, account_id: int, body: AccountChange) -> PlatformOut:
    runtime = _runtime(request)
    await require_owner(runtime)
    await _other_account(runtime, account_id)
    async with runtime.sessionmaker.begin() as session:
        user = await session.get_one(User, account_id)
        if body.suspended is not None:
            user.suspended_at = datetime.now(UTC) if body.suspended else None
            if body.suspended:
                await end_all_sessions(session, account_id)
        if "ai_budget_chf" in body.model_fields_set:
            user.ai_budget_chf = body.ai_budget_chf
    if body.suspended:
        # Ses jetons d'extension et d'agenda aussi (docs/78 §2), révoqués en son nom : ses
        # lignes ne sont visibles que de lui.
        with accounts.use(account_id):
            async with runtime.sessionmaker.begin() as session:
                for model in (ExtensionToken, CalendarToken):
                    await session.execute(
                        update(model)
                        .where(model.revoked_at.is_(None))
                        .values(revoked_at=func.now())
                    )
    log.info("account_updated", account=account_id, suspended=body.suspended)
    return await get_platform(request)


@router.delete(
    "/accounts/{account_id}",
    operation_id="deleteAccount",
    responses={403: {"description": "Exploitant seul"}, 404: {"description": "Compte"}},
)
async def delete_account(request: Request, account_id: int) -> PlatformOut:
    """Le compte et toutes ses données, fichiers compris : rien n'est gardé."""
    runtime = _runtime(request)
    await require_owner(runtime)
    await _other_account(runtime, account_id)
    async with runtime.sessionmaker.begin() as session:
        await session.execute(delete(User).where(User.id == account_id))
    runtime.storage.delete_folder(f"accounts/{account_id}")
    log.info("account_deleted", account=account_id)
    return await get_platform(request)


@router.put(
    "/settings",
    operation_id="savePlatformSettings",
    responses={403: {"description": "Exploitant seul"}},
)
async def save_platform_settings(request: Request, body: PlatformSettingsIn) -> PlatformOut:
    runtime = _runtime(request)
    await require_owner(runtime)
    async with runtime.sessionmaker.begin() as session:
        await platform.put(session, "ai_total_budget_chf", str(body.ai_total_budget_chf))
    return await get_platform(request)
