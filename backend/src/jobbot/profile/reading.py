"""La lecture d'un document par l'IA : les blocs proposés (0.4.1, docs/121 §A).

Deux chemins : la réponse attendue par la page (accueil, `understand`) et la lecture du CV qui
continue sur le serveur quand on quitte la page (maquette du 10 novembre au soir, PR 21). Dans le
second cas, le résultat reste avec le document jusqu'au choix de la personne : mêmes règles que
le document (RLS, export, effacement) ; les coordonnées connues sont retirées avant l'envoi (I-1).
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import anthropic
from sqlalchemy import select

from jobbot.core.extract import TextStatus
from jobbot.db.models import Document
from jobbot.letters.service import load_identity
from jobbot.llm import proposals
from jobbot.llm.client import Refused
from jobbot.llm.scoring import InvalidScore
from jobbot.log import get_logger
from jobbot.notify.service import Message, deliver
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring_service
from jobbot.scoring.service import account_problem, active_profile, budget_state, record_call

log = get_logger(__name__)

# Estimation prudente du coût d'une proposition (document de quelques pages).
PROPOSAL_ESTIMATE_USD = Decimal("0.10")

# États de `documents.read_state` (PR 21) : NULL, jamais demandée.
READING = "reading"
DONE = "done"
UNAVAILABLE = "unavailable"
UNREADABLE = "unreadable"
# Une lecture qui n'a pas fini en dix minutes (worker arrêté) est indisponible : on peut réessayer.
STALE_AFTER = timedelta(minutes=10)


@dataclass
class ReadingFailed(Exception):
    """La lecture n'a pas pu se faire : code HTTP pour la page, message sans contenu (J-3)."""

    status_code: int
    message: str


async def propose(
    runtime: Runtime, document_id: int, *, understand: bool = False
) -> tuple[list[proposals.Proposal], str]:
    """L'IA lit le document : les blocs proposés, et la réponse brute (pour `understood`)."""
    settings = runtime.settings
    if not settings.llm_configured:
        raise ReadingFailed(409, "IA non configurée : renseigner JOBBOT_ANTHROPIC_API_KEY.")
    async with runtime.sessionmaker() as session:
        document = await session.get(Document, document_id)
        if document is None:
            raise ReadingFailed(404, "document introuvable")
        if document.text_status != TextStatus.OK or not document.extracted_text.strip():
            raise ReadingFailed(422, "ce document n'a pas de texte lisible")
        existing = await active_profile(session)
        spend, budget, rate = await budget_state(session, datetime.now(UTC))
        # Les coordonnées connues, retirées du texte avant l'envoi (docs/121 §A.3).
        identity = await load_identity(session)
        text = document.extracted_text
    if spend + PROPOSAL_ESTIMATE_USD * rate > budget:
        raise ReadingFailed(409, "plafond mensuel de l'IA atteint : le relever dans les Réglages")

    client = scoring_service.make_client(settings)
    params = proposals.request_params(
        settings.llm_model,
        settings.llm_effort,
        existing,
        text,
        identity,
        understand=understand,
    )
    try:
        raw = await client.score(params)
    except Refused:
        raise ReadingFailed(502, "l'IA a refusé de traiter ce document") from None
    except (anthropic.RateLimitError, anthropic.APIConnectionError):
        raise ReadingFailed(503, "IA momentanément indisponible, réessayer") from None
    except anthropic.APIStatusError as exc:
        problem = account_problem(exc)
        # Sans le message de l'API, qui peut citer la demande (J-1) : le code, le type
        # d'erreur et l'identifiant de la demande suffisent pour la retrouver chez Anthropic.
        body = exc.body if isinstance(exc.body, dict) else {}
        error = body.get("error")
        error = error if isinstance(error, dict) else {}
        log.warning(
            "document_reading_failed",
            document_id=document_id,
            understand=understand,
            status_code=exc.status_code,
            error_type=error.get("type"),
            request_id=exc.request_id,
        )
        raise ReadingFailed(
            409 if problem else 502,
            problem
            or f"l'IA n'a pas pu lire ce document (erreur {exc.status_code}) : "
            "complète les champs toi-même, rien n'est perdu",
        ) from None

    async with runtime.sessionmaker.begin() as session:
        await record_call(session, raw, offer_id=None, rate=rate, purpose="propose")
    try:
        result = proposals.parse_output(raw.text, existing)
    except InvalidScore:
        raise ReadingFailed(502, "réponse de l'IA inutilisable, réessayer") from None
    log.info("chunks_proposed", document_id=document_id, proposals=len(result))
    return result, raw.text


def state_of(document: Document, now: datetime | None = None) -> str | None:
    """L'état affiché : une lecture bloquée depuis trop longtemps devient « indisponible »."""
    state = document.read_state
    started = document.read_started_at
    if state == READING and started and (now or datetime.now(UTC)) - started > STALE_AFTER:
        return UNAVAILABLE
    return state


async def read_pending(runtime: Runtime) -> int:
    """Les lectures demandées par le compte en cours (tâche du worker) : le résultat est gardé
    avec le document, la cloche prévient. Renvoie le nombre de documents lus."""
    async with runtime.sessionmaker() as session:
        pending = list(
            await session.scalars(
                select(Document.id).where(Document.read_state == READING).order_by(Document.id)
            )
        )
    done = 0
    for document_id in pending:
        try:
            found, _ = await propose(runtime, document_id)
        except ReadingFailed as exc:
            state = UNREADABLE if exc.status_code == 422 else UNAVAILABLE
            await _finish(runtime, document_id, state=state, result=None)
            log.info("cv_read_failed", document_id=document_id, status_code=exc.status_code)
            continue
        kept = [p.model_dump() for p in found]
        await _finish(runtime, document_id, state=DONE, result=kept)
        done += 1
        new = [p for p in found if p.duplicate_of is None]
        await deliver(
            runtime,
            Message(
                title="Ton CV est lu",
                message=(
                    f"Ton CV est lu : {len(new)} élément{'s' if len(new) > 1 else ''} à choisir"
                    if new
                    else "Ton CV est lu : rien de nouveau à reprendre"
                ),
            ),
            kind="cv_read",
            link="/profil",
        )
    return done


async def _finish(
    runtime: Runtime, document_id: int, *, state: str, result: list[dict[str, object]] | None
) -> None:
    async with runtime.sessionmaker.begin() as session:
        document = await session.get(Document, document_id)
        # Supprimé ou relancé pendant la lecture : rien à écrire.
        if document is None or document.read_state != READING:
            return
        document.read_state = state
        document.read_result = result
        if state == DONE:
            document.read_at = datetime.now(UTC)
