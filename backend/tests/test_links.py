"""Aucun lien entre deux comptes, et des tâches qui gardent leur compte (docs/78 §3.3, §3.4)."""

from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from starlette.requests import Request

from jobbot import accounts
from jobbot.api.routes import scoring as scoring_routes
from jobbot.auth import passwords
from jobbot.contacts import message
from jobbot.db import policies
from jobbot.db.models import (
    Application,
    ChatConversation,
    ChatMessage,
    Contact,
    JobRun,
    JobRunStatus,
    LlmCall,
    Offer,
    User,
)
from jobbot.llm.client import RawResult
from jobbot.llm.pricing import Usage
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring
from jobbot.worker import jobs
from jobbot.worker.app import build_procrastinate_app
from jobbot.worker.queue import enqueue

from .conftest import admin_engine

GUEST = "compte-liens"
NOW = datetime.now(UTC)


async def catalog(sql: str) -> list[tuple[Any, ...]]:
    async with admin_engine().connect() as conn:
        return [tuple(row) for row in await conn.execute(text(sql))]


@pytest.fixture
async def guest(runtime: Runtime) -> AsyncIterator[int]:
    async def clean() -> None:
        async with admin_engine().begin() as conn:
            await conn.execute(text("DELETE FROM users WHERE username = :u"), {"u": GUEST})
            await conn.execute(text("TRUNCATE offers, applications, llm_calls CASCADE"))
            await conn.execute(text("DELETE FROM chat_conversations"))
            await conn.execute(text("DELETE FROM job_runs WHERE job LIKE 'test-%'"))
            await conn.execute(text("DELETE FROM procrastinate_jobs"))

    await clean()
    async with runtime.sessionmaker.begin() as session:
        user = User(username=GUEST, password_hash=passwords.hash_password("x" * 12))
        session.add(user)
        await session.flush()
        guest_id = user.id
    yield guest_id
    await clean()


async def test_every_link_between_accounts_includes_the_account() -> None:
    """Les 22 clés étrangères entre tables personnelles comprennent le compte : la base refuse
    tout lien vers une ligne d'un autre compte."""
    rows = await catalog(
        "select con.conrelid::regclass::text, con.confrelid::regclass::text, "
        "pg_get_constraintdef(con.oid) from pg_constraint con where con.contype = 'f'"
    )
    personal = set(policies.PERSONAL)
    links = [(t, p, d) for t, p, d in rows if t in personal and p in personal]
    # dont la lecture d'un certificat (docs/87), la correction d'une note et son bloc (docs/114), et
    # la lettre d'une affirmation « Pas vrai »
    assert len(links) == 25
    for table, parent, definition in links:
        assert definition.startswith("FOREIGN KEY (user_id, "), (table, definition)
        assert f"REFERENCES {parent}(user_id, id)" in definition, (table, definition)


async def test_database_refuses_a_link_to_another_account(
    runtime: Runtime, account: int, guest: int
) -> None:
    async with runtime.sessionmaker.begin() as session:
        offer = Offer(
            fingerprint="liens-a", title="Poste de A", first_seen_at=NOW, last_seen_at=NOW
        )
        session.add(offer)
        await session.flush()
        application = Application(
            offer_id=offer.id,
            sent_at=date(2026, 10, 2),
            method="electronique",
            company="A SA",
            job_title="Poste de A",
            orp_month="2026-10",
        )
        conversation = ChatConversation(title="A")
        session.add_all([application, conversation])
        await session.flush()
        ids = {"offer": offer.id, "application": application.id, "chat": conversation.id}
    attempts = [
        LlmCall(
            purpose="contact",
            model="m",
            cost_usd=Decimal("0"),
            cost_chf=Decimal("0"),
            offer_id=ids["offer"],
        ),
        Application(
            offer_id=ids["offer"],
            sent_at=date(2026, 10, 2),
            method="electronique",
            company="B SA",
            job_title="B",
            orp_month="2026-10",
        ),
        Contact(
            application_id=ids["application"],
            name="x",
            role="recruiter",
            channel="email",
            contacted_on=date(2026, 10, 3),
        ),
        ChatMessage(conversation_id=ids["chat"], role="user", content="x"),
    ]
    for row in attempts:
        with accounts.use(guest), pytest.raises(IntegrityError, match="foreign key"):
            async with runtime.sessionmaker.begin() as session:
                session.add(row)


