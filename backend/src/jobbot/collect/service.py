"""Collecte des alertes : boîte IMAP → journal `searches` → offres dédoublonnées.

Idempotent : un e-mail déjà connu (même Message-ID) est ignoré, et une offre n'est liée
qu'une fois à une alerte. Relancer la collecte ne crée donc aucun doublon.
"""

import asyncio
import hashlib
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Protocol

from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot import accounts
from jobbot.collect import topic
from jobbot.core.filter import canton_of
from jobbot.core.normalize import normalize_offer
from jobbot.db.models import (
    PUBLIC_SEARCH_PREFIX,
    EnrichStatus,
    Offer,
    OfferLink,
    OfferSighting,
    ParseStatus,
    Search,
    SiteReader,
)
from jobbot.llm import alert as alert_llm
from jobbot.log import get_logger
from jobbot.mail import addresses, site_codes
from jobbot.mail.codes import find_code
from jobbot.mail.confirm import confirmation_link, open_confirmation
from jobbot.mail.imap import FetchedEmail, ImapMailbox, MailboxError
from jobbot.mail.message import ParsedEmail, parse_email
from jobbot.metrics import COLLECT_EMAILS, COLLECT_OFFERS, IMAP_ERRORS
from jobbot.notify import service as notify
from jobbot.runtime import Runtime
from jobbot.settings import Settings
from jobbot.sources.base import ParsedAlert, RawOffer
from jobbot.sources.registry import detect_source, find_parser
from jobbot.sources.sites import SiteData, load_sites, match_site, read_with_ai

log = get_logger(__name__)

# Nombre maximal d'e-mails téléchargés par collecte ; le reste passe à la suivante.
MAX_EMAILS_PER_RUN = 200


class Mailbox(Protocol):
    """Ce que la collecte attend d'une boîte aux lettres (ImapMailbox, ou un faux en test)."""

    def fetch_since(
        self, since: date, *, limit: int, skip_message_ids: Callable[[set[str]], set[str]]
    ) -> list[FetchedEmail]: ...


class GuestMailbox(Mailbox, Protocol):
    """La boîte des invités (docs/113) : lue comme l'autre, puis vidée de ce qui est copié."""

    def clean(self, *, known: Callable[[set[str]], set[str]], before: date) -> int: ...


MailboxFactory = Callable[[Settings], Mailbox]
# Remplacées dans les tests par des fausses boîtes en mémoire.
mailbox_factory: MailboxFactory = ImapMailbox.from_settings
guest_mailbox_factory: Callable[[Settings], GuestMailbox] = ImapMailbox.guest_from_settings


@dataclass
class CollectResult:
    configured: bool = True
    fetched: int = 0
    new_searches: int = 0
    new_offers: int = 0
    # Les comptes qui ont reçu de nouvelles offres : leurs tâches suivent (filtre, notation).
    accounts: set[int] = field(default_factory=set)
    # E-mails adressés à un code inconnu (compte supprimé) : pas rangés.
    unrouted: int = 0
    # Codes de vérification reçus (docs/112) : le relevé rapide s'arrête au premier.
    codes: int = 0


def raw_key(email: ParsedEmail) -> str:
    # Un dossier par compte (docs/65 §1) ; les e-mails d'avant gardent leur emplacement.
    digest = hashlib.sha256(email.message_id.encode()).hexdigest()[:32]
    return f"accounts/{accounts.current()}/emails/{email.received_at:%Y/%m}/{digest}.eml"


def _since(settings: Settings) -> date:
    """Toujours toute la fenêtre JOBBOT_IMAP_BACKFILL_DAYS, et non « depuis la dernière
    collecte » : un e-mail ancien peut entrer dans le dossier plus tard (libellé posé après
    coup, filtre ajouté). Les e-mails déjà connus sont écartés par leur Message-ID avant
    téléchargement, donc relire la fenêtre ne coûte que la lecture des en-têtes."""
    return (datetime.now(UTC) - timedelta(days=settings.imap_backfill_days)).date()


# Gmail, qui confirme un transfert vers l'adresse jobA1 par un code (docs/116 §1).
GMAIL_DOMAINS = ("google.com", "gmail.com")


