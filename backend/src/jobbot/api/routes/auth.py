"""Connexion (docs/18 §1) ; comptes invités par l'exploitant (docs/65 §2), pas d'inscription."""

from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from jobbot import accounts, welcome
from jobbot.auth import links, passwords, service
from jobbot.auth.middleware import cookie_token, session_cookie
from jobbot.db.models import User
from jobbot.log import get_logger
from jobbot.profiles.service import main_profile
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api/auth", tags=["auth"])
log = get_logger(__name__)
throttle = service.Throttle()
# Empreinte de référence : un identifiant inconnu coûte le même temps qu'un mot de passe faux.
_DUMMY_HASH = passwords.hash_password("identifiant-inconnu")


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


def _headers(request: Request) -> dict[str, str]:
    return {k.lower(): v for k, v in request.headers.items()}


async def _ensure_profile(runtime: Runtime, user_id: int) -> None:
    """Le profil principal du compte, créé à sa première connexion (docs/65), à son nom."""
    with accounts.use(user_id):
        async with runtime.sessionmaker.begin() as session:
            await main_profile(session)


def _current(request: Request) -> service.Authenticated | None:
    found: service.Authenticated | None = getattr(request.state, "user", None)
    return found


class Me(BaseModel):
    authenticated: bool
    username: str | None
    # Aucun compte créé : la page de connexion explique la commande à lancer.
    setup_needed: bool
    # false seulement pour un essai local (JOBBOT_AUTH_ENABLED=false).
    auth_enabled: bool
    # L'exploitant (le premier compte) : la rubrique Plateforme des Réglages (docs/65 §5).
    is_owner: bool = False
    # L'accueil après la première connexion (docs/66) : à faire, remis à plus tard, fait.
    welcome: Literal["pending", "postponed", "done"] = "done"


class LoginIn(BaseModel):
    username: Annotated[str, Field(min_length=1, max_length=80)]
    password: Annotated[str, Field(min_length=1, max_length=200)]


@router.get("/me", operation_id="getMe")
async def me(request: Request) -> Me:
    runtime = _runtime(request)
    async with runtime.sessionmaker() as session:
        # Le compte créé d'office (docs/65) n'a pas de mot de passe : il reste à configurer.
        users = (
            await session.scalar(
                select(func.count())
                .select_from(User)
                .where(User.password_hash != accounts.UNUSABLE_PASSWORD)
            )
            or 0
        )
        owner = await accounts.owner_id(session)
        found = _current(request)
        welcome_status = (
            welcome.status(await welcome.state(session)) if found is not None else "done"
        )
    if not runtime.settings.auth_enabled:
        return Me(
            authenticated=True, username=None, setup_needed=False, auth_enabled=False, is_owner=True
        )
    found = _current(request)
    return Me(
        authenticated=found is not None,
        username=found.username if found else None,
        setup_needed=users == 0,
        auth_enabled=True,
        is_owner=found is not None and found.user_id == owner,
        welcome=welcome_status,
    )


@router.post(
    "/login",
    operation_id="login",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"description": "Identifiant ou mot de passe incorrect"},
        409: {"description": "Aucun compte : lancer jobbot set-password"},
        429: {"description": "Trop d'essais : attendre"},
    },
)
async def login(request: Request, body: LoginIn, response: Response) -> None:
    runtime = _runtime(request)
    ip = request.client.host if request.client else "inconnue"
    username = body.username.strip()
    keys = (f"ip:{ip}", f"user:{username.casefold()}")
    wait = throttle.wait(*keys)
    if wait:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"trop d'essais : réessaie dans {wait} s",
            headers={"Retry-After": str(wait)},
        )
    async with runtime.sessionmaker.begin() as session:
        if not await session.scalar(
            select(func.count())
            .select_from(User)
            .where(User.password_hash != accounts.UNUSABLE_PASSWORD)
        ):
            raise HTTPException(
                status.HTTP_409_CONFLICT, "aucun compte : lance « jobbot set-password »"
            )
        user = await session.scalar(
            select(User).where(func.lower(User.username) == username.lower())
        )
        valid = passwords.verify_password(
            body.password, user.password_hash if user else _DUMMY_HASH
        )
        if user is not None and valid and user.suspended_at is not None:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "compte suspendu : vois avec l'exploitant de la plateforme",
            )
        if user is None or not valid:
            throttle.fail(*keys)
            # Jamais le mot de passe dans les journaux.
            log.warning("login_failed", username=username[:80], ip=ip)
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED, "identifiant ou mot de passe incorrect"
            )
        token = await service.create_session(session, user.id, request.headers.get("user-agent"))
        user.last_login_at = func.now()
        user_id = user.id
    await _ensure_profile(runtime, user_id)
    throttle.reset(*keys)
    log.info("login_succeeded", username=user.username, ip=ip)
    response.headers["set-cookie"] = session_cookie(token, _headers(request))


