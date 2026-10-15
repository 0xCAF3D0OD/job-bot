"""Actions proposées par l'assistant (docs/52) : l'IA propose, Kevin confirme.

L'outil `proposer_action` ne change rien : il vérifie la cible, enregistre la proposition et
la renvoie à l'interface. Seules `confirm` et `undo`, appelées par les routes sur un clic de
Kevin, modifient la base, avec les mêmes règles que les boutons des pages.
"""

from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.api.routes.orp import mark_changed
from jobbot.db.models import Application, ApplicationStatus, ChatAction, Offer, OfferStatus
from jobbot.followups.service import local_today

NAME = "proposer_action"
MAX_PER_ANSWER = 3

OFFER_STATUSES = {
    OfferStatus.LATER: "Plus tard",
    OfferStatus.IGNORED: "Ignorée",
    OfferStatus.TO_REVIEW: "À examiner",
}
APPLICATION_STATUSES = {
    ApplicationStatus.RELANCEE: "Relancée",
    ApplicationStatus.SANS_REPONSE: "Sans réponse",
    ApplicationStatus.REFUS: "Refus",
    ApplicationStatus.ENGAGEMENT: "Engagement",
}
EXPIRY = {"expired": "expirée", "alive": "pas expirée"}

TOOL: dict[str, Any] = {
    "name": NAME,
    "description": "Propose UN changement, que la personne confirmera elle-même d'un clic : rien "
    "n'est fait sans sa confirmation, et tu ne peux pas confirmer. Seulement : trier une offre "
    "(type offre_statut : later, ignored, to_review), la signaler expirée ou non (offre_expiree : "
    "expired, alive), changer le statut d'une candidature (candidature_statut : relancee, "
    "sans_reponse, refus, engagement). Trois propositions au plus par réponse. Jamais pour créer "
    "ou supprimer une candidature, envoyer un message ou toucher au profil : donne le lien.",
    "input_schema": {
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "enum": ["offre_statut", "offre_expiree", "candidature_statut"],
            },
            "id": {"type": "integer", "description": "id de l'offre ou de la candidature"},
            "valeur": {"type": "string"},
        },
        "required": ["type", "id", "valeur"],
    },
}

_KINDS = {
    "offre_statut": "offer_status",
    "offre_expiree": "offer_expiry",
    "candidature_statut": "application_status",
}


class ActionRefused(ValueError):
    """Proposition impossible, ou action qui ne vaut plus : rien n'est changé."""


def _offer_name(offer: Offer) -> str:
    return f"« {offer.title} »" + (f" ({offer.company})" if offer.company else "")


async def _offer(session: AsyncSession, offer_id: int) -> Offer:
    offer = await session.get(Offer, offer_id)
    if offer is None:
        raise ActionRefused("offre introuvable")
    return offer


async def _check(session: AsyncSession, kind: str, target_id: int, value: str) -> str:
    """Vérifie que le changement est permis maintenant ; rend la phrase de la proposition."""
    if kind == "offer_status":
        if value not in OFFER_STATUSES:
            raise ActionRefused("statut d'offre non proposable (later, ignored, to_review)")
        offer = await _offer(session, target_id)
        applied = await session.scalar(
            select(Application.id).where(Application.offer_id == offer.id)
        )
        if applied or offer.status == OfferStatus.APPLIED:
            raise ActionRefused("une candidature est enregistrée pour cette offre")
        if offer.status == value:
            raise ActionRefused("l'offre est déjà dans cet état")
        return f"Passer {_offer_name(offer)} en {OFFER_STATUSES[OfferStatus(value)]}"
    if kind == "offer_expiry":
        if value not in EXPIRY:
            raise ActionRefused("valeur attendue : expired ou alive")
        offer = await _offer(session, target_id)
        if offer.status == OfferStatus.APPLIED:
            raise ActionRefused("candidature envoyée : l'offre n'est plus modifiée")
        if (offer.expired_at is not None) == (value == "expired"):
            raise ActionRefused("l'offre est déjà dans cet état")
        return f"Signaler {_offer_name(offer)} comme {EXPIRY[value]}"
    if kind == "application_status":
        if value not in APPLICATION_STATUSES:
            raise ActionRefused("statut non proposable (relancee, sans_reponse, refus, engagement)")
        application = await session.get(Application, target_id)
        if application is None:
            raise ActionRefused("candidature introuvable")
        if application.status == value:
            raise ActionRefused("la candidature est déjà dans cet état")
        label = APPLICATION_STATUSES[ApplicationStatus(value)]
        name = f"« {application.job_title} » chez {application.company}"
        return f"Passer la candidature {name} en {label}"
    raise ActionRefused("type d'action inconnu")


