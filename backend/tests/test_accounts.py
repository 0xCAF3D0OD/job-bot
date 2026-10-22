"""Deux comptes, aucune fuite (docs/65 §7).

Le compte A (l'exploitant) a une ligne dans chaque table personnelle, marquée « SECRET-A ».
Le compte B, connecté, appelle **toutes les routes de l'API** (lues dans le schéma OpenAPI :
une route ajoutée plus tard est testée d'office), avec les numéros des lignes de A :
il ne doit rien en voir, rien en modifier, rien en supprimer.
"""

import io
import re
import zipfile
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from jobbot import accounts
from jobbot.api.app import create_app
from jobbot.api.routes import trainings as trainings_routes
from jobbot.auth import passwords
from jobbot.db import policies
from jobbot.db.models import (
    AlertSearch,
    Application,
    CalendarToken,
    ChatAction,
    ChatConversation,
    ChatMessage,
    Contact,
    Document,
    Draft,
    Evaluation,
    ExtensionToken,
    Interview,
    InterviewPractice,
    LlmCall,
    Notification,
    Offer,
    OfferLink,
    OrpMeeting,
    OrpMonth,
    Profile,
    ProfileChunk,
    Training,
    TrainingMark,
    User,
)
from jobbot.runtime import Runtime

from .conftest import admin_engine, make_settings

SECRET = "SECRET-A"
PASSWORD = "un-mot-de-passe-de-test"
# Paramètres qui désignent une ligne d'un compte : la lire avec le numéro de A ne doit
# jamais réussir. Les autres (source d'actualités, site, formation du catalogue, mois)
# désignent du commun ou se lisent dans son propre compte.
PERSONAL = {
    "action_id",
    "application_id",
    "chunk_id",
    "contact_id",
    "conversation_id",
    "document_id",
    "draft_id",
    "interview_id",
    "meeting_id",
    "notification_id",
    "practice_id",
    "offer_id",
    "profile_id",
    "search_id",
    "token_id",
}
# Routes qui fermeraient la session de B pendant le test.
SKIPPED = {("post", "/api/auth/logout"), ("post", "/api/auth/logout-all")}
# Sans connexion, seules répondent : la connexion et les liens d'accès, les mentions de « Tes
# données », l'état de la maintenance (docs/79), l'agenda (son propre jeton) et l'extension
# (le sien) — docs/69 §1.
ANONYMOUS_OPEN = re.compile(r"^/api/(auth/|privacy$|maintenance$|agenda/feed/|extension/)")


def visible(response: Any) -> str:
    """Ce que la réponse laisse lire : le texte, ou le contenu d'une archive ZIP (un export)."""
    if response.headers.get("content-type", "").startswith("application/zip"):
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            return "\n".join(
                archive.read(name).decode("utf-8", "replace") for name in archive.namelist()
            )
    return str(response.text)


