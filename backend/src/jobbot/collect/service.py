"""Collecte des alertes : boîte IMAP → journal `searches` → offres dédoublonnées.

Idempotent : un e-mail déjà connu (même Message-ID) est ignoré, et une offre n'est liée
qu'une fois à une alerte. Relancer la collecte ne crée donc aucun doublon.
"""

import asyncio
import hashlib
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.filter import canton_of
from jobbot.core.normalize import normalize_offer
from jobbot.db.models import Offer, OfferLink, OfferSighting, ParseStatus, Search, Source
from jobbot.log import get_logger
from jobbot.mail.imap import FetchedEmail, ImapMailbox, MailboxError
from jobbot.mail.message import ParsedEmail, parse_email
from jobbot.metrics import COLLECT_EMAILS, COLLECT_OFFERS, IMAP_ERRORS
from jobbot.runtime import Runtime
from jobbot.settings import Settings
from jobbot.sources.base import ParsedAlert, RawOffer
from jobbot.sources.registry import detect_source, find_parser

log = get_logger(__name__)

# Nombre maximal d'e-mails téléchargés par collecte ; le reste passe à la suivante.
MAX_EMAILS_PER_RUN = 200


class Mailbox(Protocol):
    """Ce que la collecte attend d'une boîte aux lettres (ImapMailbox, ou un faux en test)."""

    def fetch_since(
        self, since: date, *, limit: int, skip_message_ids: Callable[[set[str]], set[str]]
    ) -> list[FetchedEmail]: ...


MailboxFactory = Callable[[Settings], Mailbox]
# Remplacée dans les tests par une fausse boîte en mémoire.
mailbox_factory: MailboxFactory = ImapMailbox.from_settings


@dataclass
class CollectResult:
    configured: bool = True
    fetched: int = 0
    new_searches: int = 0
    new_offers: int = 0


def raw_key(email: ParsedEmail) -> str:
    digest = hashlib.sha256(email.message_id.encode()).hexdigest()[:32]
    return f"emails/{email.received_at:%Y/%m}/{digest}.eml"


def _since(settings: Settings) -> date:
    """Toujours toute la fenêtre JOBBOT_IMAP_BACKFILL_DAYS, et non « depuis la dernière
    collecte » : un e-mail ancien peut entrer dans le dossier plus tard (libellé posé après
    coup, filtre ajouté). Les e-mails déjà connus sont écartés par leur Message-ID avant
    téléchargement, donc relire la fenêtre ne coûte que la lecture des en-têtes."""
    return (datetime.now(UTC) - timedelta(days=settings.imap_backfill_days)).date()


async def _known_message_ids(runtime: Runtime, ids: set[str]) -> set[str]:
    if not ids:
        return set()
    async with runtime.sessionmaker() as session:
        rows = await session.scalars(select(Search.message_id).where(Search.message_id.in_(ids)))
        return set(rows)


def _analyse(email: ParsedEmail) -> tuple[Source, ParseStatus, str | None, ParsedAlert, str | None]:
    """(site, statut, version de l'analyseur, alerte, erreur)."""
    parser = find_parser(email)
    if parser is None:
        return detect_source(email), ParseStatus.UNRECOGNIZED, None, ParsedAlert(None, []), None
    try:
        alert = parser.parse(email)
    except Exception as exc:
        log.warning("parser_failed", source=parser.source.value, error=type(exc).__name__)
        error = f"{type(exc).__name__}: {exc}"[:500]
        return parser.source, ParseStatus.FAILED, parser.version, ParsedAlert(None, []), error
    status = ParseStatus.PARSED if alert.offers else ParseStatus.EMPTY
    return parser.source, status, parser.version, alert, None


async def _find_offer(
    session: AsyncSession, source: Source, raw: RawOffer, fingerprint: str
) -> int | None:
    if raw.external_id:
        offer_id = await session.scalar(
            select(OfferLink.offer_id).where(
                OfferLink.source == source, OfferLink.external_id == raw.external_id
            )
        )
        if offer_id is not None:
            return offer_id
    return await session.scalar(select(Offer.id).where(Offer.fingerprint == fingerprint))


async def ingest_offers(
    session: AsyncSession, search: Search, source: Source, offers: list[RawOffer]
) -> int:
    """Rattache les offres à l'alerte ; renvoie le nombre d'offres nouvelles."""
    new_count = 0
    seen_at = search.received_at
    for position, raw in enumerate(offers):
        norm = normalize_offer(raw.title, raw.company, raw.location)
        offer_id = await _find_offer(session, source, raw, norm.fingerprint)
        is_new = False
        if offer_id is None:
            offer_id = await session.scalar(
                insert(Offer)
                .values(
                    fingerprint=norm.fingerprint,
                    title=raw.title.strip(),
                    company=raw.company,
                    location=raw.location,
                    rate_min=norm.rate_min,
                    rate_max=norm.rate_max,
                    canton=canton_of(raw.location),
                    snippet=raw.snippet,
                    first_seen_at=seen_at,
                    last_seen_at=seen_at,
                )
                .on_conflict_do_nothing(index_elements=["fingerprint"])
                .returning(Offer.id)
            )
            if offer_id is None:  # créée entre-temps par une autre collecte
                offer_id = await _find_offer(session, source, raw, norm.fingerprint)
                assert offer_id is not None
            else:
                is_new = True

        sighted = await session.scalar(
            insert(OfferSighting)
            .values(offer_id=offer_id, search_id=search.id, position=position, is_first=is_new)
            .on_conflict_do_nothing()
            .returning(OfferSighting.offer_id)
        )
        if sighted is not None and not is_new:
            offer = await session.get_one(Offer, offer_id)
            offer.seen_count += 1
            offer.first_seen_at = min(offer.first_seen_at, seen_at)
            offer.last_seen_at = max(offer.last_seen_at, seen_at)

        await session.execute(
            insert(OfferLink)
            .values(offer_id=offer_id, source=source, external_id=raw.external_id, url=raw.url)
            .on_conflict_do_nothing()
        )
        if is_new:
            new_count += 1
        COLLECT_OFFERS.labels(source=source.value, result="new" if is_new else "duplicate").inc()
    return new_count


