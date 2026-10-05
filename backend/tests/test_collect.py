from collections.abc import AsyncIterator, Callable, Iterator
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select, text, update

from jobbot.api.app import create_app
from jobbot.collect import service
from jobbot.db.models import EnrichStatus, JobRun, Offer, OfferLink, OfferSighting, Search, Source
from jobbot.mail.imap import FetchedEmail, MailboxError
from jobbot.runtime import Runtime
from jobbot.settings import Settings
from jobbot.sources import registry as sources
from jobbot.worker.jobs import JOBS, execute

from .conftest import make_settings
from .emails import LineParser, make_email

T0 = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)


class FakeMailbox:
    """Boîte en mémoire : renvoie les e-mails dont le Message-ID n'est pas déjà connu."""

    def __init__(self) -> None:
        self.emails: list[tuple[str, bytes]] = []
        self.since_calls: list[date] = []
        self.error: MailboxError | None = None

    def add(self, raw: bytes, message_id: str) -> None:
        self.emails.append((message_id, raw))

    def fetch_since(
        self,
        since: date,
        *,
        limit: int,
        skip_message_ids: Callable[[set[str]], set[str]],
        newest_first: bool = False,
    ) -> list[FetchedEmail]:
        self.since_calls.append(since)
        if self.error:
            raise self.error
        known = skip_message_ids({mid for mid, _ in self.emails})
        fresh = [(i, raw) for i, (mid, raw) in enumerate(self.emails, 1) if mid not in known]
        return [FetchedEmail(uid=i, raw=raw) for i, raw in fresh[:limit]]


@pytest.fixture
def mailbox(monkeypatch: pytest.MonkeyPatch) -> FakeMailbox:
    box = FakeMailbox()
    monkeypatch.setattr(service, "mailbox_factory", lambda _settings: box)
    return box


@pytest.fixture
def parsers(monkeypatch: pytest.MonkeyPatch) -> dict[Source, LineParser]:
    registered = {
        Source.JOBUP: LineParser(source=Source.JOBUP, domain="jobup.ch"),
        Source.INDEED: LineParser(source=Source.INDEED, domain="indeed.com"),
    }
    monkeypatch.setattr(sources, "PARSERS", list(registered.values()))
    return registered


@pytest.fixture
def imap_settings(tmp_path: Path) -> Settings:
    return make_settings(
        imap_user="alertes@example.com",
        imap_password="secret-de-test",
        storage_path=tmp_path,
    )


@pytest.fixture
async def collect_runtime(imap_settings: Settings) -> AsyncIterator[Runtime]:
    runtime = Runtime.create(imap_settings)
    async with runtime.engine.begin() as conn:
        await conn.execute(text("TRUNCATE searches, offers, job_runs CASCADE"))
    yield runtime
    await runtime.dispose()


async def _count(runtime: Runtime, model: type) -> int:
    async with runtime.sessionmaker() as session:
        return await session.scalar(select(func.count()).select_from(model)) or 0


async def test_not_configured_is_a_quiet_success(runtime: Runtime, mailbox: FakeMailbox) -> None:
    result = await service.collect(runtime)
    assert result.configured is False
    assert mailbox.since_calls == []


@pytest.mark.usefixtures("parsers")
async def test_collect_twice_creates_no_duplicates(
    collect_runtime: Runtime, mailbox: FakeMailbox, tmp_path: Path, imap_settings: Settings
) -> None:
    mailbox.add(
        make_email(
            message_id="<a1@jobup.ch>",
            sender="alerts@jobup.ch",
            received_at=T0,
            offers=[
                (
                    "Ingénieur système (h/f) 80-100%",
                    "Acme SA",
                    "1003 Lausanne",
                    "https://j/1",
                    "J1",
                ),
                ("Administrateur réseau", "Globex AG", "Zürich", "https://j/2", "J2"),
            ],
        ),
        "<a1@jobup.ch>",
    )
    first = await service.collect(collect_runtime)
    second = await service.collect(collect_runtime)

    assert (first.fetched, first.new_searches, first.new_offers) == (1, 1, 2)
    assert (second.fetched, second.new_searches, second.new_offers) == (0, 0, 0)
    assert await _count(collect_runtime, Search) == 1
    assert await _count(collect_runtime, Offer) == 2

    async with collect_runtime.sessionmaker() as session:
        search = await session.scalar(select(Search))
        offer = await session.scalar(select(Offer).where(Offer.company == "Acme SA"))
    assert search is not None and offer is not None
    assert (search.source, search.parse_status, search.results_count) == ("jobup", "parsed", 2)
    assert search.new_offers_count == 2
    assert (offer.rate_min, offer.rate_max, offer.status) == (80, 100, "new")
    assert (tmp_path / search.raw_key).read_bytes().startswith(b"From:")
    # Chaque passage relit toute la fenêtre : un e-mail étiqueté après coup est rattrapé.
    expected = (datetime.now(UTC) - timedelta(days=imap_settings.imap_backfill_days)).date()
    assert mailbox.since_calls == [expected, expected]


