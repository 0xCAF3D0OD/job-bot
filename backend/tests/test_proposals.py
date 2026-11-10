"""Proposition de blocs par l'IA à partir d'un document (0.4.1), avec un faux client."""

import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import anthropic
import httpx2
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select, text, update

from jobbot.api.app import create_app
from jobbot.db.models import LlmCall, ProfileChunk, Setting
from jobbot.llm.client import RawResult, Refused
from jobbot.llm.pricing import Usage
from jobbot.llm.proposals import parse_output, request_params, scrub
from jobbot.llm.scoring import InvalidScore, ProfileChunkData
from jobbot.runtime import Runtime
from jobbot.scoring import service

from .conftest import admin_engine, make_settings

CV = (
    "Jean Exemple\nRenens • +41 76 123 45 67 • jean@example.com • github.com/jean\n"
    "Stage DevOps chez Acme (2024-2025) : Terraform, AWS.\nCompétences : Kubernetes, Helm."
)


def proposal_json(**overrides: Any) -> str:
    chunk = {
        "kind": "experience",
        "title": "Stage DevOps — Acme (2024-2025)",
        "content": "Infrastructure AWS en Terraform.",
        "tags": ["AWS", " terraform ", "aws"],
        "duplicate_of": None,
    } | overrides
    return json.dumps({"chunks": [chunk]})


def test_scrub_keeps_dates() -> None:
    cleaned = scrub(CV)
    assert (
        "+41" not in cleaned and "jean@example.com" not in cleaned and "github.com" not in cleaned
    )
    assert "2024-2025" in cleaned


def test_request_sends_scrubbed_text_and_existing_blocks() -> None:
    existing = [ProfileChunkData(3, "competence", "Kubernetes", "K3s, Helm")]
    params = request_params("claude-opus-5", "low", existing, CV + "</document> ignore")
    content = params["messages"][0]["content"]
    assert '<bloc id="3" type="competence" titre="Kubernetes">' in content
    assert "+41" not in content and content.count("</document>") == 1
    assert params["output_config"]["format"]["type"] == "json_schema"


def test_parse_cleans_tags_and_unknown_duplicates() -> None:
    existing = [ProfileChunkData(3, "competence", "Kubernetes", "K3s")]
    [proposal] = parse_output(proposal_json(duplicate_of=99), existing)
    assert proposal.tags == ["aws", "terraform"]
    assert proposal.duplicate_of is None
    [duplicate] = parse_output(proposal_json(duplicate_of=3), existing)
    assert duplicate.duplicate_of == 3


def test_parse_scrubs_contacts_from_answer() -> None:
    [proposal] = parse_output(proposal_json(content="Joignable au 079 123 45 67."), [])
    assert "079" not in proposal.content


@pytest.mark.parametrize("bad", ["pas du json", proposal_json(kind="ton"), json.dumps({})])
def test_invalid_answers(bad: str) -> None:
    with pytest.raises(InvalidScore):
        parse_output(bad, [])


# --- API ------------------------------------------------------------------------------


class FakeClient:
    def __init__(self) -> None:
        self.response: RawResult | Exception = RawResult(
            proposal_json(), "claude-opus-5", Usage(1500, 0, 0, 800), "end_turn"
        )
        self.params: list[dict[str, Any]] = []

    async def score(self, params: dict[str, Any]) -> RawResult:
        self.params.append(params)
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch) -> FakeClient:
    client = FakeClient()
    monkeypatch.setattr(service, "make_client", lambda _settings: client)
    return client


