"""Fonctions de lecture de l'assistant (docs/24 §2.2).

Lecture seule : aucune ne modifie la base. Elles ne rendent jamais les coordonnées de la
personne (nom, adresse, téléphone, e-mail), ni celles des contacts d'une candidature, ni le
contenu brut des e-mails.
"""

import json
import re
from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.alerts import service as alert_service
from jobbot.core.orp import LOCAL_TZ, due_date, shift_month
from jobbot.db.models import (
    AlertSearch,
    Application,
    ApplicationStatus,
    Evaluation,
    Interview,
    NewsItem,
    NewsSource,
    Offer,
    OfferStatus,
    OrpMonth,
    ProfileSource,
    Site,
    Training,
    TrainingMark,
)
from jobbot.interviews import service as interview_service
from jobbot.notify import interviews as interview_reminders
from jobbot.notify.service import REMIND_AFTER_DAYS
from jobbot.orp.service import load_due_day, load_target, month_counts
from jobbot.scoring.service import active_profile

_MONTH = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
DESCRIPTION_LIMIT = 4_000
CHUNK_LIMIT = 1_500


def _month_param(description: str) -> dict[str, Any]:
    return {"type": "string", "description": description, "pattern": r"^\d{4}-\d{2}$"}


TOOLS: list[dict[str, Any]] = [
    {
        "name": "situation",
        "description": "Vue d'ensemble du jour : offres à examiner, candidatures à relancer, "
        "compteur ORP du mois, entretiens sans retour, alertes qui n'arrivent pas. "
        "À appeler pour « que faire aujourd'hui ? » ou « où en suis-je ? ».",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "offres_a_examiner",
        "description": "Les offres à examiner (non triées, non expirées), les mieux notées "
        "d'abord : id, titre, entreprise, lieu, note sur 100, résumé du poste.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limite": {"type": "integer", "minimum": 1, "maximum": 20, "default": 10}
            },
        },
    },
    {
        "name": "offre",
        "description": "Le détail d'une offre par son id : description, note, résumé de l'IA, "
        "points forts et manques, liens, statut.",
        "input_schema": {
            "type": "object",
            "properties": {"id": {"type": "integer"}},
            "required": ["id"],
        },
    },
    {
        "name": "candidatures",
        "description": "Les candidatures envoyées d'un mois ORP : id, entreprise, poste, date "
        "d'envoi, statut, entretien, à relancer, ligne ORP incomplète.",
        "input_schema": {
            "type": "object",
            "properties": {"mois": _month_param("Mois AAAA-MM ; le mois en cours par défaut.")},
        },
    },
    {
        "name": "preuves_orp",
        "description": "Les preuves ORP d'un mois : nombre de candidatures, objectif, lignes à "
        "compléter, date limite de remise, état de la remise.",
        "input_schema": {
            "type": "object",
            "properties": {"mois": _month_param("Mois AAAA-MM ; le mois en cours par défaut.")},
        },
    },
    {
        "name": "alertes",
        "description": "Les recherches suivies par alerte e-mail et, par site, leur état : "
        "reçue (avec la date), créée en attente, à créer.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "retours_entretien",
        "description": "Les enseignements des retours d'entretien : questions qui reviennent "
        "(difficiles d'abord), ce qui a marché ou non, ce qui reste à préparer, et les "
        "derniers entretiens.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "profil",
        "description": "Les blocs de profil actifs (expériences, compétences, formations, "
        "préférences, rédhibitoires, ton) : la seule source sur le parcours de la personne.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "actualites",
        "description": "Les dernières actualités des sources suivies par le profil affiché.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limite": {"type": "integer", "minimum": 1, "maximum": 20, "default": 10}
            },
        },
    },
    {
        "name": "formations",
        "description": "Les formations suivies par le profil affiché (intéressé, en cours, "
        "terminée), avec la progression.",
        "input_schema": {"type": "object", "properties": {}},
    },
]