@pytest.mark.usefixtures("parsers")
async def test_same_offer_on_two_sites(collect_runtime: Runtime, mailbox: FakeMailbox) -> None:
    mailbox.add(
        make_email(
            message_id="<a1@jobup.ch>",
            sender="alerts@jobup.ch",
            received_at=T0,
            offers=[
                ("Ingénieur système (h/f)", "Acme SA", "1003 Lausanne", "https://jobup/1", "J1")
            ],
        ),
        "<a1@jobup.ch>",
    )
    mailbox.add(
        make_email(
            message_id="<b1@indeed.com>",
            sender="alert@indeed.com",
            received_at=T0 + timedelta(hours=3),
            offers=[("Ingenieur Systeme H/F", "ACME", "Lausanne, VD", "https://indeed/1", "K1")],
        ),
        "<b1@indeed.com>",
    )
    await service.collect(collect_runtime)

    async with collect_runtime.sessionmaker() as session:
        [offer] = (await session.scalars(select(Offer))).all()
        links = (await session.scalars(select(OfferLink).order_by(OfferLink.id))).all()
        sightings = (
            await session.scalars(select(OfferSighting).order_by(OfferSighting.search_id))
        ).all()
    assert offer.seen_count == 2
    assert offer.last_seen_at == T0 + timedelta(hours=3)
    assert [(link.source, link.external_id) for link in links] == [
        ("jobup", "J1"),
        ("indeed", "K1"),
    ]
    assert [s.is_first for s in sightings] == [True, False]


@pytest.mark.usefixtures("parsers")
async def test_expired_offer_seen_again_is_visible(
    collect_runtime: Runtime, mailbox: FakeMailbox
) -> None:
    offer_line = ("Ingénieur système (h/f)", "Acme SA", "1003 Lausanne", "https://jobup/1", "J1")
    mailbox.add(
        make_email(
            message_id="<a1@jobup.ch>",
            sender="alerts@jobup.ch",
            received_at=T0,
            offers=[offer_line],
        ),
        "<a1@jobup.ch>",
    )
    await service.collect(collect_runtime)
    async with collect_runtime.sessionmaker.begin() as session:
        await session.execute(
            update(Offer).values(
                expired_at=T0 + timedelta(hours=1),
                expiry_source="page",
                enrich_status=EnrichStatus.EXPIRED,
                enrich_attempts=1,
            )
        )
    mailbox.add(
        make_email(
            message_id="<a2@jobup.ch>",
            sender="alerts@jobup.ch",
            received_at=T0 + timedelta(days=2),
            offers=[offer_line],
        ),
        "<a2@jobup.ch>",
    )
    await service.collect(collect_runtime)
    async with collect_runtime.sessionmaker() as session:
        [offer] = (await session.scalars(select(Offer))).all()
    assert (offer.expired_at, offer.expiry_source) == (None, None)
    assert (offer.enrich_status, offer.enrich_attempts) == (EnrichStatus.PENDING, 0)


@pytest.mark.usefixtures("parsers")
async def test_offer_flagged_expired_by_kevin_stays_expired(
    collect_runtime: Runtime, mailbox: FakeMailbox
) -> None:
    offer_line = ("Ingénieur système (h/f)", "Acme SA", "1003 Lausanne", "https://jobup/1", "J1")
    for n, received in enumerate((T0, T0 + timedelta(days=2)), 1):
        if n == 2:
            async with collect_runtime.sessionmaker.begin() as session:
                await session.execute(
                    update(Offer).values(
                        expired_at=T0 + timedelta(hours=1),
                        expiry_source="manual",
                        expiry_override="expired",
                    )
                )
        mailbox.add(
            make_email(
                message_id=f"<a{n}@jobup.ch>",
                sender="alerts@jobup.ch",
                received_at=received,
                offers=[offer_line],
            ),
            f"<a{n}@jobup.ch>",
        )
        await service.collect(collect_runtime)
    async with collect_runtime.sessionmaker() as session:
        [offer] = (await session.scalars(select(Offer))).all()
    assert offer.expiry_source == "manual" and offer.expired_at is not None


