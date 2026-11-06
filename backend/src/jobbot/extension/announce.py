"""« Envoyer à jobA1 » : l'annonce d'une page, envoyée par l'extension (docs/142 §3).

L'extension envoie le balisage `JobPosting` de la page (titre, entreprise, lieu, description) s'il
existe, sinon le texte principal (`main`/`article`), et l'adresse de la page. Rien d'autre. Le
texte est nettoyé comme un texte collé (nom de la personne retiré, 20 000 caractères au plus,
docs/111), puis :

1. même lien qu'une offre déjà là : cette offre est complétée ;
2. sinon même poste chez la même entreprise : on demande d'abord (« C'est bien cette offre ? »),
   jamais de rattachement silencieux ;
3. sinon : une nouvelle offre, comme « Ajouter une offre » (docs/111).

Dans les trois cas, l'offre est renotée tout de suite quand son texte change. Le journal ne
garde que l'id de l'offre et le chemin suivi, jamais le texte (J-1).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from sqlalchemy import select

from jobbot import manual_offers
from jobbot.core.normalize import normalize_offer
from jobbot.db.models import Evaluation, Offer, OfferLink
from jobbot.extension.service import _key
from jobbot.filtering.service import run_filter
from jobbot.log import get_logger
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring_service
from jobbot.scoring.compare import word

log = get_logger(__name__)

SOURCE = manual_offers.SOURCE
# Les sites des alertes, comme les nomme la phrase « reçue … par une alerte jobs.ch ».
SITE_NAMES = {
    "jobup": "jobup",
    "jobsch": "jobs.ch",
    "linkedin": "LinkedIn",
    "indeed": "Indeed",
    "jobroom": "Job-Room",
}


class SendProblem(Exception):
    """Ce qui empêche d'enregistrer l'annonce (texte illisible, IA indisponible, limite)."""

    def __init__(self, message: str, *, limit: bool = False) -> None:
        super().__init__(message)
        self.message = message
        self.limit = limit


class ChoiceMismatch(Exception):
    """« Oui, compléter cette offre » pour une offre qui n'est pas celle trouvée : refusé."""


@dataclass
class Page:
    url: str
    text: str
    title: str | None = None
    company: str | None = None
    location: str | None = None


@dataclass
class Known:
    """L'offre déjà là, à confirmer : son poste, son entreprise, quand et d'où elle est arrivée."""

    id: int
    title: str
    company: str | None
    received_at: datetime
    site: str | None


@dataclass
class Sent:
    outcome: Literal["filled", "added", "confirm"]
    offer_id: int | None = None
    score: int | None = None
    label: str | None = None
    # Complétée : les champs remplis ; vide, l'offre avait déjà tout.
    filled: list[str] = field(default_factory=list)
    known: Known | None = None


async def _same_link(runtime: Runtime, url: str) -> int | None:
    """L'offre de ce lien : même hôte (sans www) et même chemin, sur un lien d'alerte, l'annonce
    chez l'employeur ou le formulaire."""
    page = _key(url)
    if page is None or len(page[1]) <= 1:
        return None
    host = f"%{page[0]}%"
    async with runtime.sessionmaker() as session:
        rows = await session.execute(
            select(OfferLink.offer_id, OfferLink.url).where(OfferLink.url.ilike(host))
        )
        for offer_id, link in rows:
            if _key(link) == page:
                return int(offer_id)
        offers = await session.execute(
            select(Offer.id, Offer.employer_url, Offer.apply_url).where(
                Offer.employer_url.ilike(host) | Offer.apply_url.ilike(host)
            )
        )
        for offer_id, employer, apply in offers:
            if page in (_key(employer), _key(apply)):
                return int(offer_id)
    return None


async def _known(runtime: Runtime, offer_id: int) -> Known:
    async with runtime.sessionmaker() as session:
        offer = await session.get(Offer, offer_id)
        assert offer is not None
        source = await session.scalar(
            select(OfferLink.source)
            .where(OfferLink.offer_id == offer_id)
            .order_by(OfferLink.id)
            .limit(1)
        )
    return Known(
        id=offer.id,
        title=offer.title,
        company=offer.company,
        received_at=offer.first_seen_at,
        site=SITE_NAMES.get(source or ""),
    )