LABELS = {
    "situation": "ta situation du jour",
    "offres_a_examiner": "les offres à examiner",
    "offre": "l'offre",
    "candidatures": "tes candidatures",
    "preuves_orp": "tes preuves ORP",
    "alertes": "tes alertes",
    "retours_entretien": "tes retours d'entretien",
    "profil": "tes blocs de profil",
    "actualites": "les actualités",
    "formations": "tes formations",
}


class ToolInputError(ValueError):
    """Paramètre absent ou invalide : rendu à l'IA comme une erreur, sans rien exécuter."""


def _today() -> date:
    return datetime.now(UTC).astimezone(LOCAL_TZ).date()


def _limit(params: dict[str, Any], default: int = 10) -> int:
    value = params.get("limite", default)
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 20:
        raise ToolInputError("limite : un entier de 1 à 20")
    return value


def _month(params: dict[str, Any]) -> str:
    value = params.get("mois")
    if value is None:
        return f"{_today():%Y-%m}"
    if not isinstance(value, str) or not _MONTH.match(value):
        raise ToolInputError("mois : au format AAAA-MM")
    return value


def _day(value: date | datetime | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.astimezone(LOCAL_TZ).strftime("%Y-%m-%d %H:%M")
    return value.isoformat()


def _cut(text: str | None, limit: int) -> str | None:
    if not text:
        return None
    return text if len(text) <= limit else text[:limit] + " […]"


Tool = Callable[[AsyncSession, int, dict[str, Any]], Awaitable[Any]]


async def _situation(session: AsyncSession, _profile: int, _params: dict[str, Any]) -> Any:
    today = _today()
    month = f"{today:%Y-%m}"
    to_review = await session.scalar(
        select(func.count())
        .select_from(Offer)
        .where(
            Offer.status.in_((OfferStatus.NEW, OfferStatus.TO_REVIEW)),
            Offer.expired_at.is_(None),
        )
    )
    to_follow_up = await session.scalar(
        select(func.count())
        .select_from(Application)
        .where(
            Application.status == ApplicationStatus.EN_ATTENTE,
            Application.sent_at <= today - timedelta(days=REMIND_AFTER_DAYS),
        )
    )
    counts = await month_counts(session, month)
    pending = await interview_reminders.to_review(session, today)
    return {
        "date": today.isoformat(),
        "offres_a_examiner": to_review or 0,
        "candidatures_a_relancer": to_follow_up or 0,
        "relance_apres_jours": REMIND_AFTER_DAYS,
        "orp_mois": {
            "mois": month,
            "candidatures": counts.count,
            "objectif": await load_target(session),
            "lignes_a_completer": counts.incomplete,
        },
        "entretiens_sans_retour": [
            {
                "candidature_id": p.application_id,
                "entreprise": p.company,
                "date": _day(p.interview_on),
            }
            for p in pending
        ],
        "alertes_sans_envoi_depuis_3_jours": await alert_service.waiting(session),
    }


async def _offers_to_review(session: AsyncSession, _profile: int, params: dict[str, Any]) -> Any:
    limit = _limit(params)
    rows = (
        await session.execute(
            select(Offer, Evaluation)
            .outerjoin(Evaluation, Evaluation.offer_id == Offer.id)
            .where(
                Offer.status.in_((OfferStatus.NEW, OfferStatus.TO_REVIEW)),
                Offer.expired_at.is_(None),
                Evaluation.filter_passed.is_not(False),
            )
            .order_by(Evaluation.score.desc().nulls_last(), Offer.first_seen_at.desc())
            .limit(limit)
        )
    ).all()
    return [
        {
            "id": offer.id,
            "titre": offer.title,
            "entreprise": offer.company,
            "lieu": offer.location,
            "note": evaluation.score if evaluation else None,
            "poste": evaluation.summary_role if evaluation else None,
            "recue_le": _day(offer.first_seen_at),
        }
        for offer, evaluation in rows
    ]


async def _offer(session: AsyncSession, _profile: int, params: dict[str, Any]) -> Any:
    offer_id = params.get("id")
    if not isinstance(offer_id, int) or isinstance(offer_id, bool):
        raise ToolInputError("id : l'identifiant entier de l'offre")
    offer = await session.get(Offer, offer_id)
    if offer is None:
        return {"erreur": f"aucune offre {offer_id}"}
    evaluation = await session.scalar(select(Evaluation).where(Evaluation.offer_id == offer.id))
    applied = await session.scalar(select(Application.id).where(Application.offer_id == offer.id))
    result: dict[str, Any] = {
        "id": offer.id,
        "titre": offer.title,
        "entreprise": offer.company,
        "lieu": offer.location,
        "taux": f"{offer.rate_min}-{offer.rate_max} %" if offer.rate_min else None,
        "contrat": offer.employment_type,
        "statut": offer.status,
        "expiree": offer.expired_at is not None,
        "recue_le": _day(offer.first_seen_at),
        "candidature_id": applied,
        "annonce_chez_employeur": offer.employer_url,
        "lien_pour_postuler": offer.employer_url or offer.apply_url,
        "description": _cut(offer.description or offer.snippet, DESCRIPTION_LIMIT),
    }
    if evaluation:
        result |= {
            "filtre_passe": evaluation.filter_passed,
            "raisons_du_filtre": [r.get("message") for r in evaluation.filter_reasons or []],
            "note": evaluation.score,
            "resume_poste": evaluation.summary_role,
            "resume_demande": evaluation.summary_asks,
            "resume_offre": evaluation.summary_offers,
            "points_forts": evaluation.strengths,
            "manques": evaluation.gaps,
        }
    return result


async def _applications(session: AsyncSession, _profile: int, params: dict[str, Any]) -> Any:
    month = _month(params)
    limit = _today() - timedelta(days=REMIND_AFTER_DAYS)
    rows = await session.scalars(
        select(Application)
        .where(Application.orp_month == month)
        .order_by(Application.sent_at, Application.id)
    )
    return {
        "mois": month,
        "candidatures": [
            {
                "id": a.id,
                "entreprise": a.company,
                "poste": a.job_title,
                "lieu": a.location,
                "envoyee_le": _day(a.sent_at),
                "mode": a.method,
                "assignee_par_orp": a.assigned_by_orp,
                "statut": a.status,
                "entretien": _day(a.interview_at),
                "relancee_le": _day(a.reminded_at),
                "a_relancer": a.status == ApplicationStatus.EN_ATTENTE and a.sent_at <= limit,
                "ligne_orp_incomplete": not (a.company_address or "").strip(),
            }
            for a in rows
        ],
    }


async def _orp(session: AsyncSession, _profile: int, params: dict[str, Any]) -> Any:
    month = _month(params)
    counts = await month_counts(session, month)
    state = await session.get(OrpMonth, month)
    due_day = await load_due_day(session)
    return {
        "mois": month,
        "candidatures": counts.count,
        "objectif": await load_target(session),
        "lignes_a_completer": counts.incomplete,
        "a_remettre_avant": _day(due_date(month, due_day)),
        "remis_le": _day(state.submitted_at) if state else None,
        "modifie_apres_remise": bool(state and state.changed_after_submit),
        "mois_precedent": shift_month(month, -1),
    }


async def _alerts(session: AsyncSession, _profile: int, _params: dict[str, Any]) -> Any:
    sites = list(await session.scalars(select(Site).where(Site.active.is_(True))))
    result = []
    for search in await session.scalars(select(AlertSearch).order_by(AlertSearch.id)):
        cells = await alert_service.cells(session, search, sites)
        result.append(
            {
                "mots": search.terms,
                "lieu": search.location,
                "active": search.active,
                "sites": {
                    cell.site: {"etat": cell.status, "recue_le": _day(cell.received_at)}
                    for cell in cells
                },
            }
        )
    return result


async def _interviews(session: AsyncSession, _profile: int, _params: dict[str, Any]) -> Any:
    insights = await interview_service.insights(session)
    recent = (
        await session.execute(
            select(Interview, Application.company, Application.job_title)
            .join(Application, Application.id == Interview.application_id)
            .order_by(Interview.held_at.desc().nulls_last(), Interview.id.desc())
            .limit(5)
        )
    ).all()
    return {
        "nombre": insights.count,
        "ressenti_moyen_sur_5": insights.average_rating,
        "questions": [
            {"texte": q.text, "fois": q.count, "difficile": q.difficult}
            for q in insights.questions[:20]
        ],
        "a_marche": [n.text for n in insights.went_well[:10]],
        "n_a_pas_marche": [n.text for n in insights.went_badly[:10]],
        "a_preparer": [{"texte": t, "fait": done} for t, done in insights.to_prepare],
        "questions_regrettees": [n.text for n in insights.missed_questions[:10]],
        "retours_employeurs": [n.text for n in insights.employer_feedback[:10]],
        "derniers": [
            {
                "entreprise": company,
                "poste": title,
                "date": _day(i.held_at),
                "type": i.kind,
                "ressenti": i.rating,
                "suite": i.next_step,
                "suite_avant": _day(i.next_step_at),
            }
            for i, company, title in recent
        ],
    }


async def _profile(session: AsyncSession, _profile_id: int, _params: dict[str, Any]) -> Any:
    return [
        {"type": c.kind, "titre": c.title, "contenu": _cut(c.content, CHUNK_LIMIT)}
        for c in await active_profile(session)
    ]


async def _news(session: AsyncSession, profile_id: int, params: dict[str, Any]) -> Any:
    rows = (
        await session.execute(
            select(NewsItem, NewsSource.name)
            .join(NewsSource, NewsSource.id == NewsItem.source_id)
            .join(ProfileSource, ProfileSource.source_id == NewsSource.id)
            .where(ProfileSource.profile_id == profile_id, ProfileSource.active.is_(True))
            .order_by(NewsItem.published_at.desc())
            .limit(_limit(params))
        )
    ).all()
    return [
        {
            "titre": item.title,
            "source": source,
            "date": _day(item.published_at),
            "resume": _cut(item.summary, 400),
            "lien": item.url,
        }
        for item, source in rows
    ]


async def _trainings(session: AsyncSession, profile_id: int, _params: dict[str, Any]) -> Any:
    rows = (
        await session.execute(
            select(TrainingMark, Training)
            .join(Training, Training.id == TrainingMark.training_id)
            .where(TrainingMark.profile_id == profile_id)
            .order_by(TrainingMark.updated_at.desc())
        )
    ).all()
    return [
        {
            "titre": t.title,
            "organisme": t.provider,
            "suivi": m.status,
            "progression": m.progress,
            "terminee_le": _day(m.done_at),
            "certifie": m.certified,
            "lien": t.url,
        }
        for m, t in rows
    ]


_TOOLS: dict[str, Tool] = {
    "situation": _situation,
    "offres_a_examiner": _offers_to_review,
    "offre": _offer,
    "candidatures": _applications,
    "preuves_orp": _orp,
    "alertes": _alerts,
    "retours_entretien": _interviews,
    "profil": _profile,
    "actualites": _news,
    "formations": _trainings,
}


async def run(session: AsyncSession, profile_id: int, name: str, params: Any) -> tuple[str, bool]:
    """Exécute une fonction ; rend (résultat JSON, erreur ?)."""
    tool = _TOOLS.get(name)
    if tool is None:
        return f"fonction inconnue : {name}", True
    if not isinstance(params, dict):
        return "paramètres invalides : un objet est attendu", True
    try:
        result = await tool(session, profile_id, params)
    except ToolInputError as exc:
        return f"paramètre invalide : {exc}", True
    return json.dumps(result, ensure_ascii=False, default=str), False