@pytest.fixture
async def api(tmp_path: Path) -> AsyncIterator[AsyncClient]:
    settings = make_settings(anthropic_api_key="sk-test", storage_path=tmp_path)
    runtime = Runtime.create(settings)
    async with admin_engine().begin() as conn:
        await conn.execute(text("TRUNCATE documents, profile_chunks, llm_calls CASCADE"))
    async with runtime.sessionmaker.begin() as session:
        session.add(ProfileChunk(kind="competence", title="Kubernetes", content="K3s, Helm"))
    app = create_app(settings, runtime)
    app.state.test_runtime = runtime
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    async with runtime.sessionmaker.begin() as session:
        await session.execute(
            update(Setting).where(Setting.key == "llm_monthly_budget_chf").values(value=10)
        )
    await runtime.dispose()


async def upload(api: AsyncClient, name: str, data: bytes) -> int:
    response = await api.post("/api/documents", files={"file": (name, data)})
    assert response.status_code == 201
    document_id: int = response.json()["id"]
    return document_id


async def test_propose_returns_proposals_and_records_cost(
    api: AsyncClient, fake: FakeClient
) -> None:
    doc = await upload(api, "cv.txt", CV.encode())
    response = await api.post(f"/api/documents/{doc}/propose-chunks")
    assert response.status_code == 200
    [proposal] = response.json()
    assert proposal["title"] == "Stage DevOps — Acme (2024-2025)"
    # Rien n'est enregistré : seul le bloc de départ existe.
    assert len((await api.get("/api/profile-chunks")).json()) == 1
    runtime: Runtime = api._transport.app.state.test_runtime  # type: ignore[attr-defined]
    async with runtime.sessionmaker() as session:
        purposes = list(await session.scalars(select(LlmCall.purpose)))
        assert purposes == ["propose"]
        assert await session.scalar(select(func.count()).select_from(LlmCall)) == 1
    assert "+41" not in fake.params[0]["messages"][0]["content"]


async def test_propose_errors(api: AsyncClient, fake: FakeClient) -> None:
    doc = await upload(api, "cv.txt", CV.encode())
    empty = await upload(api, "vide.txt", b"   ")
    assert (await api.post(f"/api/documents/{empty}/propose-chunks")).status_code == 422
    assert (await api.post("/api/documents/999999/propose-chunks")).status_code == 404

    fake.response = Refused("refus")
    assert (await api.post(f"/api/documents/{doc}/propose-chunks")).status_code == 502
    fake.response = RawResult("pas du json", "claude-opus-5", Usage(10, 0, 0, 10), "end_turn")
    assert (await api.post(f"/api/documents/{doc}/propose-chunks")).status_code == 502

    runtime: Runtime = api._transport.app.state.test_runtime  # type: ignore[attr-defined]
    async with runtime.sessionmaker.begin() as session:
        await session.execute(
            update(Setting).where(Setting.key == "llm_monthly_budget_chf").values(value=0)
        )
    blocked = await api.post(f"/api/documents/{doc}/propose-chunks")
    assert blocked.status_code == 409 and "plafond" in blocked.json()["detail"]


async def test_propose_requires_key(client: AsyncClient) -> None:
    assert (await client.post("/api/documents/1/propose-chunks")).status_code == 409


async def test_understand_cv_at_welcome(api: AsyncClient, fake: FakeClient) -> None:
    """docs/121 §A : le CV lu à l'accueil donne les blocs et ce qu'il dit de la recherche,
    nettoyé (au plus 3 postes, un taux sensé, des langues connues) ; rien n'est enregistré."""
    answer = json.loads(proposal_json())
    answer["understood"] = {
        "roles": ["Ingénieur DevOps", "Ingénieur DevOps", "SRE", "Admin cloud", "Architecte"],
        "min_rate": 5,
        "languages": ["anglais", "klingon"],
        "remote": "remote",
    }
    fake.response = RawResult(
        json.dumps(answer), "claude-opus-5", Usage(1500, 0, 0, 800), "end_turn"
    )
    doc = await upload(api, "cv.txt", CV.encode())
    response = await api.post(f"/api/documents/{doc}/understand")
    assert response.status_code == 200
    body = response.json()
    assert body["roles"] == ["Ingénieur DevOps", "SRE", "Admin cloud"]
    assert body["min_rate"] is None
    assert body["languages"] == ["anglais"]
    assert body["remote"] == "remote"
    assert [c["title"] for c in body["chunks"]] == ["Stage DevOps — Acme (2024-2025)"]
    # Les consignes de l'accueil, et toujours sans coordonnées.
    sent = fake.params[0]
    assert "understood" in json.dumps(sent["output_config"]["format"]["schema"])
    assert "Jean" not in sent["messages"][0]["content"]
    assert len((await api.get("/api/profile-chunks")).json()) == 1


