"""Actions proposées par l'assistant (docs/52) : l'IA propose, Kevin confirme.

L'outil `proposer_action` ne change rien : il vérifie la cible, enregistre la proposition et
la renvoie à l'interface. Seules `confirm` et `undo`, appelées par les routes sur un clic de
Kevin, modifient la base, avec les mêmes règles que les boutons des pages.
"""

from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.api.routes.orp import mark_changed
from jobbot.db.models import (
    Application,
    ApplicationStatus,
    ChatAction,
    Offer,
    OfferStatus,
    Setting,
)
from jobbot.followups.service import local_today
from jobbot.letters.document import MONTHS
from jobbot.rhythm.service import DAY_NAMES, DEFAULT_DAYS

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
    ApplicationStatus.ENGAGEMENT: "Poste obtenu",
}
EXPIRY = {"expired": "expirée", "alive": "pas expirée"}
# Le bon rythme (docs/86, 0.68.1) : réglages du compte, sans cible (id 0).
RHYTHM_KEYS = ("rhythm_days", "rhythm_pause_from", "rhythm_pause_until")

TOOL: dict[str, Any] = {
    "name": NAME,
    "description": "Propose UN changement, que la personne confirmera elle-même d'un clic : rien "
    "n'est fait sans sa confirmation, et tu ne peux pas confirmer. Seulement : trier une offre "
    "(type offre_statut : later, ignored, to_review), la signaler expirée ou non (offre_expiree : "
    "expired, alive), changer le statut d'une candidature (candidature_statut : relancee, "
    "sans_reponse, refus, engagement), régler les jours de recherche (rythme_jours, id 0, "
    "valeur : numéros des jours séparés par des virgules, lundi = 0, par exemple « 0,2,4 »), "
    "faire une pause (pause, id 0, valeur « AAAA-MM-JJ/AAAA-MM-JJ », ou « fin » pour la "
    "terminer). Trois propositions au plus par réponse. Jamais pour créer ou supprimer une "
    "candidature, envoyer un message ou toucher au profil : donne le lien.",
    "input_schema": {
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "enum": [
                    "offre_statut",
                    "offre_expiree",
                    "candidature_statut",
                    "rythme_jours",
                    "pause",
                ],
            },
            "id": {
                "type": "integer",
                "description": "id de l'offre ou de la candidature ; 0 pour le rythme",
            },
            "valeur": {"type": "string"},
        },
        "required": ["type", "id", "valeur"],
    },
}

_KINDS = {
    "offre_statut": "offer_status",
    "offre_expiree": "offer_expiry",
    "candidature_statut": "application_status",
    "rythme_jours": "rhythm_days",
    "pause": "rhythm_pause",
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


def _rhythm_days(value: str) -> list[int]:
    try:
        days = sorted({int(part) for part in value.split(",") if part.strip()})
    except ValueError:
        raise ActionRefused("jours attendus : 0 à 6, séparés par des virgules") from None
    if not days or any(d < 0 or d > 6 for d in days):
        raise ActionRefused("jours attendus : 0 à 6, au moins un")
    return days


def _pause(value: str) -> tuple[date, date] | None:
    """« fin » : None ; sinon les deux dates de la pause."""
    if value == "fin":
        return None
    try:
        start, end = (date.fromisoformat(part) for part in value.split("/"))
    except ValueError:
        raise ActionRefused("pause attendue : AAAA-MM-JJ/AAAA-MM-JJ, ou « fin »") from None
    if end < start:
        raise ActionRefused("la pause finit avant de commencer")
    if end < local_today():
        raise ActionRefused("cette pause est déjà passée")
    return start, end


def _long(day: date) -> str:
    return f"{'1er' if day.day == 1 else day.day} {MONTHS['fr'][day.month - 1]}"


async def _settings(session: AsyncSession) -> dict[str, Any]:
    rows = await session.scalars(select(Setting).where(Setting.key.in_(RHYTHM_KEYS)))
    return {s.key: s.value for s in rows}


async def _put(session: AsyncSession, key: str, value: Any) -> None:
    await session.execute(
        insert(Setting)
        .values(key=key, value=value)
        .on_conflict_do_update(index_elements=["user_id", "key"], set_={"value": value})
    )


def _rhythm_value(kind: str, current: dict[str, Any]) -> str:
    """L'état actuel, écrit comme la valeur d'une proposition (pour comparer)."""
    if kind == "rhythm_days":
        days = current.get("rhythm_days") or list(DEFAULT_DAYS)
        return ",".join(str(d) for d in sorted(days))
    start, end = current.get("rhythm_pause_from"), current.get("rhythm_pause_until")
    return f"{start}/{end}" if start and end else "fin"


async def _check_rhythm(session: AsyncSession, kind: str, value: str) -> str:
    current = await _settings(session)
    if kind == "rhythm_days":
        days = _rhythm_days(value)
        if _rhythm_value(kind, current) == ",".join(str(d) for d in days):
            raise ActionRefused("ce sont déjà tes jours de recherche")
        return "Garder comme jours de recherche : " + ", ".join(DAY_NAMES[d] for d in days)
    pause = _pause(value)
    if pause is None:
        if _rhythm_value(kind, current) == "fin":
            raise ActionRefused("aucune pause en cours")
        return "Terminer la pause"
    if _rhythm_value(kind, current) == f"{pause[0]}/{pause[1]}":
        raise ActionRefused("cette pause est déjà enregistrée")
    return f"Faire une pause du {_long(pause[0])} au {_long(pause[1])}"


async def _check(session: AsyncSession, kind: str, target_id: int, value: str) -> str:
    """Vérifie que le changement est permis maintenant ; rend la phrase de la proposition."""
    if kind in ("rhythm_days", "rhythm_pause"):
        return await _check_rhythm(session, kind, value)
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
        return f"Passer la candidature {name} en « {label} »"
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
    if action.kind in ("rhythm_days", "rhythm_pause"):
        action.previous = await _settings(session)
        if action.kind == "rhythm_days":
            await _put(session, "rhythm_days", _rhythm_days(action.value))
        else:
            pause = _pause(action.value)
            await _put(session, "rhythm_pause_from", pause[0].isoformat() if pause else None)
            await _put(session, "rhythm_pause_until", pause[1].isoformat() if pause else None)
    elif action.kind == "offer_status":
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
    if action.kind in ("rhythm_days", "rhythm_pause"):
        if _rhythm_value(action.kind, await _settings(session)) != (
            ",".join(str(d) for d in _rhythm_days(action.value))
            if action.kind == "rhythm_days"
            else action.value
        ):
            raise ActionRefused("le rythme a changé depuis : rien n'est annulé")
        keys = ("rhythm_days",) if action.kind == "rhythm_days" else RHYTHM_KEYS[1:]
        for key in keys:
            await _put(session, key, previous.get(key))
    elif action.kind == "offer_status":
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