async def _score(runtime: Runtime, offer_id: int, rescore: bool) -> tuple[int | None, str | None]:
    """La note, refaite tout de suite si le texte a changé (sans IA, au plafond : l'ancienne)."""
    score: int | None = None
    if rescore and runtime.settings.llm_configured:
        score = await scoring_service.score_offer(runtime, offer_id)
    if score is None:
        async with runtime.sessionmaker() as session:
            score = await session.scalar(
                select(Evaluation.score).where(Evaluation.offer_id == offer_id)
            )
    return score, (word(score) if score is not None else None)


async def _draft(runtime: Runtime, page: Page) -> manual_offers.Draft:
    """La fiche de l'annonce : le balisage tel quel, sinon le texte lu par l'IA (docs/111)."""
    async with runtime.sessionmaker() as session:
        text = await manual_offers.clean_pasted(session, page.text)
    if len(text) < manual_offers.MIN_PASTED:
        raise SendProblem("Je ne trouve pas d'annonce sur cette page : ouvre l'annonce elle-même.")
    title = " ".join((page.title or "").split())[:300]
    if title:
        return manual_offers.Draft(
            title=title,
            company=" ".join((page.company or "").split())[:300] or None,
            location=" ".join((page.location or "").split())[:300] or None,
            description=text,
            url=page.url,
            read_by="page",
        )
    try:
        draft = await manual_offers.read_with_ai(runtime, text, page.url)
    except manual_offers.ReadProblem as exc:
        raise SendProblem(exc.message) from exc
    draft.description = text
    return draft


async def _fill(runtime: Runtime, offer_id: int, draft: manual_offers.Draft, path: str) -> Sent:
    filled = await manual_offers.fill(runtime, offer_id, draft)
    if "description" in filled:
        await run_filter(runtime)
    score, label = await _score(runtime, offer_id, "description" in filled)
    log.info("extension_offer_filled", offer=offer_id, path=path, fields=filled)
    return Sent(outcome="filled", offer_id=offer_id, score=score, label=label, filled=filled)


async def _add(runtime: Runtime, draft: manual_offers.Draft, *, separate: bool) -> Sent:
    try:
        offer_id = await manual_offers.add(runtime, draft, separate=separate)
    except manual_offers.ReadProblem as exc:
        raise SendProblem(exc.message, limit=True) from exc
    score, label = await _score(runtime, offer_id, True)
    log.info("extension_offer_added", offer=offer_id, read_by=draft.read_by)
    return Sent(outcome="added", offer_id=offer_id, score=score, label=label)


async def send(
    runtime: Runtime,
    page: Page,
    choice: Literal["fill", "new"] | None = None,
    offer_id: int | None = None,
) -> Sent:
    """L'annonce envoyée par l'extension. `choice` : la réponse à « C'est bien cette offre ? »
    (« fill » avec l'id montré, ou « new »)."""
    draft = await _draft(runtime, page)
    linked = await _same_link(runtime, page.url)
    if linked is not None:
        return await _fill(runtime, linked, draft, "lien")
    norm = normalize_offer(draft.title, draft.company, draft.location)
    async with runtime.sessionmaker() as session:
        similar = await manual_offers.same_offer(session, norm)
    if similar is not None:
        if choice is None:
            log.info("extension_offer_to_confirm", offer=similar)
            return Sent(outcome="confirm", known=await _known(runtime, similar))
        if choice == "fill":
            # L'id du client doit être celui qu'on vient de retrouver (relu sous la RLS) :
            # jamais un rattachement à une autre offre.
            if offer_id != similar:
                raise ChoiceMismatch
            return await _fill(runtime, similar, draft, "titre")
        return await _add(runtime, draft, separate=True)
    return await _add(runtime, draft, separate=False)