async def _known_message_ids(runtime: Runtime, ids: set[str]) -> set[str]:
    """Déjà rangés, dans n'importe quel compte (docs/65 §3) : la base ne rend que les ids."""
    if not ids:
        return set()
    async with runtime.sessionmaker() as session:
        rows = await session.scalars(select(func.collected_message_ids(list(ids))))
        return {str(r) for r in rows}


async def _analyse(
    runtime: Runtime, email: ParsedEmail, sites: list[SiteData]
) -> tuple[str, ParseStatus, str | None, ParsedAlert, str | None]:
    """(site, statut, version de l'analyseur, alerte, erreur)."""
    empty = ParsedAlert(None, [])
    site = match_site(sites, email)
    if site is not None and not site.active:
        return site.slug, ParseStatus.UNRECOGNIZED, None, empty, "site en pause"
    parser = find_parser(email)
    if parser is None:
        if site is not None and site.reader == SiteReader.AI:
            reading = await read_with_ai(runtime, email, site)
            version = (
                None if reading.status == ParseStatus.UNRECOGNIZED else alert_llm.PROMPT_VERSION
            )
            return site.slug, reading.status, version, reading.alert, reading.error
        source = site.slug if site is not None else detect_source(email)
        return source, ParseStatus.UNRECOGNIZED, None, empty, None
    try:
        alert = parser.parse(email)
    except Exception as exc:
        log.warning("parser_failed", source=parser.source, error=type(exc).__name__)
        error = f"{type(exc).__name__}: {exc}"[:500]
        return parser.source, ParseStatus.FAILED, parser.version, ParsedAlert(None, []), error
    status = ParseStatus.PARSED if alert.offers else ParseStatus.EMPTY
    return parser.source, status, parser.version, alert, None


async def _find_offer(
    session: AsyncSession, source: str, raw: RawOffer, fingerprint: str
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
    session: AsyncSession, search: Search, source: str, offers: list[RawOffer]
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
                    logo_url=raw.logo_url,
                    canton=canton_of(raw.location),
                    snippet=raw.snippet,
                    first_seen_at=seen_at,
                    seen_since=seen_at,
                    last_seen_at=seen_at,
                )
                .on_conflict_do_nothing(index_elements=["user_id", "fingerprint"])
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
            if raw.logo_url and not offer.logo_url:
                offer.logo_url = raw.logo_url
            if (
                offer.expired_at is not None
                and seen_at > offer.expired_at
                # Signalée expirée par Kevin : elle le reste.
                and offer.expiry_override != "expired"
            ):
                # Réapparue dans une alerte (docs/10 §1) : de nouveau visible ; une page jobup
                # introuvable sera relue.
                offer.expired_at = offer.expiry_source = None
                if offer.enrich_status == EnrichStatus.EXPIRED:
                    offer.enrich_status, offer.enrich_attempts = EnrichStatus.PENDING, 0

        await session.execute(
            insert(OfferLink)
            .values(offer_id=offer_id, source=source, external_id=raw.external_id, url=raw.url)
            .on_conflict_do_nothing()
        )
        if is_new:
            new_count += 1
        COLLECT_OFFERS.labels(source=source, result="new" if is_new else "duplicate").inc()
    return new_count