@pytest.mark.usefixtures("parsers")
async def test_site_identifier_wins_over_changed_title(
    collect_runtime: Runtime, mailbox: FakeMailbox
) -> None:
    for i, title in enumerate(("Ingénieur système", "Ingénieur système senior")):
        mid = f"<a{i}@jobup.ch>"
        mailbox.add(
            make_email(
                message_id=mid,
                sender="alerts@jobup.ch",
                received_at=T0 + timedelta(days=i),
                offers=[(title, "Acme SA", "Lausanne", f"https://j/{i}", "J1")],
            ),
            mid,
        )
    await service.collect(collect_runtime)
    assert await _count(collect_runtime, Offer) == 1


@pytest.mark.usefixtures("parsers")
async def test_unknown_and_unparsed_emails_are_kept(
    collect_runtime: Runtime, mailbox: FakeMailbox
) -> None:
    mailbox.add(
        make_email(message_id="<p@pub.example>", sender="news@pub.example", received_at=T0),
        "<p@pub.example>",
    )
    mailbox.add(
        make_email(message_id="<j@job-room.ch>", sender="noreply@job-room.ch", received_at=T0),
        "<j@job-room.ch>",
    )
    await service.collect(collect_runtime)
    async with collect_runtime.sessionmaker() as session:
        rows = (await session.scalars(select(Search).order_by(Search.message_id))).all()
    assert [(s.source, s.parse_status) for s in rows] == [
        ("jobroom", "unrecognized"),
        ("unknown", "unrecognized"),
    ]


async def test_failing_parser_is_recorded(
    collect_runtime: Runtime, mailbox: FakeMailbox, parsers: dict[Source, LineParser]
) -> None:
    parsers[Source.JOBUP].fail = True
    mailbox.add(
        make_email(message_id="<x@jobup.ch>", sender="alerts@jobup.ch", received_at=T0),
        "<x@jobup.ch>",
    )
    await service.collect(collect_runtime)
    async with collect_runtime.sessionmaker() as session:
        search = await session.scalar(select(Search))
    assert search is not None
    assert (search.parse_status, search.parser_version) == ("failed", "test-1")
    assert search.error == "ValueError: format inattendu"


async def test_auth_error_fails_the_job_without_secret(
    collect_runtime: Runtime, mailbox: FakeMailbox
) -> None:
    mailbox.error = MailboxError("auth", "authentification IMAP refusée")
    with pytest.raises(MailboxError):
        await execute(collect_runtime, "collect")
    async with collect_runtime.sessionmaker() as session:
        run = await session.scalar(select(JobRun).where(JobRun.job == "collect"))
    assert run is not None and run.status == "failure"
    assert run.error is not None and "secret-de-test" not in run.error


@pytest.mark.usefixtures("parsers")
async def test_collect_job_records_counts(collect_runtime: Runtime, mailbox: FakeMailbox) -> None:
    mailbox.add(
        make_email(
            message_id="<a@jobup.ch>",
            sender="alerts@jobup.ch",
            received_at=T0,
            offers=[("Admin", "Acme", "Lausanne", "https://j/1")],
        ),
        "<a@jobup.ch>",
    )
    assert await execute(collect_runtime, "collect")
    async with collect_runtime.sessionmaker() as session:
        run = await session.scalar(select(JobRun).where(JobRun.job == "collect"))
        search = await session.scalar(select(Search))
    assert run is not None and (run.items_in, run.items_out) == (1, 1)
    assert search is not None and search.job_run_id == run.run_id
    # Le filtre est enchaîné après une collecte qui a trouvé de nouvelles offres.
    async with collect_runtime.sessionmaker() as session:
        filter_run = await session.scalar(select(JobRun).where(JobRun.job == "filter"))
        offer = await session.scalar(select(Offer))
    assert filter_run is not None and filter_run.status == "success"
    assert offer is not None and offer.status == "to_review"


@pytest.mark.parametrize(
    ("utc_time", "active"),
    [
        (datetime(2026, 7, 1, 4, 0, tzinfo=UTC), False),  # 6 h en été
        (datetime(2026, 7, 1, 6, 0, tzinfo=UTC), True),  # 8 h en été
        (datetime(2026, 7, 1, 20, 0, tzinfo=UTC), False),  # 22 h en été
        (datetime(2026, 1, 15, 6, 0, tzinfo=UTC), True),  # 7 h en hiver
        (datetime(2026, 1, 15, 20, 0, tzinfo=UTC), True),  # 21 h en hiver
        (datetime(2026, 1, 15, 22, 0, tzinfo=UTC), False),  # 23 h en hiver
    ],
)
def test_collect_active_hours_are_swiss_time(utc_time: datetime, active: bool) -> None:
    assert JOBS["collect"].is_active_at(utc_time) is active


