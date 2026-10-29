"""Démo publique (docs/72) : réglage, garde-fou, lecture seule, jeu de données fictif.

Sur une base à part (`jobbot_demo_test`) : le remplissage vide les comptes, il ne doit pas
toucher la base des autres tests.
"""

from collections.abc import AsyncIterator, Iterator
from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import make_url

from jobbot import accounts, demo
from jobbot.api.app import create_app
from jobbot.db.models import Application, Draft, Evaluation, Offer, User
from jobbot.db.schema import upgrade
from jobbot.demo import data
from jobbot.demo.seed import next_thursday, seed, sent_day
from jobbot.runtime import Runtime
from jobbot.settings import ConfigError, load_settings

from .conftest import TEST_DATABASE_URL, make_settings

TODAY = date(2026, 10, 18)
# render_as_string(hide_password=False) : str() remplacerait le mot de passe par « *** ».
DEMO_DATABASE_URL = (
    make_url(TEST_DATABASE_URL)
    .set(database="jobbot_demo_test")
    .render_as_string(hide_password=False)
)


@pytest.fixture(scope="module")
def demo_database() -> Iterator[str]:
    url = make_url(DEMO_DATABASE_URL)
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.scalar(
            text("select 1 from pg_database where datname = :name"), {"name": url.database}
        )
        if not exists:
            conn.execute(text(f'create database "{url.database}"'))
    admin.dispose()
    engine = create_engine(DEMO_DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    engine.dispose()
    upgrade(make_settings(database_url=DEMO_DATABASE_URL))
    yield DEMO_DATABASE_URL


@pytest.fixture
async def demo_runtime(demo_database: str) -> AsyncIterator[Runtime]:
    rt = Runtime.create(make_settings(database_url=demo_database, demo=True))
    yield rt
    await rt.dispose()


@pytest.fixture
async def demo_admin(demo_database: str) -> AsyncIterator[Runtime]:
    """`jobbot demo-seed` : la commande du propriétaire des tables (docs/78 §3.1)."""
    rt = Runtime.create(make_settings(database_url=demo_database, demo=True), "admin")
    yield rt
    await rt.dispose()


def test_demo_refuses_ai_mail_and_ntfy(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValueError, match="JOBBOT_DEMO"):
        make_settings(demo=True, anthropic_api_key="sk-test")
    monkeypatch.setenv("JOBBOT_DATABASE_URL", DEMO_DATABASE_URL)
    monkeypatch.setenv("JOBBOT_DEMO", "true")
    monkeypatch.setenv("JOBBOT_NTFY_TOPIC", "sujet")
    with pytest.raises(ConfigError, match="JOBBOT_DEMO"):
        load_settings()


def test_dates_follow_the_day() -> None:
    assert next_thursday(TODAY) == date(2026, 10, 22)  # dimanche -> jeudi
    assert next_thursday(date(2026, 10, 22)) == date(2026, 10, 29)
    # Le mois en cours s'arrête la veille ; les précédents vont jusqu'à leur dernier jour.
    assert sent_day(TODAY, 0, 1.0) == date(2026, 10, 17)
    assert sent_day(TODAY, 1, 0.0) == date(2026, 9, 1)
    assert sent_day(TODAY, 1, 1.0) == date(2026, 9, 30)
    assert sent_day(date(2026, 1, 1), 0, 0.5) == date(2026, 1, 1)


async def test_seed_fills_a_believable_search(demo_runtime: Runtime, demo_admin: Runtime) -> None:
    count = await seed(demo_admin, TODAY)
    # Un deuxième passage repart de zéro : la démo est rejouée chaque nuit.
    assert await seed(demo_admin, TODAY) == count
    async with demo_admin.sessionmaker() as session:
        users = list(await session.scalars(select(User.username).order_by(User.id)))
        assert users == [accounts.PLACEHOLDER_USERNAME, demo.DEMO_USERNAME]
        visitor = await demo.account(session)
    with accounts.use(visitor):
        async with demo_runtime.sessionmaker() as session:
            months = dict(
                (
                    await session.execute(
                        select(Application.orp_month, func.count()).group_by(Application.orp_month)
                    )
                ).all()
            )
            # Aucune offre fictive n'est prise pour le doublon d'une autre.
            duplicates = await session.scalar(
                select(func.count()).select_from(Offer).where(Offer.duplicate_of.is_not(None))
            )
            filtered = list(
                await session.scalars(
                    select(Offer.title).where(Offer.status == "filtered_out").order_by(Offer.title)
                )
            )
            reasons = {
                r["rule"]
                for e in await session.scalars(
                    select(Evaluation).where(Evaluation.filter_passed.is_(False))
                )
                for r in e.filter_reasons
            }
            upcoming = await session.scalar(select(func.max(Application.interview_at)))
            # Une lettre déjà rédigée pour les deux meilleures offres à examiner (docs/126 §5).
            showcased = list(
                await session.scalars(
                    select(Offer.title)
                    .join(Draft, Draft.offer_id == Offer.id)
                    .where(Draft.kind == "letter", Offer.status == "to_review")
                    .order_by(Offer.title)
                )
            )
            notes = {
                title: (why, level)
                for title, why, level in (
                    await session.execute(
                        select(Offer.title, Evaluation.why, Evaluation.level)
                        .join(Evaluation, Evaluation.offer_id == Offer.id)
                        .where(Evaluation.score.is_not(None))
                    )
                ).all()
            }
    # La phrase « pourquoi » suit l'offre (docs/121 §C.1) ; le niveau, seulement là où
    # l'annonce le dit (§C.2).
    assert notes["Data Engineer"] == (
        "Le poste vise la donnée (Spark, SQL). Ton parcours cloud colle en partie.",
        None,
    )
    assert notes["Cloud Engineer (Azure)"][0] == ("Il manque Bicep. Azure et PowerShell collent.")
    assert {t for t, (_, level) in notes.items() if level} == {"SRE junior"}
    assert all(why and len(why) <= 140 for why, _ in notes.values())
    assert len(showcased) == 2
    assert count == sum(months.values())
    assert months["2026-10"] == 6 and months["2026-09"] == 10 and months["2026-08"] == 10
    assert months["2026-07"] == 10
    assert duplicates == 0
    assert filtered == ["Ingénieur·e cloud à 40 %", "Platform Engineer", "Stage DevOps"]
    assert reasons == {"contract", "locations", "min_rate"}
    # L'entretien à venir : jeudi prochain.
    assert upcoming is not None and upcoming.date() == next_thursday(TODAY)
    # Rien que des noms d'entreprise inventés, reconnaissables.
    words = (
        "Exemple",
        "Démo",
        "Essai",
        "Modèle",
        "Prototype",
        "Échantillon",
        "Test",
        "Bac à sable",
        "Maquette",
        "Brouillon",
        "Fictif",
        "Témoin",
    )
    assert all(any(w in spec.company for w in words) for spec in data.OFFERS)


async def test_read_only_without_login(demo_runtime: Runtime, demo_admin: Runtime) -> None:
    await seed(demo_admin, TODAY)
    app = create_app(demo_runtime.settings, demo_runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        me = (await client.get("/api/auth/me")).json()
        assert (me["demo"], me["authenticated"], me["is_owner"]) == (True, True, False)
        month = (await client.get("/api/orp", params={"month": "2026-09"})).json()
        assert month["count"] == 10
        refused = await client.put("/api/applications/1/job-room")
        assert refused.status_code == 403
        assert refused.json() == {"detail": demo.MESSAGE, "demo": True}
        assert (await client.post("/api/collect")).status_code == 403
        login = await client.post("/api/auth/login", json={"username": "x", "password": "y"})
        assert login.status_code == 403


async def test_guard_refuses_a_real_database() -> None:
    """Le mode démo ne démarre pas, et le remplissage refuse, sur une base qui a un vrai compte."""
    real = Runtime.create(make_settings(demo=True))
    try:
        async with real.sessionmaker.begin() as session:
            session.add(User(username="kevin-test", password_hash="scrypt$x"))
        with pytest.raises(demo.NotADemoDatabase):
            await seed(real, TODAY)
        app = create_app(real.settings, real)
        with pytest.raises(demo.NotADemoDatabase):
            async with app.router.lifespan_context(app):
                pass
    finally:
        async with real.sessionmaker.begin() as session:
            await session.execute(text("delete from users where username = 'kevin-test'"))
        await real.dispose()


async def test_guard_refuses_data_outside_the_demo(demo_database: str, demo_admin: Runtime) -> None:
    """Une installation neuve, ou sans connexion, a un exploitant sans mot de passe : ce sont
    ses données qui la distinguent d'une démo (docs/76 §1). Rien n'est effacé."""
    rt = Runtime.create(make_settings(database_url=demo_database, demo=True))
    owner = None
    try:
        await seed(demo_admin, TODAY)
        async with demo_admin.sessionmaker() as session:
            owner = await session.scalar(
                select(User.id).where(User.username == accounts.PLACEHOLDER_USERNAME)
            )
        with accounts.use(owner):
            async with rt.sessionmaker.begin() as session:
                session.add(
                    Application(
                        sent_at=TODAY,
                        method="electronique",
                        company="Vraie SA",
                        job_title="Vrai poste",
                        orp_month="2026-10",
                    )
                )
        with pytest.raises(demo.NotADemoDatabase, match="données"):
            await seed(demo_admin, TODAY)
        with accounts.use(owner):
            async with rt.sessionmaker() as session:
                kept = await session.scalar(select(func.count()).select_from(Application))
        assert kept == 1
        # Sans le mode démo, la commande ne touche à rien, même sur une base de démo.
        plain = Runtime.create(make_settings(database_url=demo_database))
        try:
            with pytest.raises(demo.NotADemoDatabase, match="JOBBOT_DEMO"):
                await seed(plain, TODAY)
        finally:
            await plain.dispose()
    finally:
        # Au nom de l'exploitant : les règles de la base ne montrent que ses lignes.
        with accounts.use(owner):
            async with rt.sessionmaker.begin() as session:
                await session.execute(text("DELETE FROM applications WHERE company = 'Vraie SA'"))
        await rt.dispose()


async def test_demo_reads_write_nothing(demo_runtime: Runtime, demo_admin: Runtime) -> None:
    """Une lecture qui enregistrerait quelque chose (date d'export du CSV) n'écrit rien en démo,
    et la base refuse toute écriture pendant une requête de visiteur."""
    await seed(demo_admin, TODAY)
    app = create_app(demo_runtime.settings, demo_runtime)

    async def months() -> int:
        async with demo_runtime.engine.begin() as conn:
            return int(await conn.scalar(text("select count(*) from orp_months")) or 0)

    before = await months()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.get("/api/orp/2026-09/csv")).status_code == 200
        # Les pages qui écrivaient en lisant (catalogue des formations, propositions
        # d'alertes) répondent sans rien écrire.
        assert (await client.get("/api/trainings")).status_code == 200
        assert (await client.get("/api/alert-searches")).status_code == 200
        # Les actualités du métier (docs/116 §4) : la démo n'abonne pas son profil.
        assert (await client.get("/api/news", params={"domain_only": True})).status_code == 200
    assert await months() == before
    from jobbot.db.base import read_only

    with read_only():
        async with demo_runtime.sessionmaker() as session:
            with pytest.raises(Exception, match="read-only"):
                await session.execute(text("insert into orp_months (month) values ('2026-01')"))


async def test_demo_url_offered_by_any_platform() -> None:
    """« La plateforme » d'une vraie installation propose la démo quand son adresse est réglée."""
    rt = Runtime.create(make_settings(demo_url="https://demo.exemple.ch"))
    try:
        app = create_app(rt.settings, rt)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            me = (await client.get("/api/auth/me")).json()
    finally:
        await rt.dispose()
    assert (me["demo"], me["demo_url"]) == (False, "https://demo.exemple.ch")