async def seed_account_a(runtime: Runtime) -> dict[str, Any]:
    now = datetime.now(UTC)
    async with runtime.sessionmaker.begin() as session:
        offer = Offer(
            fingerprint="secret-a",
            title=f"{SECRET} poste",
            company=f"{SECRET} SA",
            status="to_review",
            first_seen_at=now,
            last_seen_at=now,
        )
        session.add(offer)
        await session.flush()
        session.add(
            Evaluation(
                offer_id=offer.id, filter_passed=True, criteria_hash="h", summary_role=SECRET
            )
        )
        session.add(OfferLink(offer_id=offer.id, source="jobup", url="https://a.example/1"))
        application = Application(
            offer_id=offer.id,
            sent_at=date(2026, 10, 2),
            method="electronique",
            company=f"{SECRET} SA",
            job_title=SECRET,
            orp_month="2026-10",
            interview_at=now + timedelta(days=2),
        )
        session.add(application)
        await session.flush()
        interview = Interview(application_id=application.id, rating=4)
        practice = InterviewPractice(
            application_id=application.id,
            kind="rh",
            tone="bienveillant",
            language="fr",
            turns=[{"role": "recruteur", "text": SECRET, "question": 1}],
        )
        contact = Contact(
            application_id=application.id,
            name=SECRET,
            role="recruiter",
            channel="email",
            contacted_on=date(2026, 10, 3),
        )
        draft = Draft(offer_id=offer.id, kind="letter", version=1, language="fr", content=SECRET)
        document = Document(
            filename=f"{SECRET}.pdf",
            doc_type="pdf",
            size=3,
            sha256="a" * 64,
            storage_key="accounts/a/documents/x.pdf",
            text_status="ok",
            extracted_text=SECRET,
        )
        chunk = ProfileChunk(kind="experience", title=SECRET, content=SECRET)
        notification = Notification(kind="test", title=SECRET, message=SECRET)
        search = AlertSearch(terms=SECRET)
        profile = Profile(name=f"{SECRET} essai")
        conversation = ChatConversation(title=SECRET)
        calendar = CalendarToken(name=SECRET, token_hash="c" * 64)
        extension = ExtensionToken(name=SECRET, token_hash="e" * 64)
        training = Training(
            title="Formation commune",
            provider="Catalogue",
            kind="cours",
            format="self_paced",
            language="fr",
            price="free",
            url="https://formation.example/commune",
            origin="catalog",
        )
        session.add_all(
            [
                interview,
                practice,
                contact,
                draft,
                document,
                chunk,
                notification,
                search,
                profile,
                conversation,
                calendar,
                extension,
                training,
                OrpMonth(month="2026-10"),
                LlmCall(
                    purpose="score",
                    model="m",
                    cost_usd=Decimal("1"),
                    cost_chf=Decimal("0.9"),
                ),
            ]
        )
        await session.flush()
        session.add(ChatMessage(conversation_id=conversation.id, role="user", content=SECRET))
        action = ChatAction(
            conversation_id=conversation.id,
            kind="offer_status",
            target_id=offer.id,
            value="later",
            previous="to_review",
            label=SECRET,
        )
        session.add(action)
        meeting = OrpMeeting(
            starts_at=datetime.now(UTC) - timedelta(days=1), place=SECRET, questions=[], measures=[]
        )
        session.add(meeting)
        main = await session.scalar(text("select id from profiles where is_main"))
        session.add(TrainingMark(profile_id=main, training_id=training.id, status="interested"))
        await session.execute(
            text(
                "insert into settings (key, value) values ('identity_last_name', :v), "
                "('ui_secret', :v) on conflict do nothing"
            ),
            {"v": f'"{SECRET}"'},
        )
        await session.execute(
            text(
                "insert into criteria (kind, value) values ('banned_words', :v) "
                "on conflict (user_id, kind) do update set value = excluded.value"
            ),
            {"v": f'["{SECRET}"]'},
        )
        await session.flush()
        return {
            "action_id": action.id,
            "application_id": application.id,
            "chunk_id": chunk.id,
            "contact_id": contact.id,
            "conversation_id": conversation.id,
            "document_id": document.id,
            "draft_id": draft.id,
            "interview_id": interview.id,
            "meeting_id": meeting.id,
            "practice_id": practice.id,
            "notification_id": notification.id,
            "offer_id": offer.id,
            "profile_id": profile.id,
            "search_id": search.id,
            "token_id": calendar.id,
            "training_id": training.id,
            "month": "2026-10",
            "site": "jobup",
            "site_id": 1,
            "source_id": 1,
            "item_id": 1,
            "catalog_id": "inconnu",
            "token": "inconnu",
            "account_id": accounts.current(),
            "link_id": 1,
        }


async def account_tables(_runtime: Runtime) -> list[str]:
    """Les tables rangées par compte (docs/78 §3.2) ; `test_policies.py` vérifie que la base
    les sépare toutes."""
    return sorted(policies.PERSONAL)


# Communs, et modifiables seulement par l'exploitant et le worker (docs/78 §3.2) ; le journal
# des tâches change à chaque tâche.
SHARED = tuple(t for t in policies.SHARED if t != "job_runs")