async def ingest_email(
    runtime: Runtime, fetched: FetchedEmail, run_id: uuid.UUID | None
) -> Search | None:
    """Enregistre un e-mail et ses offres. None s'il était déjà connu."""
    email = parse_email(fetched.raw, fallback_received=datetime.now(UTC))
    source, status, version, alert, error = _analyse(email)
    key = raw_key(email)
    runtime.storage.put(key, fetched.raw)

    async with runtime.sessionmaker.begin() as session:
        search_id = await session.scalar(
            insert(Search)
            .values(
                source=source,
                message_id=email.message_id,
                imap_uid=fetched.uid,
                received_at=email.received_at,
                subject=email.subject,
                alert_label=alert.alert_label,
                raw_key=key,
                parse_status=status,
                parser_version=version,
                error=error,
                results_count=len(alert.offers),
                job_run_id=run_id,
            )
            .on_conflict_do_nothing(index_elements=["message_id"])
            .returning(Search.id)
        )
        if search_id is None:
            return None
        search = await session.get_one(Search, search_id)
        search.new_offers_count = await ingest_offers(session, search, source, alert.offers)

    COLLECT_EMAILS.labels(source=source.value, parse_status=status.value).inc()
    log.info(
        "email_ingested",
        search_id=search.id,
        source=source.value,
        parse_status=status.value,
        offers=search.results_count,
        new_offers=search.new_offers_count,
    )
    return search


async def collect(runtime: Runtime, run_id: uuid.UUID | None = None) -> CollectResult:
    settings = runtime.settings
    if not settings.imap_configured:
        log.info("collect_not_configured")
        return CollectResult(configured=False)

    since = _since(settings)

    loop = asyncio.get_running_loop()

    def known(ids: set[str]) -> set[str]:
        # Appelé depuis le thread IMAP : la requête est renvoyée sur la boucle asyncio.
        return asyncio.run_coroutine_threadsafe(_known_message_ids(runtime, ids), loop).result()

    mailbox = mailbox_factory(settings)
    try:
        emails = await asyncio.to_thread(
            mailbox.fetch_since, since, limit=MAX_EMAILS_PER_RUN, skip_message_ids=known
        )
    except MailboxError as exc:
        IMAP_ERRORS.labels(kind=exc.kind).inc()
        raise

    result = CollectResult(fetched=len(emails))
    for fetched in emails:
        search = await ingest_email(runtime, fetched, run_id)
        if search is not None:
            result.new_searches += 1
            result.new_offers += search.new_offers_count
    log.info(
        "collect_finished",
        since=since.isoformat(),
        fetched=result.fetched,
        new_searches=result.new_searches,
        new_offers=result.new_offers,
    )
    return result


@dataclass
class ReparseResult:
    examined: int = 0
    updated: int = 0
    new_offers: int = 0
    missing_raw: int = 0


async def reparse(runtime: Runtime, *, source: Source | None = None) -> ReparseResult:
    """Réanalyse les copies brutes stockées, sans retourner dans la boîte.

    Ne touche que les alertes dont le résultat change : analyseur nouveau ou corrigé
    (version différente), ou alerte jusqu'ici non reconnue ou en échec. Les offres déjà
    rattachées ne sont pas dupliquées.
    """
    result = ReparseResult()
    query = select(Search.id).order_by(Search.received_at, Search.id)
    if source is not None:
        query = query.where(Search.source == source)
    async with runtime.sessionmaker() as session:
        ids = list(await session.scalars(query))

    for search_id in ids:
        result.examined += 1
        async with runtime.sessionmaker.begin() as session:
            search = await session.get_one(Search, search_id)
            try:
                raw = runtime.storage.get(search.raw_key)
            except FileNotFoundError:
                result.missing_raw += 1
                continue
            email = parse_email(raw, fallback_received=search.received_at)
            new_source, status, version, alert, error = _analyse(email)
            unchanged = version == search.parser_version and status == search.parse_status
            if unchanged or (version is None and status == ParseStatus.UNRECOGNIZED):
                continue
            search.source = new_source
            search.parse_status = status
            search.parser_version = version
            search.alert_label = alert.alert_label
            search.error = error
            search.results_count = len(alert.offers)
            created = await ingest_offers(session, search, new_source, alert.offers)
            search.new_offers_count += created
            result.updated += 1
            result.new_offers += created
    log.info(
        "reparse_finished",
        examined=result.examined,
        updated=result.updated,
        new_offers=result.new_offers,
        missing_raw=result.missing_raw,
    )
    return result
