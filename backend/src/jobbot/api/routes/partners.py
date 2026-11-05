"""Get'emAll (docs/140) : l'autorisation, l'échange du code et la lecture du suivi.

Trois sortes de routes, sous `/api/partenaires/getemall` :

- avec la session de la personne : l'état de la liaison, « Autoriser », « Retirer » ;
- `POST /echange`, sans session : le serveur de Get'emAll, avec son secret client ;
- `/suivi`, `/candidatures/{id}/offre` et `DELETE /lien` : avec le jeton de liaison
  (`Authorization: Bearer jbg_…`, vérifié par le middleware), en lecture seule.

Rien d'autre ne passe que ce que rend chaque modèle : jamais le nom, les coordonnées, l'id du
compte jobA1, les contacts, les CV ni les lettres (docs/140 §3).
"""

from datetime import date, datetime
from typing import Annotated, Literal
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot import accounts, first_steps
from jobbot.api.routes.orp import _default_month
from jobbot.auth.service import Throttle
from jobbot.core.orp import due_date
from jobbot.db.models import Application, Contact, Offer, PartnerLink, User
from jobbot.letters.service import load_identity
from jobbot.llm.redact import redact
from jobbot.log import get_logger
from jobbot.orp.service import load_due_day, load_target, month_counts
from jobbot.partners import getemall as service
from jobbot.runtime import Runtime

log = get_logger(__name__)

router = APIRouter(prefix="/api/partenaires/getemall", tags=["partenaires"])
# Seul un mauvais secret client compte : un code faux vient d'une personne, par le serveur de
# Get'emAll, et ne doit pas bloquer les autres (un code de 128 bits ne se devine pas).
throttle = Throttle()
APPLICATIONS_LIMIT = 50
DESCRIPTION_LIMIT = 8_000
NO_STORE = "no-store"


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


def _ready(runtime: Runtime) -> None:
    if not runtime.settings.getemall_ready:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "connexion Get'emAll indisponible")


# --- Avec la session de la personne -------------------------------------------------------


class GetemallLinkState(BaseModel):
    # Configurée sur cette installation (secret et adresses de retour).
    available: bool
    # Marqué « testeur Get'emAll » par l'exploitant : seul un testeur peut autoriser.
    tester: bool
    linked: bool
    orp: bool
    authorized_at: datetime | None
    last_used_at: datetime | None


class GetemallAuthorizeIn(BaseModel):
    redirect_uri: Annotated[str, Field(max_length=300)]
    state: Annotated[str, Field(pattern=service.STATE.pattern)]
    code_challenge: Annotated[str, Field(pattern=service.CHALLENGE.pattern)]
    code_challenge_method: Literal["S256"]
    # La case à part de la page de consentement : les recherches ORP du mois.
    orp: bool = False


class GetemallAuthorizeOut(BaseModel):
    # L'adresse de retour, avec `code` et `state` : la page y envoie le navigateur.
    redirect_to: str


async def _tester(runtime: Runtime) -> bool:
    async with runtime.sessionmaker() as session:
        user = await session.get(User, accounts.current())
    return bool(user and user.getemall_tester)


@router.get("", operation_id="getemallLink")
async def link_state(request: Request) -> GetemallLinkState:
    runtime = _runtime(request)
    async with runtime.sessionmaker() as session:
        link = await service.current_link(session)
    active = link is not None and link.revoked_at is None
    return GetemallLinkState(
        available=runtime.settings.getemall_ready,
        tester=await _tester(runtime),
        linked=active,
        orp=bool(link and active and link.orp),
        authorized_at=link.authorized_at if link and active else None,
        last_used_at=link.last_used_at if link and active else None,
    )