async def snapshot(runtime: Runtime, tables: list[str] | None = None) -> dict[str, str]:
    """Empreinte de chaque table personnelle, vue par le compte en cours."""
    found = {}
    tables = tables or await account_tables(runtime)
    async with runtime.sessionmaker() as session:
        for table in tables:
            found[table] = await session.scalar(
                text(
                    "select md5(coalesce(string_agg(t::text, '|' order by t::text), '')) "
                    f"from {table} t"
                )
            )
    return found


def example(
    schema: dict[str, Any], spec: dict[str, Any], ids: dict[str, Any], depth: int = 0
) -> Any:
    """Un corps de requête valide d'après le schéma, pour que la route aille au bout ; les
    champs qui désignent une ligne (`offer_id`, `chunk_ids`…) reçoivent celles de A."""
    if "$ref" in schema:
        name = schema["$ref"].rsplit("/", 1)[-1]
        return example(spec["components"]["schemas"][name], spec, ids, depth + 1)
    for key in ("anyOf", "oneOf", "allOf"):
        if key in schema:
            options = [s for s in schema[key] if s.get("type") != "null"]
            return example(options[0], spec, ids, depth + 1) if options else None
    if "enum" in schema:
        return schema["enum"][0]
    kind = schema.get("type")
    if kind == "object" or "properties" in schema:
        if depth > 6:
            return {}
        body = {}
        for name, sub in schema.get("properties", {}).items():
            if name in ids:
                body[name] = ids[name]
            elif name.endswith("_ids") and f"{name[:-4]}_id" in ids:
                body[name] = [ids[f"{name[:-4]}_id"]]
            elif name in schema.get("required", []):
                body[name] = example(sub, spec, ids, depth + 1)
        return body
    if "default" in schema:
        return schema["default"]
    if kind == "array":
        count = int(schema.get("minItems", 0))
        return [example(schema.get("items", {}), spec, ids, depth + 1) for _ in range(count)]
    if kind == "integer":
        return max(1, int(schema.get("minimum", 1)))
    if kind == "number":
        return 1
    if kind == "boolean":
        return False
    if schema.get("format") == "date":
        return "2026-10-05"
    return "x" * max(2, int(schema.get("minLength", 1)))


@pytest.fixture
async def two_accounts(runtime: Runtime) -> AsyncIterator[tuple[int, int]]:
    async with admin_engine().begin() as conn:
        await conn.execute(text("TRUNCATE offers, alert_searches, chat_conversations CASCADE"))
        await conn.execute(text("DELETE FROM users WHERE username = 'compte-b'"))
    async with runtime.sessionmaker.begin() as session:
        owner = await accounts.owner_id(session)
        b = User(username="compte-b", password_hash=passwords.hash_password(PASSWORD))
        session.add(b)
        await session.flush()
        other = b.id
    yield owner, other
    async with admin_engine().begin() as conn:
        await conn.execute(text("DELETE FROM users WHERE username = 'compte-b'"))
        await conn.execute(text("TRUNCATE offers, alert_searches, chat_conversations CASCADE"))
        await conn.execute(text("DELETE FROM calendar_tokens WHERE name = :n"), {"n": SECRET})
        await conn.execute(text("DELETE FROM extension_tokens WHERE name = :n"), {"n": SECRET})
        for table in ("documents", "profile_chunks", "notifications", "llm_calls", "orp_months"):
            await conn.execute(text(f"DELETE FROM {table}"))
        await conn.execute(text("DELETE FROM profiles WHERE name = :n"), {"n": f"{SECRET} essai"})
        await conn.execute(
            text("DELETE FROM trainings WHERE url LIKE 'https://formation.example/%'")
        )
        await conn.execute(
            text("DELETE FROM settings WHERE key IN ('identity_last_name', 'ui_secret')")
        )
        await conn.execute(text("DELETE FROM criteria WHERE kind = 'banned_words'"))


