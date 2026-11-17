"""Doublons et ancienneté des annonces (docs/30 §2), sans IA.

Deux offres au même titre et à la même entreprise (autre site, autre lien) sont la même
annonce : la plus avancée (en préparation, mise de côté…) ou à défaut la plus récente est
gardée, les autres lui sont rattachées et disparaissent des listes. `seen_since` garde la
première apparition de l'annonce, doublons compris : au-delà de 30 jours, c'est une annonce
permanente.

Offre déjà postulée (décision de Kevin du 16.11.2026, docs/decisions/2026-11-16-doublons-offres) :
- même lien qu'une offre envoyée = doublon sûr, rattaché à l'offre envoyée, il sort de la liste ;
  une candidature saisie sans fiche reçoit l'offre de son lien comme fiche ;
- même titre chez la même entreprise = doublon probable : jamais rattaché à l'offre envoyée (un
  poste republié ou un second poste au même titre resterait caché sans rien dire). L'offre reste
  visible, avec la pastille « Déjà postulé le … » (`applied_before`).
"""

from collections import defaultdict
from collections.abc import Iterable
from datetime import date, datetime
from urllib.parse import parse_qsl, urlencode, urlsplit

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.normalize import normalize_company, normalize_text, normalize_title
from jobbot.db.models import Application, Offer, OfferLink, OfferStatus

# L'offre gardée dans un groupe : celle sur laquelle tu as agi, puis une offre en ligne.
RANK: dict[str, int] = {
    OfferStatus.APPLIED: 5,
    OfferStatus.PREPARING: 4,
    OfferStatus.LATER: 3,
    OfferStatus.TO_REVIEW: 2,
    OfferStatus.NEW: 2,
    OfferStatus.FILTERED_OUT: 1,
    OfferStatus.IGNORED: 0,
}

# Paramètres d'adresse qui désignent l'annonce elle-même (Indeed : …/viewjob?jk=…) ; les autres
# (suivi, provenance) changent d'un e-mail à l'autre et sont ignorés.
_ID_PARAMS = frozenset({"jk", "vjk", "jobid", "job_id", "currentjobid", "id"})


def _key(offer: Offer) -> tuple[str, str] | None:
    title, company = normalize_text(offer.title), normalize_text(offer.company or "")
    return (title, company) if title and company else None


def post_key(title: str | None, company: str | None) -> tuple[str, str] | None:
    """Le poste : titre (sans taux ni genre) et entreprise (sans SA, Sàrl, AG, GmbH…), en
    minuscules, sans accents ni ponctuation."""
    wanted, at = normalize_title(title or ""), normalize_company(company)
    return (wanted, at) if wanted and at else None


def link_key(url: str | None) -> str | None:
    """La page de l'annonce : hôte (sans www), chemin (sans / final), et l'identifiant de
    l'annonce s'il est dans les paramètres. Rien pour la page d'accueil d'un site."""
    if not url:
        return None
    try:
        parts = urlsplit(url.strip())
    except ValueError:
        return None
    if parts.scheme not in ("http", "https") or not parts.hostname:
        return None
    path = parts.path.rstrip("/").lower()
    ids = sorted((k.lower(), v) for k, v in parse_qsl(parts.query) if k.lower() in _ID_PARAMS)
    if len(path) <= 1 and not ids:
        return None
    host = parts.hostname.lower().removeprefix("www.")
    return f"{host}{path}" + (f"?{urlencode(ids)}" if ids else "")


def _keep(group: list[Offer]) -> Offer:
    return max(
        group,
        key=lambda o: (RANK.get(o.status, 0), o.expired_at is None, o.first_seen_at, o.id),
    )


def _merge(group: list[Offer]) -> None:
    """Le groupe sous l'offre gardée."""
    kept = _keep(group)
    first: datetime = min(o.first_seen_at for o in group)
    for offer in group:
        if offer is kept:
            offer.duplicate_of = None
            offer.seen_since = first
        else:
            offer.duplicate_of = kept.id
            offer.seen_since = offer.first_seen_at


async def _links(session: AsyncSession, offers: Iterable[Offer]) -> dict[int, set[str]]:
    """Les pages connues de chaque offre : liens des alertes, annonce chez l'employeur,
    formulaire."""
    found: dict[int, set[str]] = defaultdict(set)
    for offer_id, url in await session.execute(select(OfferLink.offer_id, OfferLink.url)):
        if page := link_key(url):
            found[offer_id].add(page)
    for offer in offers:
        for other in (offer.employer_url, offer.apply_url):
            if page := link_key(other):
                found[offer.id].add(page)
    return found