# --- API -----------------------------------------------------------------------------


@pytest.fixture
async def api(collect_runtime: Runtime, imap_settings: Settings) -> AsyncIterator[AsyncClient]:
    app = create_app(imap_settings, collect_runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def clean_queue(settings: Settings) -> Iterator[None]:
    from sqlalchemy import create_engine

    engine = create_engine(settings.sqlalchemy_url)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM procrastinate_jobs"))
    yield
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM procrastinate_jobs"))
    engine.dispose()


@pytest.mark.usefixtures("parsers")
async def test_api_journal_and_offers(
    api: AsyncClient, collect_runtime: Runtime, mailbox: FakeMailbox
) -> None:
    mailbox.add(
        make_email(
            message_id="<a@jobup.ch>",
            sender="alerts@jobup.ch",
            received_at=T0,
            offers=[("Admin 80%", "Acme", "Lausanne", "https://j/1", "J1")],
        ),
        "<a@jobup.ch>",
    )
    mailbox.add(
        make_email(message_id="<p@pub.example>", sender="news@pub.example", received_at=T0),
        "<p@pub.example>",
    )
    await service.collect(collect_runtime)

    page = (await api.get("/api/searches")).json()
    assert page["total"] == 2
    filtered = (await api.get("/api/searches", params={"parse_status": "parsed"})).json()
    assert [s["source"] for s in filtered["items"]] == ["jobup"]

    detail = (await api.get(f"/api/searches/{filtered['items'][0]['id']}")).json()
    [offer] = detail["offers"]
    assert offer["is_first"] is True
    assert offer["links"] == [{"source": "jobup", "url": "https://j/1"}]
    assert (offer["rate_min"], offer["rate_max"]) == (80, 80)

    offers = (await api.get("/api/offers")).json()
    assert offers["total"] == 1 and offers["items"][0]["title"] == "Admin 80%"
    popular = (await api.get("/api/offers", params={"sort": "popular"})).json()
    assert popular["items"][0]["title"] == "Admin 80%"
    assert (await api.get("/api/offers", params={"sort": "autre"})).status_code == 422
    assert (await api.get("/api/searches/999999")).status_code == 404


@pytest.mark.usefixtures("clean_queue")
async def test_api_collect_button_queues_once(api: AsyncClient) -> None:
    first = await api.post("/api/collect")
    second = await api.post("/api/collect")
    assert (first.status_code, first.json()) == (202, {"result": "queued"})
    assert second.json() == {"result": "already_queued"}


async def test_api_collect_button_requires_configuration(client: AsyncClient) -> None:
    response = await client.post("/api/collect")
    assert response.status_code == 409


async def test_status_reports_collect(
    api: AsyncClient, collect_runtime: Runtime, mailbox: FakeMailbox
) -> None:
    mailbox.error = MailboxError("connection", "connexion IMAP impossible (TimeoutError)")
    with pytest.raises(MailboxError):
        await execute(collect_runtime, "collect")
    body = (await api.get("/api/status")).json()["collect"]
    assert body["configured"] is True
    assert body["last_success_at"] is None
    assert body["last_error"] == "MailboxError: connexion IMAP impossible (TimeoutError)"


async def test_reparse_after_new_parser(
    collect_runtime: Runtime, mailbox: FakeMailbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sources, "PARSERS", [])
    mailbox.add(
        make_email(
            message_id="<r@jobup.ch>",
            sender="alerts@jobup.ch",
            received_at=T0,
            offers=[("Admin", "Acme", "Lausanne", "https://j/1", "J1")],
        ),
        "<r@jobup.ch>",
    )
    await service.collect(collect_runtime)
    async with collect_runtime.sessionmaker() as session:
        search = await session.scalar(select(Search))
    assert search is not None and search.parse_status == "unrecognized"

    monkeypatch.setattr(sources, "PARSERS", [LineParser(source=Source.JOBUP, domain="jobup.ch")])
    first = await service.reparse(collect_runtime)
    again = await service.reparse(collect_runtime)

    assert (first.updated, first.new_offers) == (1, 1)
    assert (again.updated, again.new_offers) == (0, 0)
    async with collect_runtime.sessionmaker() as session:
        search = await session.scalar(select(Search))
    assert search is not None
    assert (search.parse_status, search.parser_version, search.new_offers_count) == (
        "parsed",
        "test-1",
        1,
    )
    assert await _count(collect_runtime, Offer) == 1