async def test_account_b_sees_and_changes_nothing_of_a(
    runtime: Runtime, two_accounts: tuple[int, int], monkeypatch: pytest.MonkeyPatch
) -> None:
    owner, other = two_accounts
    assert owner != other
    ids = await seed_account_a(runtime)
    # Le catalogue des formations, tiré du dépôt, est écrit d'abord : ce n'est pas B qui
    # l'écrit, c'est la plateforme, au nom de l'exploitant.
    await trainings_routes._ensure_catalog(runtime)
    before = await snapshot(runtime)
    shared_before = await snapshot(runtime, list(SHARED))

    async def no_queue(*_args: object) -> bool:
        return True

    for module in ("collect", "scoring", "preferences", "news"):
        monkeypatch.setattr(f"jobbot.api.routes.{module}.enqueue", no_queue)

    # Connexion activée : B est reconnu par son cookie.
    secured = Runtime.create(make_settings(auth_enabled=True))
    app = create_app(secured.settings, secured)
    spec = app.openapi()
    called = 0
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as api:
        login = await api.post(
            "/api/auth/login", json={"username": "compte-b", "password": PASSWORD}
        )
        assert login.status_code == 204
        # L'extension de B, avec son propre jeton : elle non plus ne voit rien de A.
        created = await api.post("/api/extension-tokens", json={"name": "B"})
        extension = {"Authorization": f"Bearer {created.json()['token']}"}
        # Les lectures d'abord, puis les modifications.
        operations = sorted(
            ((m, p, op) for p, ops in spec["paths"].items() for m, op in ops.items()),
            key=lambda o: o[0] != "get",
        )
        for method, path, op in operations:
            if (method, path) in SKIPPED:
                continue
            names = re.findall(r"{([^}]+)}", path)
            url = path
            for name in names:
                url = url.replace("{" + name + "}", str(ids[name]))
            body = None
            if "requestBody" in op:
                content = op["requestBody"]["content"]
                if "application/json" in content:
                    body = example(content["application/json"]["schema"], spec, ids)
            headers = extension if path.startswith("/api/extension/") else {}
            if body is not None:
                response = await api.request(method.upper(), url, json=body, headers=headers)
            elif "requestBody" in op:
                response = await api.request(
                    method.upper(), url, files={"file": ("b.txt", b"b")}, headers=headers
                )
            else:
                response = await api.request(method.upper(), url, headers=headers)
            called += 1
            assert SECRET not in visible(response), (
                f"{method.upper()} {path} montre une donnée de A"
            )
            if method == "get" and PERSONAL & set(names) and response.status_code == 200:
                # Une liste rattachée à une ligne de A (ses entretiens…) : vide pour B.
                assert response.json() in ([], None), f"GET {path} lit une ligne de A"
    assert called > 140

    with accounts.use(owner):
        after = await snapshot(runtime)
    changed = [table for table in before if before[table] != after[table]]
    assert changed == [], f"B a modifié des lignes de A : {changed}"
    shared_after = await snapshot(runtime, list(SHARED))
    changed = [table for table in SHARED if shared_before[table] != shared_after[table]]
    assert changed == [], f"B a modifié des données communes : {changed}"

    # L'agenda : chaque lien ne donne que les rendez-vous de son compte.
    async def feed(api: AsyncClient) -> str:
        created = (await api.post("/api/agenda/tokens", json={"name": "agenda"})).json()
        return (await api.get(created["url"].replace("http://localhost", ""))).text

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as api:
        await api.post("/api/auth/login", json={"username": "compte-b", "password": PASSWORD})
        assert "BEGIN:VCALENDAR" in (b_feed := await feed(api)) and SECRET not in b_feed
    owner_app = create_app(runtime.settings, runtime)
    async with AsyncClient(
        transport=ASGITransport(app=owner_app), base_url="http://localhost"
    ) as api:
        assert SECRET in await feed(api)
    await secured.dispose()