async def ingest_email(
    runtime: Runtime,
    fetched: FetchedEmail,
    run_id: uuid.UUID | None,
    email: ParsedEmail | None = None,
) -> Search | None:
    """Enregistre un e-mail et ses offres, dans le compte en cours. None s'il était connu."""
    email = email or parse_email(fetched.raw, fallback_received=datetime.now(UTC))
    async with runtime.sessionmaker() as session:
        sites = await load_sites(session)
    source, status, version, alert, error = await _analyse(runtime, email, sites)
    # Un code de vérification (docs/112) : montré au compte le temps de le recopier.
    found = find_code(email) if status != ParseStatus.PARSED else None
    # Le code de Gmail qui confirme un transfert vers l'adresse jobA1 (docs/116 §1).
    if found is not None and email.sender_domain in GMAIL_DOMAINS:
        source = "gmail"
    no_offer = status == ParseStatus.EMPTY or (status == ParseStatus.UNRECOGNIZED and not error)
    # « Confirmez votre alerte » : le lien, pour la page Alertes (docs/65 §3) ; ouvert par
    # jobA1 pour un site connu (docs/112 §4).
    confirm = confirmation_link(email) if no_offer and found is None else None
    confirmed_at = datetime.now(UTC) if confirm and await open_confirmation(confirm) else None
    # Ni alerte, ni code, ni confirmation : un message du site (bienvenue, mot de passe…) :
    # aucun analyseur ne le reconnaît, ou l'IA n'y a trouvé aucune offre. Une alerte reconnue
    # sans offre ce jour-là reste une alerte ; une alerte qui attend l'IA (plafond, pas de
    # clé) aussi : elle sera relue.
    unknown = status == ParseStatus.UNRECOGNIZED and not error
    read_empty = status == ParseStatus.EMPTY and version == alert_llm.PROMPT_VERSION
    message = confirm is None and (unknown or read_empty)
    kind = "code" if found else "message" if message else None
    key = raw_key(email)
    runtime.storage.put(key, fetched.raw)
    # Les recommandations du site : seulement celles du métier (docs/116 §3).
    offers = alert.offers
    if alert.recommended and offers:
        async with runtime.sessionmaker() as session:
            stems = await topic.trade_stems(session)
        offers = [raw for raw in offers if topic.on_topic(raw.title, stems)]

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
                results_count=len(offers),
                off_topic_count=len(alert.offers) - len(offers),
                job_run_id=run_id,
                confirm_url=confirm,
                confirmed_at=confirmed_at,
                kind=kind,
                code=found.code if found else None,
            )
            .on_conflict_do_nothing(index_elements=["user_id", "message_id"])
            .returning(Search.id)
        )
        if search_id is None:
            return None
        search = await session.get_one(Search, search_id)
        search.new_offers_count = await ingest_offers(session, search, source, offers)
        # La première alerte d'un site avec des offres (docs/121 §B.3) : la personne sait que
        # son alerte marche.
        first = (
            kind is None
            and status == ParseStatus.PARSED
            and offers
            and not await session.scalar(
                select(Search.id)
                .where(
                    Search.source == source,
                    Search.kind.is_(None),
                    Search.parse_status == ParseStatus.PARSED,
                    Search.results_count > 0,
                    Search.id != search.id,
                )
                .limit(1)
            )
        )

    COLLECT_EMAILS.labels(source=source, parse_status=status).inc()
    if first:
        name = next((site.name for site in sites if site.slug == source), source)
        count = len(offers)
        await notify.deliver(
            runtime,
            notify.Message(
                title=f"Première alerte de {name}",
                message=f"{name} t'a envoyé ses premières offres : {count}.",
                tags=["bell"],
            ),
            kind="first_alert",
            link="/candidatures/offres",
        )
    if found is not None:
        fallback = "Gmail" if source == "gmail" else source
        name = next((site.name for site in sites if site.slug == source), fallback)
        await site_codes.announce(runtime, name, found.code)
    log.info(
        "email_ingested",
        search_id=search.id,
        source=source,
        parse_status=status,
        offers=search.results_count,
        new_offers=search.new_offers_count,
    )
    return search


# Les e-mails sans compte (adresse inconnue, compte supprimé) quittent la boîte des invités
# au bout de 7 jours (docs/113).
GUEST_UNROUTED_KEPT = timedelta(days=7)


async def collect(runtime: Runtime, run_id: uuid.UUID | None = None) -> CollectResult:
    """Les deux boîtes : celle de l'exploitant (ses alertes, en lecture seule) et, si elle est
    réglée, celle des invités (docs/113), vidée de ce qui est copié dans jobA1."""
    settings = runtime.settings
    if not settings.imap_configured and not settings.guest_imap_configured:
        log.info("collect_not_configured")
        return CollectResult(configured=False)
    result = CollectResult()
    if settings.imap_configured:
        await _collect_box(runtime, mailbox_factory(settings), run_id, result, guest=False)
    if settings.guest_imap_configured:
        guest = guest_mailbox_factory(settings)
        await _collect_box(runtime, guest, run_id, result, guest=True)
        await _clean_guest_box(runtime, guest)
    return result