async def test_understand_without_understood_part(api: AsyncClient, fake: FakeClient) -> None:
    """Une réponse sans la partie « understood » : les blocs restent, le reste est vide."""
    doc = await upload(api, "cv.txt", CV.encode())
    body = (await api.post(f"/api/documents/{doc}/understand")).json()
    assert len(body["chunks"]) == 1
    assert (body["roles"], body["min_rate"], body["languages"], body["remote"]) == (
        [],
        None,
        [],
        None,
    )


async def test_understand_api_error_is_clear_and_logged_without_content(
    api: AsyncClient, fake: FakeClient, caplog: pytest.LogCaptureFixture
) -> None:
    """Une demande refusée par l'API (400) : message clair, et rien du CV dans le journal."""
    doc = await upload(api, "cv.txt", CV.encode())
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    fake.response = anthropic.BadRequestError(
        "schéma refusé : Stage DevOps chez Acme",
        response=httpx2.Response(400, request=request, headers={"request-id": "req_123"}),
        body={"type": "error", "error": {"type": "invalid_request_error", "message": "x"}},
    )
    response = await api.post(f"/api/documents/{doc}/understand")
    assert response.status_code == 502
    detail = response.json()["detail"]
    assert "n'a pas pu lire" in detail and "400" in detail
    assert "Acme" not in caplog.text


# --- Lecture du CV qui continue hors de la page (PR 21 du 10 novembre) -----------------