async def test_without_login_nothing_answers(
    runtime: Runtime, two_accounts: tuple[int, int], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sans connexion, toutes les routes (lues dans le schéma) répondent 401, sauf celles qui
    sont ouvertes exprès ; aucune ne montre ni ne modifie une donnée de A (docs/69 §1)."""
    ids = await seed_account_a(runtime)
    before = await snapshot(runtime)

    async def no_queue(*_args: object) -> bool:
        return True

    for module in ("collect", "scoring", "preferences", "news"):
        monkeypatch.setattr(f"jobbot.api.routes.{module}.enqueue", no_queue)
    secured = Runtime.create(make_settings(auth_enabled=True))
    app = create_app(secured.settings, secured)
    spec = app.openapi()
    called = 0
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as api:
        for path, ops in spec["paths"].items():
            for method, op in ops.items():
                url = path
                for name in re.findall(r"{([^}]+)}", path):
                    url = url.replace("{" + name + "}", str(ids.get(name, 1)))
                body = None
                content = op.get("requestBody", {}).get("content", {})
                if "application/json" in content:
                    body = example(content["application/json"]["schema"], spec, ids)
                response = await api.request(method.upper(), url, json=body)
                called += 1
                where = f"{method.upper()} {path}"
                assert SECRET not in visible(response), f"{where} montre une donnée de A"
                if not ANONYMOUS_OPEN.match(path):
                    assert response.status_code == 401, f"{where} répond sans connexion"
    assert called > 140
    assert await snapshot(runtime) == before, "une route sans connexion a modifié des données"
    await secured.dispose()


async def test_database_refuses_other_account(
    runtime: Runtime, two_accounts: tuple[int, int]
) -> None:
    owner, other = two_accounts
    await seed_account_a(runtime)
    tables = await account_tables(runtime)
    assert len(tables) == 33  # dont les paiements de Plus (docs/125)
    with accounts.use(other):
        async with runtime.sessionmaker() as session:
            for table in tables:
                seen = await session.scalar(text(f"select count(*) from {table}"))
                mine = await session.scalar(
                    text(f"select count(*) from {table} where user_id = :b"),
                    {"b": other},
                )
                assert seen == mine, table
        # Écrire au nom de A, même en le demandant, est refusé.
        with pytest.raises(ProgrammingError):
            async with runtime.sessionmaker.begin() as session:
                await session.execute(
                    text("insert into notifications (kind, title, user_id) values ('x', 'x', :a)"),
                    {"a": owner},
                )
    # Sans compte : rien de visible, aucune écriture.
    with accounts.use(None):
        async with runtime.sessionmaker() as session:
            assert await session.scalar(text("select count(*) from offers")) == 0
        with pytest.raises(Exception, match=r"row-level security|null value"):
            async with runtime.sessionmaker.begin() as session:
                await session.execute(
                    text("insert into notifications (kind, title) values ('x', 'x')")
                )


async def test_jobs_run_account_by_account(
    runtime: Runtime, two_accounts: tuple[int, int], monkeypatch: pytest.MonkeyPatch
) -> None:
    from jobbot.worker import jobs

    owner, other = two_accounts
    seen: list[tuple[str, int | None]] = []

    async def record(_runtime: Runtime, ctx: jobs.RunContext) -> None:
        seen.append((ctx.job, accounts.current()))

    monkeypatch.setitem(jobs.JOBS, "test-comptes", jobs.JobSpec("test-comptes", record))
    monkeypatch.setitem(
        jobs.JOBS, "test-exploitant", jobs.JobSpec("test-exploitant", record, scope="owner")
    )
    monkeypatch.setitem(
        jobs.JOBS, "test-plateforme", jobs.JobSpec("test-plateforme", record, scope="platform")
    )
    # Le worker, avec son accès (docs/78 §3.1) : il écrit le journal des tâches.
    worker = Runtime.create(runtime.settings, "worker")
    with accounts.use(None):
        # Planifiées : chaque compte à son tour, l'exploitant seul, ou sans compte.
        for name in ("test-comptes", "test-exploitant", "test-plateforme"):
            assert await jobs.execute(worker, name)
    assert seen == [
        ("test-comptes", owner),
        ("test-comptes", other),
        ("test-exploitant", owner),
        ("test-plateforme", None),
    ]
    seen.clear()
    # Lancée pour un compte (bouton) : pour lui seul ; celle de l'exploitant, pas pour B.
    with accounts.use(other):
        assert await jobs.execute(worker, "test-comptes")
        assert await jobs.execute(worker, "test-exploitant")
    assert seen == [("test-comptes", other)]
    await worker.dispose()
