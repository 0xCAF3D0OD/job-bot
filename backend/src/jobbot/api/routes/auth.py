"""Connexion (docs/18 §1) : un seul compte, créé par `jobbot set-password`, pas d'inscription."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from jobbot.auth import passwords, service
from jobbot.auth.middleware import cookie_token, session_cookie
from jobbot.db.models import User
from jobbot.log import get_logger
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


class LoginIn(BaseModel):
    username: Annotated[str, Field(min_length=1, max_length=80)]
    password: Annotated[str, Field(min_length=1, max_length=200)]


@router.get("/me", operation_id="getMe")
async def me(request: Request) -> Me:
    runtime = _runtime(request)
    async with runtime.sessionmaker() as session:
        users = await session.scalar(select(func.count()).select_from(User)) or 0
    if not runtime.settings.auth_enabled:
        return Me(authenticated=True, username=None, setup_needed=False, auth_enabled=False)
    found = _current(request)
    return Me(
        authenticated=found is not None,
        username=found.username if found else None,
        setup_needed=users == 0,
        auth_enabled=True,
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
        if not await session.scalar(select(func.count()).select_from(User)):
            raise HTTPException(
                status.HTTP_409_CONFLICT, "aucun compte : lance « jobbot set-password »"
            )
        user = await session.scalar(
            select(User).where(func.lower(User.username) == username.lower())
        )
        valid = passwords.verify_password(
            body.password, user.password_hash if user else _DUMMY_HASH
        )
        if user is None or not valid:
            throttle.fail(*keys)
            # Jamais le mot de passe dans les journaux.
            log.warning("login_failed", username=username[:80], ip=ip)
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED, "identifiant ou mot de passe incorrect"
            )
        token = await service.create_session(session, user.id, request.headers.get("user-agent"))
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
