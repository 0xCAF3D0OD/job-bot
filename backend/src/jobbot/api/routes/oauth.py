"""Se connecter avec Google, Microsoft ou Apple (docs/65, complément du 2026-11-05).

- `GET /api/auth/providers` : les fournisseurs configurés ; la page de connexion n'affiche que
  leurs boutons.
- `GET /api/auth/oauth/{fournisseur}/start` : envoie chez le fournisseur (`?suite=` : la page où
  revenir ; `?lier=1` : lier à son compte, depuis Compte, Connexions).
- `GET|POST /api/auth/oauth/{fournisseur}/callback` : le retour (Apple répond par un formulaire,
  en POST). Le compte lié ouvre la session comme l'identifiant et le mot de passe.
- `GET|DELETE /api/account/connexions` : voir et retirer ses comptes liés, jamais le dernier
  moyen de se connecter.

Au retour, sans compte lié : un e-mail vérifié par Google ou Apple qui est déjà celui d'un compte
lié (vérifié lui aussi) lie ce compte ; sinon, demandes de compte ouvertes, une demande est
créée (docs/102 : elle attend l'exploitant) ; fermées, la connexion est refusée.

Journal : connexion réussie ou refusée, par fournisseur, avec le numéro du compte et la raison ;
jamais le jeton, le code, l'identifiant du fournisseur ni l'e-mail.
"""

import re
import unicodedata
from datetime import UTC, datetime
from typing import Annotated, Literal
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import func, null, select
from sqlalchemy.exc import IntegrityError

from jobbot import accounts, welcome
from jobbot.api.routes.auth import _ensure_profile, signup_limit
from jobbot.auth import oidc, service, signup
from jobbot.auth.links import USERNAME_MAX, LinkError, free_username
from jobbot.auth.middleware import secure_cookie, session_cookie
from jobbot.db.models import OauthLink, User
from jobbot.log import get_logger
from jobbot.notify import service as notify
from jobbot.runtime import Runtime

router = APIRouter(tags=["auth"])
log = get_logger(__name__)
# Au plus 30 départs par 10 minutes depuis une même adresse : la mémoire des parcours reste bornée.
start_limit = service.Window(limit=30, period_s=600)

Provider = Literal["apple", "google", "microsoft"]
LOGIN = "/connexion"
CONNECTIONS = "/reglages?rubrique=connexions"


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


def _headers(request: Request) -> dict[str, str]:
    return {k.lower(): v for k, v in request.headers.items()}


def _ip(request: Request) -> str:
    return request.client.host if request.client else "inconnue"


def http_client() -> httpx.AsyncClient:
    """Le client HTTP vers les fournisseurs (remplacé dans les tests). TLS vérifié (K-1)."""
    return httpx.AsyncClient()


class AuthProviders(BaseModel):
    providers: list[Provider]


@router.get("/api/auth/providers", operation_id="getAuthProviders")
async def providers(request: Request) -> AuthProviders:
    return AuthProviders(providers=_runtime(request).settings.oauth_providers)


def _next_path(value: str | None) -> str | None:
    # Seulement une page de la plateforme (pas d'adresse externe), comme la page de connexion.
    if value and value.startswith("/") and not value.startswith("//") and "\\" not in value:
        return value[:300]
    return None


def _flow_cookie(value: str, headers: dict[str, str], *, clear: bool = False) -> str:
    parts = [
        f"{oidc.FLOW_COOKIE}={'' if clear else value}",
        "Path=/api/auth/oauth",
        f"Max-Age={0 if clear else oidc.FLOW_TTL_S}",
        "HttpOnly",
    ]
    # Apple revient par un POST venu de son site : le cookie doit suivre (SameSite=None, donc
    # Secure). Sur la machine elle-même (http://localhost), Lax : Apple n'y renvoie jamais.
    parts += ["SameSite=None", "Secure"] if secure_cookie(headers) else ["SameSite=Lax"]
    return "; ".join(parts)


def _configured(request: Request, provider: str) -> None:
    if provider not in _runtime(request).settings.oauth_providers:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "fournisseur non configuré")


def _to(base: str, **params: str) -> str:
    """L'adresse de la page, avec ses paramètres (encodés)."""
    return f"{base}{'&' if '?' in base else '?'}{urlencode(params)}"