async def test_contact_message_keeps_only_its_own_offer(
    runtime: Runtime, account: int, guest: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Une candidature de B avec le numéro d'une offre de A : l'appel est enregistré sans
    l'offre de A (docs/78 §2)."""
    async with runtime.sessionmaker.begin() as session:
        offer = Offer(
            fingerprint="liens-a", title="Poste de A", first_seen_at=NOW, last_seen_at=NOW
        )
        session.add(offer)
        await session.flush()
        a_offer = offer.id
    with accounts.use(guest):
        async with runtime.sessionmaker.begin() as session:
            application = Application(
                sent_at=date(2026, 10, 2),
                method="electronique",
                company="B SA",
                job_title="Poste de B",
                orp_month="2026-10",
            )
            session.add(application)
            await session.flush()
            b_application = application.id

    class Fake:
        async def score(self, _params: dict[str, Any]) -> RawResult:
            return RawResult("Bonjour", message.MODEL, Usage(10, 0, 0, 5), "end_turn")

    monkeypatch.setattr(scoring, "make_client", lambda _settings: Fake())
    monkeypatch.setattr(type(runtime.settings), "llm_configured", property(lambda _self: True))
    with accounts.use(guest):
        await message.draft(
            runtime,
            offer_id=a_offer,
            application_id=b_application,
            role="recruiter",
            channel="email",
        )
        async with runtime.sessionmaker() as session:
            assert list(await session.scalars(select(LlmCall.offer_id))) == [None]


async def test_queued_task_runs_only_for_its_account(
    runtime: Runtime, account: int, guest: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    """La vraie file (sans la remplacer) : la tâche mise en file par B ne tourne que pour B ;
    deux comptes peuvent la demander en même temps, un même compte une fois (docs/78 §3.4)."""
    seen: list[int | None] = []

    async def record(_runtime: Runtime, _ctx: jobs.RunContext) -> None:
        seen.append(accounts.current())

    monkeypatch.setitem(jobs.JOBS, "test-file", jobs.JobSpec("test-file", record))
    with accounts.use(guest):
        assert await enqueue(runtime.settings, "test-file")
        assert not await enqueue(runtime.settings, "test-file")
    assert await enqueue(runtime.settings, "test-file")  # l'exploitant, à son tour
    queued = await catalog("select args, queueing_lock from procrastinate_jobs order by id")
    assert queued == [
        ({"account": guest}, f"test-file:{guest}"),
        ({"account": account}, f"test-file:{account}"),
    ]
    worker = Runtime.create(runtime.settings, "worker")
    try:
        app = build_procrastinate_app(worker)
        async with app.open_async():
            await app.run_worker_async(
                queues=["default"], wait=False, install_signal_handlers=False
            )
    finally:
        await worker.dispose()
    assert seen == [guest, account]


async def test_scoring_error_seen_by_its_account_detail_by_the_owner(
    runtime: Runtime, account: int, guest: int
) -> None:
    """Le passage de notation est commun : le compte qui a échoué le voit, sans le détail ;
    l'exploitant voit le détail ; un autre compte ne voit rien (docs/78 §3.4)."""
    async with runtime.sessionmaker.begin() as session:
        session.add(
            JobRun(
                job="score",
                status=JobRunStatus.FAILURE,
                finished_at=datetime.now(UTC),
                error="IntegrityError: détail d'un compte",
                failed_accounts=[guest],
            )
        )
        third = User(username="compte-liens-3", password_hash="!")
        session.add(third)
        await session.flush()
        other = third.id
    request = Request(
        {
            "type": "http",
            "app": SimpleNamespace(state=SimpleNamespace(runtime=runtime)),
            "headers": [],
        }
    )
    try:
        seen = {}
        for who in (account, guest, other):
            with accounts.use(who):
                seen[who] = (await scoring_routes.get_scoring_status(request)).last_error
    finally:
        async with admin_engine().begin() as conn:
            await conn.execute(text("DELETE FROM job_runs WHERE job = 'score'"))
            await conn.execute(text("DELETE FROM users WHERE username = 'compte-liens-3'"))
    assert seen[account] == "IntegrityError: détail d'un compte"
    assert seen[guest] == "la dernière notation a échoué : voir avec l'exploitant"
    assert seen[other] is None
