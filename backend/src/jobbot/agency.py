"""Agences de placement (section 35 de la maquette du 16.11, décision de Kevin du 16.11).

Sans IA : une agence connue par son nom (sûr), ou une annonce qui recrute « pour notre client »
(probable). Les corrections « Ce n'est pas une agence » et « C'est une agence de placement »
(Kevin, 16.11 23 h 33) sont gardées par compte, pour l'entreprise (réglages `not_agencies` et
`agencies`) ; la dernière l'emporte sur la détection. Le répertoire SECO n'est pas lu tant que
le SECO n'a pas donné son accord écrit. Les mêmes règles en Python (la fiche) et en SQL (le
filtre), pour qu'une offre marquée « Agence » soit aussi celle que « Masquer les agences de
placement » cache.
"""

import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Literal

from sqlalchemy import ColumnElement, and_, func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.normalize import normalize_text
from jobbot.db.models import Application, Offer, Setting
from jobbot.employer.service import AGENCIES, CLIENT_PHRASES, title_matches

AgencyKind = Literal["known", "probable"]

# La correction de l'utilisateur, par compte : les entreprises (nom en minuscules, sans espaces
# autour) qui ne sont pas des agences. Niveau : personnelle (D-1), exportée et effacée avec les
# réglages du compte.
NOT_AGENCIES = "not_agencies"
# Dans l'autre sens : les entreprises que la personne a marquées « agence de placement ». Une
# entreprise n'est que dans l'une des deux listes : la dernière correction retire l'autre.
MARKED_AGENCIES = "agencies"
# Une candidature envoyée à un poste proche, ces 90 derniers jours (décision de Kevin du 16.11).
DUPLICATE_DAYS = 90

_ACCENTED = "àâäáãåéèêëíìîïóòôöõúùûüçñÿ"
_PLAIN = "aaaaaaeeeeiiiiooooouuuucny"


@dataclass(frozen=True)
class Corrections:
    """Les corrections du compte, par entreprise (`company_key`)."""

    yes: frozenset[str] = frozenset()
    no: frozenset[str] = frozenset()


NO_CORRECTIONS = Corrections()


def company_key(company: str | None) -> str:
    return (company or "").strip().lower()


def _known(company: str | None) -> bool:
    name = f" {normalize_text(company or '')} "
    return any(f" {normalize_text(a)} " in name for a in AGENCIES)


def _for_client(text: str | None) -> bool:
    body = normalize_text(text or "")
    return any(normalize_text(p) in body for p in CLIENT_PHRASES)


def agency_kind(offer: Offer, corrections: Corrections) -> AgencyKind | None:
    """« known » : agence connue ou marquée par la personne ; « probable » : l'annonce recrute
    pour un client."""
    key = company_key(offer.company)
    if offer.spontaneous or key in corrections.no:
        return None
    if key in corrections.yes or _known(offer.company):
        return "known"
    if _for_client(offer.description or offer.snippet) or offer.employer_status == "agency":
        return "probable"
    return None


def _norm(column: Any) -> ColumnElement[str]:
    """normalize_text en SQL : minuscules, sans accents, tout ce qui n'est ni lettre ni chiffre
    devient une espace."""
    lowered = func.translate(func.lower(func.coalesce(column, "")), _ACCENTED, _PLAIN)
    return func.regexp_replace(lowered, "[^a-z0-9]+", " ", "g")


def agency_condition(corrections: Corrections) -> ColumnElement[bool]:
    """Les offres que `agency_kind` marque, en SQL."""
    key = func.lower(func.btrim(func.coalesce(Offer.company, "")))
    name = literal(" ").concat(_norm(Offer.company)).concat(" ")
    known = or_(*(name.like(f"% {normalize_text(a)} %") for a in AGENCIES))
    body = _norm(func.coalesce(func.nullif(Offer.description, ""), Offer.snippet))
    for_client = or_(*(body.like(f"%{normalize_text(p)}%") for p in CLIENT_PHRASES))
    found = [known, for_client, func.coalesce(Offer.employer_status, "") == "agency"]
    if corrections.yes:
        found.append(key.in_(sorted(corrections.yes)))
    conditions = [Offer.spontaneous.is_(False), or_(*found)]
    if corrections.no:
        conditions.append(key.not_in(sorted(corrections.no)))
    return and_(*conditions)


async def load_corrections(session: AsyncSession) -> Corrections:
    rows = await session.execute(
        select(Setting.key, Setting.value).where(Setting.key.in_([MARKED_AGENCIES, NOT_AGENCIES]))
    )
    lists = {
        k: frozenset(str(v) for v in value) if isinstance(value, list) else frozenset()
        for k, value in rows
    }
    return Corrections(
        yes=lists.get(MARKED_AGENCIES, frozenset()), no=lists.get(NOT_AGENCIES, frozenset())
    )


def _title(value: str) -> str:
    """Le titre sans taux ni chiffres : « DevOps Engineer (80-100 %) » → « DevOps Engineer »."""
    return re.sub(r"[\d%]+", " ", value)


def _city(location: str | None) -> str:
    return normalize_text((location or "").split(",")[0])


@dataclass(frozen=True)
class Duplicate:
    title: str
    company: str
    sent_at: date
    # L'offre de cette candidature, pour ne pas se signaler soi-même.
    offer_id: int | None
    city: str


async def recent_applications(session: AsyncSession, today: date) -> list[Duplicate]:
    """Les candidatures envoyées ces 90 derniers jours, la plus récente d'abord : une requête
    par page de la liste, et seulement s'il y a une agence dans la page."""
    rows = await session.execute(
        select(
            Application.job_title,
            Application.company,
            Application.sent_at,
            Application.offer_id,
            func.coalesce(Application.location, Offer.location),
        )
        .outerjoin(Offer, Offer.id == Application.offer_id)
        .where(Application.sent_at >= today - timedelta(days=DUPLICATE_DAYS))
        .order_by(Application.sent_at.desc(), Application.id.desc())
    )
    return [Duplicate(t, c, d, o, _city(loc)) for t, c, d, o, loc in rows]


def duplicate(offer: Offer, sent: list[Duplicate]) -> Duplicate | None:
    """Une candidature à un poste proche (titre proche, même ville), chez l'employeur ou via
    une autre agence ; la plus récente."""
    city = _city(offer.location)
    if not city:
        return None
    wanted = _title(offer.title)
    for row in sent:
        if (
            row.offer_id != offer.id
            and row.city == city
            and title_matches(wanted, _title(row.title))
        ):
            return row
    return None