@router.post(
    "/autorisation",
    operation_id="authorizeGetemall",
    responses={
        400: {"description": "Adresse de retour hors de la liste"},
        403: {"description": "Réservé aux testeurs invités"},
        404: {"description": "Connexion Get'emAll non configurée"},
    },
)
async def authorize(
    request: Request, body: GetemallAuthorizeIn, response: Response
) -> GetemallAuthorizeOut:
    runtime = _runtime(request)
    _ready(runtime)
    # Comparée à la liste de la configuration, jamais reprise de la requête sans cela.
    if body.redirect_uri not in runtime.settings.getemall_redirect_uris:
        log.warning("getemall_redirect_refused", account=accounts.current())
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "adresse de retour inconnue")
    if not await _tester(runtime):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Get'emAll est réservé aux testeurs invités pour l'instant"
        )
    async with runtime.sessionmaker.begin() as session:
        code = await service.create_code(
            session,
            redirect_uri=body.redirect_uri,
            code_challenge=body.code_challenge,
            orp=body.orp,
        )
    log.info("getemall_code_created", account=accounts.current(), orp=body.orp)
    response.headers["Cache-Control"] = NO_STORE
    query = urlencode({"code": code, "state": body.state})
    separator = "&" if "?" in body.redirect_uri else "?"
    return GetemallAuthorizeOut(redirect_to=f"{body.redirect_uri}{separator}{query}")


@router.delete("", operation_id="revokeGetemall", status_code=status.HTTP_204_NO_CONTENT)
async def revoke(request: Request) -> None:
    """« Retirer » dans les Réglages (Connexions) : Get'emAll ne lit plus rien."""
    async with _runtime(request).sessionmaker.begin() as session:
        revoked = await service.revoke(session)
    if revoked:
        log.info("getemall_revoked", account=accounts.current(), by="account")


# --- Le serveur de Get'emAll, sans session ------------------------------------------------


class GetemallExchangeIn(BaseModel):
    client_secret: Annotated[str, Field(max_length=200)]
    code: Annotated[str, Field(max_length=100)]
    code_verifier: Annotated[str, Field(max_length=128)]
    redirect_uri: Annotated[str, Field(max_length=300)]


class GetemallExchangeOut(BaseModel):
    # Propre à Get'emAll, stable, jamais l'id du compte jobA1.
    subject: str
    # Jeton de liaison, à garder chiffré côté Get'emAll : il ne sert qu'à lire le suivi.
    token: str
    orp: bool


@router.post(
    "/echange",
    operation_id="getemallExchange",
    responses={
        400: {"description": "Code inconnu, déjà lu, expiré, ou PKCE faux"},
        401: {"description": "Secret client faux"},
        404: {"description": "Connexion Get'emAll non configurée"},
        429: {"description": "Trop d'essais : attendre"},
    },
)
async def exchange(
    request: Request, body: GetemallExchangeIn, response: Response
) -> GetemallExchangeOut:
    runtime = _runtime(request)
    _ready(runtime)
    ip = request.client.host if request.client else "inconnue"
    key = f"getemall:{ip}"
    if wait := throttle.wait(key):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"trop d'essais : réessaie dans {wait} s",
            headers={"Retry-After": str(wait)},
        )
    if not service.secret_matches(runtime.settings, body.client_secret):
        throttle.fail(key)
        # Jamais le secret, le code ni le vérificateur dans les journaux.
        log.warning("getemall_exchange_refused", reason="secret", ip=ip)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "secret client invalide")
    throttle.reset(key)
    try:
        granted = await service.exchange(
            runtime.sessionmaker,
            code=body.code,
            verifier=body.code_verifier,
            redirect_uri=body.redirect_uri,
        )
    except service.InvalidCode:
        log.warning("getemall_exchange_refused", reason="code")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "code invalide ou expiré") from None
    log.info("getemall_linked", account=granted.account, orp=granted.orp)
    response.headers["Cache-Control"] = NO_STORE
    return GetemallExchangeOut(subject=granted.subject, token=granted.token, orp=granted.orp)


# --- Avec le jeton de liaison -------------------------------------------------------------


class GetemallProfile(BaseModel):
    """« Profil complété » : les premiers pas de jobA1 (docs/128), cinq étapes."""

    steps_done: int
    steps_total: int
    percent: int
    # La prochaine étape (profile, alerts, keep, prepare, sent), vide quand tout est fait.
    next_step: first_steps.StepKey | None