@router.post("/logout", operation_id="logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response) -> None:
    async with _runtime(request).sessionmaker.begin() as session:
        await service.end_session(session, cookie_token(_headers(request)))
    response.headers["set-cookie"] = session_cookie("", _headers(request), clear=True)


@router.post(
    "/logout-all",
    operation_id="logoutAll",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={401: {"description": "Connexion requise"}},
)
async def logout_all(request: Request, response: Response) -> None:
    """« Se déconnecter partout » : ferme toutes les sessions du compte, celle-ci comprise."""
    found = _current(request)
    if found is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "connexion requise")
    async with _runtime(request).sessionmaker.begin() as session:
        await service.end_all_sessions(session, found.user_id)
    response.headers["set-cookie"] = session_cookie("", _headers(request), clear=True)


# --- Liens d'invitation et de réinitialisation (docs/65 §2) -------------------------------


class LinkOut(BaseModel):
    kind: Literal["invite", "reset"]
    # Réinitialisation : le compte concerné ; invitation : rien, l'identifiant est à choisir.
    username: str | None
    expires_at: datetime


class LinkUse(BaseModel):
    username: Annotated[str | None, Field(max_length=links.USERNAME_MAX)] = None
    password: Annotated[str, Field(min_length=1, max_length=200)]


_LINK_STATUS = {
    "unknown": status.HTTP_404_NOT_FOUND,
    "gone": status.HTTP_410_GONE,
    "invalid": status.HTTP_422_UNPROCESSABLE_CONTENT,
}


def _link_error(exc: links.LinkError) -> HTTPException:
    return HTTPException(_LINK_STATUS[exc.reason], str(exc))


@router.get(
    "/links/{token}",
    operation_id="getAccountLink",
    responses={404: {"description": "Lien inconnu"}, 410: {"description": "Utilisé ou expiré"}},
)
async def get_link(request: Request, token: str) -> LinkOut:
    async with _runtime(request).sessionmaker() as session:
        try:
            link, user = await links.find(session, token)
        except links.LinkError as exc:
            raise _link_error(exc) from None
    return LinkOut(
        kind="reset" if link.kind == "reset" else "invite",
        username=user.username if user else None,
        expires_at=link.expires_at,
    )


@router.post(
    "/links/{token}",
    operation_id="useAccountLink",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Lien inconnu"},
        410: {"description": "Utilisé ou expiré"},
        422: {"description": "Identifiant ou mot de passe refusé"},
    },
)
async def use_link(request: Request, token: str, body: LinkUse, response: Response) -> None:
    """Crée le compte ou change le mot de passe, puis ouvre la session."""
    runtime = _runtime(request)
    async with runtime.sessionmaker.begin() as session:
        try:
            user = await links.use(session, token, body.username, body.password)
        except links.LinkError as exc:
            raise _link_error(exc) from None
        cookie = await service.create_session(session, user.id, request.headers.get("user-agent"))
        user.last_login_at = func.now()
        username, user_id = user.username, user.id
    await _ensure_profile(runtime, user_id)
    log.info("account_link_used", username=username)
    response.headers["set-cookie"] = session_cookie(cookie, _headers(request))