async def group_duplicates(session: AsyncSession) -> int:
    """Rattache les doublons à l'offre gardée ; rend le nombre d'offres rattachées."""
    offers = list(await session.scalars(select(Offer)))
    links = await _links(session, offers)
    by_id = {o.id: o for o in offers}

    # 1. Doublon sûr : la page d'une offre envoyée, ou le lien d'une candidature saisie sans fiche.
    sent_pages: dict[str, Offer] = {}
    for offer in sorted((o for o in offers if o.status == OfferStatus.APPLIED), key=lambda o: o.id):
        for page in links.get(offer.id, ()):
            sent_pages.setdefault(page, offer)
    loose: dict[str, Application] = {}
    has_application: set[int] = set()
    if any(o.status != OfferStatus.APPLIED for o in offers):
        for application in await session.scalars(
            select(Application)
            .where(Application.offer_id.is_(None), Application.application_url.is_not(None))
            .order_by(Application.id)
        ):
            if own := link_key(application.application_url):
                loose.setdefault(own, application)
        has_application = set(
            await session.scalars(
                select(Application.offer_id).where(Application.offer_id.is_not(None))
            )
        )
    on_sent: dict[int, int] = {}
    for offer in offers:
        if offer.status == OfferStatus.APPLIED:
            continue
        pages = links.get(offer.id, set())
        target = next((sent_pages[k] for k in sorted(pages) if k in sent_pages), None)
        if target is not None:
            on_sent[offer.id] = target.id
            continue
        found = next((loose.pop(k) for k in sorted(pages) if k in loose), None)
        if (
            found is not None
            and offer.duplicate_of is None
            and offer.id not in has_application
        ):
            # La candidature saisie dans Envoyées trouve sa fiche : l'offre de son lien.
            found.offer_id = offer.id
            offer.status = OfferStatus.APPLIED
            for page in pages:
                sent_pages.setdefault(page, offer)

    # 2. Même titre chez la même entreprise : les offres envoyées entre elles, les autres entre
    # elles. Une candidature spontanée n'est le doublon de rien (docs/39 §4).
    groups: dict[tuple[bool, tuple[str, str]], list[Offer]] = defaultdict(list)
    alone: list[Offer] = []
    for offer in offers:
        same = None if offer.spontaneous or offer.id in on_sent else _key(offer)
        if same is None:
            alone.append(offer)
        else:
            groups[(offer.status == OfferStatus.APPLIED, same)].append(offer)
    for group in groups.values():
        _merge(group)
    for offer in alone:
        offer.duplicate_of = None
        offer.seen_since = offer.seen_since or offer.first_seen_at
    for offer_id, target_id in on_sent.items():
        offer, target = by_id[offer_id], by_id[target_id]
        # Rattachée à l'offre gardée de son groupe, si l'offre envoyée y est elle-même rattachée.
        kept = target.duplicate_of or target.id
        offer.duplicate_of = kept
        offer.seen_since = offer.first_seen_at
        if offer.first_seen_at < (by_id[kept].seen_since or by_id[kept].first_seen_at):
            by_id[kept].seen_since = offer.first_seen_at
    return sum(1 for o in offers if o.duplicate_of is not None)


async def applied_before(
    session: AsyncSession,
) -> dict[tuple[str, str], list[tuple[date, int | None]]]:
    """Les candidatures par poste (`post_key`), la plus récente d'abord, avec leur fiche."""
    found: dict[tuple[str, str], list[tuple[date, int | None]]] = defaultdict(list)
    rows = await session.execute(
        select(
            Application.job_title, Application.company, Application.sent_at, Application.offer_id
        ).order_by(Application.sent_at.desc(), Application.id.desc())
    )
    for title, company, sent_at, offer_id in rows:
        if key := post_key(title, company):
            found[key].append((sent_at, offer_id))
    return found


def sent_on(
    offer: Offer, sent: dict[tuple[str, str], list[tuple[date, int | None]]]
) -> date | None:
    """Doublon probable : la dernière candidature au même poste, envoyée depuis une autre fiche
    ou saisie sans fiche. Rien pour une offre déjà envoyée."""
    if offer.status == OfferStatus.APPLIED or not sent:
        return None
    key = post_key(offer.title, offer.company)
    if key is None:
        return None
    return next((day for day, offer_id in sent.get(key, ()) if offer_id != offer.id), None)