async def _collect_box(
    runtime: Runtime,
    mailbox: Mailbox,
    run_id: uuid.UUID | None,
    result: CollectResult,
    *,
    guest: bool,
) -> None:
    settings = runtime.settings
    since = _since(settings)

    loop = asyncio.get_running_loop()

    def known(ids: set[str]) -> set[str]:
        # Appelé depuis le thread IMAP : la requête est renvoyée sur la boucle asyncio.
        return asyncio.run_coroutine_threadsafe(_known_message_ids(runtime, ids), loop).result()

    try:
        emails = await asyncio.to_thread(
            mailbox.fetch_since, since, limit=MAX_EMAILS_PER_RUN, skip_message_ids=known
        )
    except MailboxError as exc:
        IMAP_ERRORS.labels(kind=exc.kind).inc()
        raise

    # Chaque e-mail va au compte de son adresse de destination (docs/65 §3).
    base = addresses.base_address(settings)
    domain = addresses.alert_domain(settings)
    async with runtime.sessionmaker.begin() as session:
        owner = await accounts.owner_id(session)
        codes = await addresses.recipients_map(session)
        active = set(await accounts.account_ids(session))
    result.fetched += len(emails)
    for fetched in emails:
        email = parse_email(fetched.raw, fallback_received=datetime.now(UTC))
        account = addresses.route(email.recipients, base, codes, owner, domain)
        # La boîte des invités n'est jamais à l'exploitant : un e-mail sans code d'invité n'y
        # est à personne (docs/113).
        if guest and account == owner:
            account = None
        if account is None or account not in active:
            # Code inconnu (compte supprimé) ou compte suspendu : l'e-mail n'est pas rangé.
            result.unrouted += 1
            log.info("email_not_routed", suspended=account is not None, guest_box=guest)
            continue
        with accounts.use(account):
            search = await ingest_email(runtime, fetched, run_id, email)
        if search is not None:
            result.new_searches += 1
            result.codes += search.kind == "code"
            result.new_offers += search.new_offers_count
            if search.new_offers_count:
                result.accounts.add(account)
    log.info(
        "collect_finished",
        since=since.isoformat(),
        guest_box=guest,
        fetched=len(emails),
        new_searches=result.new_searches,
        new_offers=result.new_offers,
    )


async def _clean_guest_box(runtime: Runtime, mailbox: GuestMailbox) -> None:
    """Vide la boîte des invités de ce qui est déjà copié dans un compte, et des e-mails sans
    compte de plus de 7 jours : personne n'a de raison de les y lire (docs/113)."""
    loop = asyncio.get_running_loop()

    def known(ids: set[str]) -> set[str]:
        return asyncio.run_coroutine_threadsafe(_known_message_ids(runtime, ids), loop).result()

    before = (datetime.now(UTC) - GUEST_UNROUTED_KEPT).date()
    try:
        removed = await asyncio.to_thread(mailbox.clean, known=known, before=before)
    except MailboxError as exc:
        IMAP_ERRORS.labels(kind=exc.kind).inc()
        raise
    log.info("guest_box_cleaned", removed=removed)


@dataclass
class ReparseResult:
    examined: int = 0
    updated: int = 0
    new_offers: int = 0
    missing_raw: int = 0


async def reparse(
    runtime: Runtime,
    *,
    source: str | None = None,
    parse_status: ParseStatus | None = None,
) -> ReparseResult:
    """Réanalyse les copies brutes stockées, sans retourner dans la boîte.

    Ne touche que les alertes dont le résultat change : analyseur nouveau ou corrigé
    (version différente), ou alerte jusqu'ici non reconnue ou en échec. Les offres déjà
    rattachées ne sont pas dupliquées.
    """
    result = ReparseResult()
    # Ni les recherches publiques de jobA1 (docs/104), sans e-mail, ni les codes (docs/112) ;
    # un message du site peut être une alerte mal lue : il est relu.
    query = (
        select(Search.id)
        .where(
            Search.message_id.not_like(f"{PUBLIC_SEARCH_PREFIX}%"),
            or_(Search.kind.is_(None), Search.kind == "message"),
        )
        .order_by(Search.received_at, Search.id)
    )
    if source is not None:
        query = query.where(Search.source == source)
    if parse_status is not None:
        query = query.where(Search.parse_status == parse_status)
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
            sites = await load_sites(session)
            new_source, status, version, alert, error = await _analyse(runtime, email, sites)
            unchanged = version == search.parser_version and status == search.parse_status
            if unchanged or (version is None and status == ParseStatus.UNRECOGNIZED):
                continue
            search.source = new_source
            search.parse_status = status
            search.parser_version = version
            search.alert_label = alert.alert_label
            search.error = error
            search.results_count = len(alert.offers)
            # Relue avec des offres : c'était une alerte, pas un message du site (docs/112).
            if alert.offers and search.kind == "message":
                search.kind = None
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