def _redirect(path: str, request: Request, cookies: list[str] | None = None) -> RedirectResponse:
    response = RedirectResponse(path, status_code=status.HTTP_303_SEE_OTHER)
    response.headers["cache-control"] = "no-store"
    response.headers.append("set-cookie", _flow_cookie("", _headers(request), clear=True))
    for cookie in cookies or []:
        response.headers.append("set-cookie", cookie)
    return response


def _refused(
    request: Request, provider: str, reason: str, *, link: bool = False, account: int | None = None
) -> RedirectResponse:
    log.warning(
        "oauth_login_refused" if not link else "oauth_link_refused",
        provider=provider,
        reason=reason,
        account=account,
        ip=_ip(request),
    )
    base = CONNECTIONS if link else LOGIN
    return _redirect(_to(base, erreur=reason, fournisseur=provider), request)


@router.get(
    "/api/auth/oauth/{provider}/start",
    operation_id="startOauth",
    status_code=status.HTTP_303_SEE_OTHER,
    responses={404: {"description": "Fournisseur non configuré"}},
)
async def start(
    request: Request, provider: Provider, suite: str | None = None, lier: bool = False
) -> RedirectResponse:
    _configured(request, provider)
    settings = _runtime(request).settings
    if wait := start_limit.take(f"ip:{_ip(request)}"):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"trop d'essais : réessaie dans {wait} s",
            headers={"Retry-After": str(wait)},
        )
    found: service.Authenticated | None = getattr(request.state, "user", None)
    if lier and found is None:
        return _redirect(_to(LOGIN, suite=CONNECTIONS), request)
    key = oidc.flows.start(
        provider, _next_path(suite), found.user_id if lier and found is not None else None
    )
    flow = oidc.flows.get(key)
    assert flow is not None
    response = RedirectResponse(
        oidc.authorize_url(settings, provider, flow), status_code=status.HTTP_303_SEE_OTHER
    )
    response.headers["cache-control"] = "no-store"
    response.headers.append("set-cookie", _flow_cookie(key, _headers(request)))
    return response