async def propose(
    session: AsyncSession, conversation_id: int, params: Any, already: int
) -> ChatAction:
    """Enregistre une proposition (outil de l'IA). Ne change rien d'autre."""
    if already >= MAX_PER_ANSWER:
        raise ActionRefused(f"{MAX_PER_ANSWER} propositions au plus par réponse")
    if not isinstance(params, dict):
        raise ActionRefused("paramètres invalides")
    kind = _KINDS.get(str(params.get("type")))
    target_id, value = params.get("id"), str(params.get("valeur", ""))
    if kind is None or not isinstance(target_id, int):
        raise ActionRefused("type et id attendus")
    label = await _check(session, kind, target_id, value)
    action = ChatAction(
        conversation_id=conversation_id, kind=kind, target_id=target_id, value=value, label=label
    )
    session.add(action)
    await session.flush()
    return action


def _day(value: date | None) -> str | None:
    return value.isoformat() if value else None


def _parse_day(value: Any) -> date | None:
    return date.fromisoformat(value) if isinstance(value, str) else None


def _apply_application(application: Application, status: str) -> None:
    # Mêmes règles que « Modifier la candidature » (docs/38) : date du statut, date de relance.
    today = local_today()
    if status != application.status:
        application.status_at = today
    if application.status != ApplicationStatus.RELANCEE or not application.followed_up_at:
        application.followed_up_at = today
    application.status = ApplicationStatus(status)


async def confirm(session: AsyncSession, action: ChatAction) -> None:
    """Fait le changement (clic « Confirmer »). Une proposition qui ne vaut plus devient
    « stale » sans rien changer."""
    if action.state != "proposed":
        raise ActionRefused("déjà décidée")
    try:
        await _check(session, action.kind, action.target_id, action.value)
    except ActionRefused:
        action.state, action.decided_at = "stale", datetime.now(UTC)
        raise
    if action.kind == "offer_status":
        offer = await _offer(session, action.target_id)
        action.previous = {"status": str(offer.status)}
        offer.status = OfferStatus(action.value)
    elif action.kind == "offer_expiry":
        offer = await _offer(session, action.target_id)
        action.previous = {
            "expired_at": offer.expired_at.isoformat() if offer.expired_at else None,
            "expiry_source": offer.expiry_source,
            "expiry_override": offer.expiry_override,
        }
        if action.value == "expired":
            offer.expired_at = datetime.now(UTC)
            offer.expiry_source, offer.expiry_override = "manual", "expired"
        else:
            offer.expired_at = offer.expiry_source = None
            offer.expiry_override = "alive"
    else:
        application = await session.get(Application, action.target_id)
        assert application is not None  # vérifiée par _check
        action.previous = {
            "status": str(application.status),
            "status_at": _day(application.status_at),
            "followed_up_at": _day(application.followed_up_at),
        }
        _apply_application(application, action.value)
        await mark_changed(session, {application.orp_month})
    action.state, action.decided_at = "done", datetime.now(UTC)


async def undo(session: AsyncSession, action: ChatAction) -> None:
    """Remet l'état d'avant (clic « Annuler »), si rien n'a changé depuis."""
    if action.state != "done" or not isinstance(action.previous, dict):
        raise ActionRefused("rien à annuler")
    previous = action.previous
    if action.kind == "offer_status":
        offer = await _offer(session, action.target_id)
        if offer.status != action.value:
            raise ActionRefused("l'offre a changé depuis : rien n'est annulé")
        offer.status = OfferStatus(previous["status"])
    elif action.kind == "offer_expiry":
        offer = await _offer(session, action.target_id)
        if (offer.expired_at is not None) != (action.value == "expired"):
            raise ActionRefused("l'offre a changé depuis : rien n'est annulé")
        expired_at = previous.get("expired_at")
        offer.expired_at = datetime.fromisoformat(expired_at) if expired_at else None
        offer.expiry_source = previous.get("expiry_source")
        offer.expiry_override = previous.get("expiry_override")
    else:
        application = await session.get(Application, action.target_id)
        if application is None or application.status != action.value:
            raise ActionRefused("la candidature a changé depuis : rien n'est annulé")
        application.status = ApplicationStatus(previous["status"])
        application.status_at = _parse_day(previous.get("status_at"))
        application.followed_up_at = _parse_day(previous.get("followed_up_at"))
        await mark_changed(session, {application.orp_month})
    action.state, action.decided_at = "undone", datetime.now(UTC)


async def decline(action: ChatAction) -> None:
    """« Non merci » : la proposition reste dans la discussion, sans effet."""
    if action.state != "proposed":
        raise ActionRefused("déjà décidée")
    action.state, action.decided_at = "declined", datetime.now(UTC)


def as_dict(action: ChatAction) -> dict[str, Any]:
    """Ce que l'interface affiche : la phrase et l'état."""
    return {
        "id": action.id,
        "kind": action.kind,
        "label": action.label,
        "state": action.state,
        "created_at": action.created_at.isoformat() if action.created_at else None,
    }