class GetemallOrp(BaseModel):
    """Les recherches du mois, seulement si la case ORP a été cochée."""

    month: str
    done: int
    target: int | None
    due_on: date


class GetemallApplication(BaseModel):
    id: int
    job_title: str
    company: str
    # Tel quel : en_attente, relancee, entretien, refus, engagement, sans_reponse.
    status: str
    interview_at: datetime | None


class GetemallFollowUp(BaseModel):
    profile: GetemallProfile
    # Absent sans la case ORP (le champ n'est pas rendu du tout).
    orp: GetemallOrp | None = None
    applications: list[GetemallApplication]


class GetemallOffer(BaseModel):
    title: str
    company: str | None
    # Le texte de l'annonce sans e-mail, téléphone, lien ni nom de contact.
    description: str | None


async def _link(request: Request, session: AsyncSession) -> PartnerLink:
    """La liaison posée par le middleware ; sans elle, rien (une route mal protégée)."""
    link_id = getattr(request.state, "partner_link", None)
    link = await session.get(PartnerLink, link_id) if link_id else None
    if link is None or link.revoked_at is not None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "jeton de liaison absent ou révoqué")
    return link


@router.get("/suivi", operation_id="getemallFollowUp", response_model_exclude_unset=True)
async def follow_up(request: Request, response: Response) -> GetemallFollowUp:
    response.headers["Cache-Control"] = NO_STORE
    async with _runtime(request).sessionmaker() as session:
        link = await _link(request, session)
        done = await first_steps.reached(session)
        steps = len(first_steps.STEPS)
        applications = await session.scalars(
            select(Application)
            .order_by(Application.sent_at.desc(), Application.id.desc())
            .limit(APPLICATIONS_LIMIT)
        )
        out = GetemallFollowUp(
            profile=GetemallProfile(
                steps_done=done,
                steps_total=steps,
                percent=round(100 * done / steps),
                next_step=first_steps.STEPS[done] if done < steps else None,
            ),
            applications=[
                GetemallApplication(
                    id=a.id,
                    job_title=a.job_title,
                    company=a.company,
                    status=a.status,
                    interview_at=a.interview_at,
                )
                for a in applications
            ],
        )
        if link.orp:
            month = await _default_month(session)
            out.orp = GetemallOrp(
                month=month,
                done=(await month_counts(session, month)).count,
                target=await load_target(session),
                due_on=due_date(month, await load_due_day(session)),
            )
    return out


@router.get(
    "/candidatures/{application_id}/offre",
    operation_id="getemallOffer",
    responses={404: {"description": "Candidature introuvable"}},
)
async def application_offer(
    request: Request, application_id: int, response: Response
) -> GetemallOffer:
    response.headers["Cache-Control"] = NO_STORE
    async with _runtime(request).sessionmaker() as session:
        await _link(request, session)
        application = await session.get(Application, application_id)
        if application is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "candidature introuvable")
        offer = await session.get(Offer, application.offer_id) if application.offer_id else None
        contacts = await session.scalars(
            select(Contact.name).where(
                (Contact.application_id == application.id)
                | (Contact.offer_id == application.offer_id)
            )
        )
        names = [application.contact_name, *contacts]
        identity = await load_identity(session)
    raw = (offer.description or offer.snippet) if offer else None
    description = (
        service.without_names(redact(raw[:DESCRIPTION_LIMIT], identity), names) if raw else None
    )
    return GetemallOffer(
        title=offer.title if offer else application.job_title,
        company=(offer.company if offer else None) or application.company,
        description=description,
    )


@router.delete("/lien", operation_id="getemallUnlink", status_code=status.HTTP_204_NO_CONTENT)
async def unlink(request: Request) -> None:
    """« Supprimer mes données » dans Get'emAll : la liaison est retirée aussi chez jobA1."""
    async with _runtime(request).sessionmaker.begin() as session:
        await _link(request, session)
        await service.revoke(session)
    log.info("getemall_revoked", account=accounts.current(), by="partner")