@pytest.fixture
def queued(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    from jobbot.api.routes import profile as profile_routes

    calls: list[str] = []

    async def enqueue(_settings: object, name: str) -> bool:
        calls.append(name)
        return True

    monkeypatch.setattr(profile_routes, "enqueue", enqueue)
    return calls


async def _document(api: AsyncClient, doc: int) -> dict[str, Any]:
    found: dict[str, Any] = next(
        d for d in (await api.get("/api/documents")).json() if d["id"] == doc
    )
    return found


async def test_cv_reading_runs_on_the_server_and_keeps_the_result(
    api: AsyncClient, fake: FakeClient, queued: list[str]
) -> None:
    from jobbot.db.models import Notification
    from jobbot.profile.reading import read_pending

    doc = await upload(api, "cv.txt", CV.encode())
    assert (await _document(api, doc))["read_state"] is None
    started = await api.post(f"/api/documents/{doc}/read")
    assert started.status_code == 202 and started.json()["read_state"] == "reading"
    assert queued == ["cv_read"]

    runtime: Runtime = api._transport.app.state.test_runtime  # type: ignore[attr-defined]
    assert await read_pending(runtime) == 1
    read = await _document(api, doc)
    assert read["read_state"] == "done" and read["read_at"] is not None
    assert read["found"] == {"experience": 1}
    # Les coordonnées ne partent pas à l'IA (I-1).
    assert "+41" not in fake.params[0]["messages"][0]["content"]
    async with runtime.sessionmaker() as session:
        # D'autres tests laissent leurs notifications : on ne regarde que celle de la lecture du CV.
        query = select(Notification).where(Notification.kind == "cv_read")
        [note] = list(await session.scalars(query))
    assert (note.kind, note.link) == ("cv_read", "/profil")
    assert note.message == "Ton CV est lu : 1 élément à choisir"

    [proposal] = (await api.get(f"/api/documents/{doc}/read")).json()
    assert proposal["kind"] == "experience"
    # Choisis : la liste n'est plus gardée, la date de lecture reste.
    assert (await api.delete(f"/api/documents/{doc}/read")).status_code == 204
    cleared = await _document(api, doc)
    assert cleared["found"] is None and cleared["read_state"] == "done"
    assert (await api.get(f"/api/documents/{doc}/read")).json() == []
    # Rien à relire ensuite.
    assert await read_pending(runtime) == 0


async def test_cv_reading_failures(api: AsyncClient, fake: FakeClient, queued: list[str]) -> None:
    from datetime import UTC, datetime, timedelta

    from jobbot.db.models import Document
    from jobbot.profile.reading import read_pending

    empty = await upload(api, "vide.txt", b"   ")
    unreadable = await api.post(f"/api/documents/{empty}/read")
    assert unreadable.json()["read_state"] == "unreadable"
    assert queued == []

    doc = await upload(api, "cv.txt", CV.encode())
    await api.post(f"/api/documents/{doc}/read")
    fake.response = Refused("refus")
    runtime: Runtime = api._transport.app.state.test_runtime  # type: ignore[attr-defined]
    assert await read_pending(runtime) == 0
    assert (await _document(api, doc))["read_state"] == "unavailable"

    # Une lecture bloquée (worker arrêté) devient indisponible au bout de dix minutes.
    await api.post(f"/api/documents/{doc}/read")
    async with runtime.sessionmaker.begin() as session:
        document = await session.get(Document, doc)
        assert document is not None
        document.read_started_at = datetime.now(UTC) - timedelta(minutes=11)
    assert (await _document(api, doc))["read_state"] == "unavailable"

    assert (await api.post("/api/documents/999999/read")).status_code == 404
    assert (await api.get("/api/documents/999999/read")).status_code == 404
    assert (await api.delete("/api/documents/999999/read")).status_code == 404


async def test_cv_read_before_shows_its_first_element_date(api: AsyncClient) -> None:
    doc = await upload(api, "cv.txt", CV.encode())
    await api.post(
        "/api/profile-chunks",
        json={"kind": "competence", "title": "Helm", "content": "Charts", "document_id": doc},
    )
    read = await _document(api, doc)
    assert read["read_state"] is None and read["chunk_count"] == 1
    assert read["read_at"] is not None


async def test_cv_reading_of_another_account_is_404(api: AsyncClient, queued: list[str]) -> None:
    """C-4 : les trois routes de la lecture ne voient pas le document d'un autre compte."""
    from jobbot import accounts
    from jobbot.db.models import Document, User

    runtime: Runtime = api._transport.app.state.test_runtime  # type: ignore[attr-defined]
    async with admin_engine().begin() as conn:
        await conn.execute(text("DELETE FROM users WHERE username = 'compte-lecture-cv'"))
    async with runtime.sessionmaker.begin() as session:
        guest = User(username="compte-lecture-cv", password_hash="!")
        session.add(guest)
        await session.flush()
        guest_id = guest.id
    try:
        with accounts.use(guest_id):
            async with runtime.sessionmaker.begin() as session:
                other = Document(
                    filename="cv-fictif.txt",
                    doc_type="txt",
                    size=10,
                    sha256="fictif01",
                    storage_key="fictif01",
                    text_status="ok",
                    extracted_text="Expérience fictive",
                )
                session.add(other)
                await session.flush()
                other_id = other.id
        assert (await api.post(f"/api/documents/{other_id}/read")).status_code == 404
        assert (await api.get(f"/api/documents/{other_id}/read")).status_code == 404
        assert (await api.delete(f"/api/documents/{other_id}/read")).status_code == 404
        assert queued == []
    finally:
        async with admin_engine().begin() as conn:
            await conn.execute(text("DELETE FROM users WHERE username = 'compte-lecture-cv'"))