@router.get(
    "/api/auth/oauth/{provider}/callback",
    operation_id="oauthCallback",
    status_code=status.HTTP_303_SEE_OTHER,
)
async def callback_get(
    request: Request,
    provider: Provider,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    return await _callback(request, provider, code, state, error, None)


@router.post(
    "/api/auth/oauth/{provider}/callback",
    operation_id="oauthCallbackForm",
    status_code=status.HTTP_303_SEE_OTHER,
)
async def callback_post(
    request: Request,
    provider: Provider,
    code: Annotated[str | None, Form(max_length=2000)] = None,
    state: Annotated[str | None, Form(max_length=300)] = None,
    error: Annotated[str | None, Form(max_length=100)] = None,
    user: Annotated[str | None, Form(max_length=2000)] = None,
) -> RedirectResponse:
    """Apple : `response_mode=form_post` ; le champ `user` n'arrive qu'à la première fois."""
    return await _callback(request, provider, code, state, error, user)


def _cookie(request: Request, name: str) -> str | None:
    return request.cookies.get(name)


async def _callback(
    request: Request,
    provider: str,
    code: str | None,
    state: str | None,
    error: str | None,
    apple_user: str | None,
) -> RedirectResponse:
    if provider not in _runtime(request).settings.oauth_providers:
        return _refused(request, provider, "indisponible")
    runtime = _runtime(request)
    settings = runtime.settings
    try:
        flow = oidc.flows.take(_cookie(request, oidc.FLOW_COOKIE), provider, state)
    except oidc.OidcError as exc:
        log.warning("oauth_flow_refused", provider=provider, detail=str(exc), ip=_ip(request))
        return _refused(request, provider, exc.reason)
    link = flow.link_account is not None
    if error or not code:
        # La personne a annulé chez le fournisseur.
        return _refused(request, provider, "annule", link=link, account=flow.link_account)
    try:
        async with http_client() as client:
            token = await oidc.exchange(client, settings, provider, code[:2000], flow.verifier)
            identity = await oidc.verify_id_token(client, settings, provider, token, flow.nonce)
    except oidc.OidcError as exc:
        log.warning("oauth_token_refused", provider=provider, detail=str(exc), ip=_ip(request))
        return _refused(request, provider, exc.reason, link=link, account=flow.link_account)
    if provider == "apple" and identity.email is None:
        email = oidc.apple_first_email(apple_user)
        if email:
            identity = oidc.Identity(provider, identity.subject, email, False)
    if flow.link_account is not None:
        return await _link(request, identity, flow.link_account)
    return await _login(request, identity, flow.next_path)


async def _link_of(runtime: Runtime, provider: str, subject: str) -> int | None:
    async with runtime.sessionmaker.begin() as session:
        found = await session.scalar(select(func.account_of_oauth(provider, subject)))
    return None if found is None else int(found)


async def _add_link(runtime: Runtime, account: int, identity: oidc.Identity) -> bool:
    """Le lien, au nom du compte ; False si ce compte du fournisseur vient d'être lié ailleurs."""
    with accounts.use(account):
        try:
            async with runtime.sessionmaker.begin() as session:
                session.add(
                    OauthLink(
                        provider=identity.provider,
                        subject=identity.subject,
                        email=identity.email,
                        email_verified=identity.email_verified,
                        last_used_at=datetime.now(UTC),
                    )
                )
        except IntegrityError:
            return False
    return True


async def _link(request: Request, identity: oidc.Identity, account: int) -> RedirectResponse:
    runtime = _runtime(request)
    provider = identity.provider
    owner_of_link = await _link_of(runtime, provider, identity.subject)
    if owner_of_link is not None and owner_of_link != account:
        return _refused(request, provider, "deja-lie", link=True, account=account)
    if owner_of_link is None and not await _add_link(runtime, account, identity):
        return _refused(request, provider, "deja-lie", link=True, account=account)
    log.info("oauth_linked", provider=provider, account=account, ip=_ip(request))
    return _redirect(_to(CONNECTIONS, lie=provider), request)


async def _login(
    request: Request, identity: oidc.Identity, next_path: str | None
) -> RedirectResponse:
    runtime = _runtime(request)
    provider = identity.provider
    async with runtime.sessionmaker.begin() as session:
        if not await accounts.has_password(session):
            # Premier démarrage : le premier compte (l'exploitant) se crée par la commande.
            return _refused(request, provider, "indisponible")
    account = await _link_of(runtime, provider, identity.subject)
    if account is None and identity.email_verified and identity.email:
        async with runtime.sessionmaker.begin() as session:
            found = await session.scalar(select(func.account_of_verified_email(identity.email)))
        if found is not None:
            account = int(found)
            if not await _add_link(runtime, account, identity):
                return _refused(request, provider, "refuse")
            log.info("oauth_linked_by_email", provider=provider, account=account)
    if account is None:
        return await _request_account(request, identity)
    with accounts.use(account):
        async with runtime.sessionmaker.begin() as session:
            user = await session.get(User, account)
            if user is None:
                return _refused(request, provider, "aucun-compte")
            if user.suspended_at is not None:
                return _refused(request, provider, "suspendu", account=account)
            if user.approved_at is None:
                return _refused(request, provider, "en-attente", account=account)
            row = await session.scalar(
                select(OauthLink).where(
                    OauthLink.provider == provider, OauthLink.subject == identity.subject
                )
            )
            if row is not None:
                row.last_used_at = datetime.now(UTC)
                # Apple ne donne l'e-mail qu'à la première fois : gardé à ce moment-là.
                if row.email is None and identity.email:
                    row.email = identity.email
                    row.email_verified = identity.email_verified
            token = await service.create_session(
                session, user.id, request.headers.get("user-agent")
            )
            user.last_login_at = func.now()
        await _ensure_profile(runtime, account)
        with accounts.use(account):
            async with runtime.sessionmaker() as session:
                step = welcome.status(await welcome.state(session))
    log.info("oauth_login_succeeded", provider=provider, account=account, ip=_ip(request))
    target = "/bienvenue" if step in ("pending", "postponed") else (next_path or "/aujourdhui")
    return _redirect(target, request, [session_cookie(token, _headers(request))])


def username_from(identity: oidc.Identity) -> str:
    """Un identifiant proposé : le début de l'e-mail, sans accents ni signes ; sinon « membre »."""
    base = (identity.email or "").split("@")[0]
    base = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode("ascii")
    base = re.sub(r"[^a-z0-9._-]+", "", base.lower()).strip("._-")[: USERNAME_MAX - 4]
    return base or "membre"


async def _request_account(request: Request, identity: oidc.Identity) -> RedirectResponse:
    """Aucun compte lié : une demande de compte si elles sont ouvertes (docs/102), sinon refus."""
    runtime = _runtime(request)
    provider = identity.provider
    if not await signup.is_open(runtime):
        return _refused(request, provider, "aucun-compte")
    if signup_limit.take(f"ip:{_ip(request)}"):
        return _refused(request, provider, "trop-de-demandes")
    owner = await _owner(runtime)
    base = username_from(identity)
    with accounts.use(owner):
        async with runtime.sessionmaker.begin() as session:
            name = None
            for suffix in ["", *[f"-{n}" for n in range(2, 100)]]:
                try:
                    name = await free_username(session, f"{base}{suffix}")
                    break
                except LinkError:
                    continue
            if name is None:
                return _refused(request, provider, "refuse")
            user = User(
                username=name,
                # Pas de mot de passe : la connexion passe par le fournisseur.
                password_hash=accounts.UNUSABLE_PASSWORD,
                # Explicitement vide : la demande attend l'exploitant (docs/102).
                approved_at=null(),
                signup_note=f"Demande par {oidc.LABELS[provider]}",
            )
            session.add(user)
            await session.flush()
            account = user.id
    if not await _add_link(runtime, account, identity):
        return _refused(request, provider, "refuse")
    log.info("signup_requested", provider=provider, account=account, ip=_ip(request))
    with accounts.use(owner):
        await notify.deliver(
            runtime,
            notify.Message(
                title=f"Nouvelle demande de compte : {name}",
                message="À accepter ou refuser dans les Réglages, rubrique Plateforme.",
                tags=["bust_in_silhouette"],
                click=f"{runtime.settings.public_url.rstrip('/')}/reglages?rubrique=plateforme",
            ),
            kind="signup_request",
            link="/reglages?rubrique=plateforme",
        )
    return _redirect(_to(LOGIN, info="demande", fournisseur=provider), request)


async def _owner(runtime: Runtime) -> int:
    async with runtime.sessionmaker.begin() as session:
        return await accounts.owner_id(session)


# --- Compte, Connexions ------------------------------------------------------------------


class ConnectionOut(BaseModel):
    id: int
    provider: Provider
    email: str | None
    created_at: datetime
    last_used_at: datetime | None


class Connections(BaseModel):
    # Les fournisseurs proposés sur cette installation.
    providers: list[Provider]
    links: list[ConnectionOut]
    # Le compte a un mot de passe : il reste un moyen de se connecter sans fournisseur.
    has_password: bool


async def _connections(runtime: Runtime) -> Connections:
    async with runtime.sessionmaker() as session:
        user = await session.get(User, accounts.current())
        rows = await session.scalars(select(OauthLink).order_by(OauthLink.created_at))
        links = [
            ConnectionOut(
                id=row.id,
                provider=row.provider,
                email=row.email,
                created_at=row.created_at,
                last_used_at=row.last_used_at,
            )
            for row in rows
        ]
    return Connections(
        providers=runtime.settings.oauth_providers,
        links=links,
        has_password=user is not None and user.password_hash != accounts.UNUSABLE_PASSWORD,
    )


@router.get(
    "/api/account/connexions",
    operation_id="getConnections",
    responses={401: {"description": "Connexion requise"}},
)
async def get_connections(request: Request) -> Connections:
    response = await _connections(_runtime(request))
    return response


@router.delete(
    "/api/account/connexions/{connection_id}",
    operation_id="removeConnection",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Lien inconnu"},
        409: {"description": "Dernier moyen de se connecter"},
    },
)
async def remove_connection(request: Request, connection_id: int) -> None:
    runtime = _runtime(request)
    async with runtime.sessionmaker.begin() as session:
        # Relu sous la séparation du compte : le lien d'un autre compte n'existe pas (C-5).
        row = await session.get(OauthLink, connection_id)
        if row is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "lien inconnu")
        user = await session.get(User, accounts.current())
        others = await session.scalar(
            select(func.count()).select_from(OauthLink).where(OauthLink.id != connection_id)
        )
        has_password = user is not None and user.password_hash != accounts.UNUSABLE_PASSWORD
        if not has_password and not others:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "c'est ton seul moyen de te connecter : lie d'abord un autre compte",
            )
        provider = row.provider
        await session.delete(row)
    log.info("oauth_unlinked", provider=provider, account=accounts.current())
