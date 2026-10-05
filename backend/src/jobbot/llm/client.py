"""Accès à l'API Anthropic pour la notation (appels directs et lots).

Toute la plateforme passe par le protocole `ScoreClient` : en test, un faux client le
remplace et aucun appel réseau ni aucun coût n'a lieu.
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Protocol

import anthropic

from jobbot.llm.pricing import Usage
from jobbot.settings import Settings

# Repli serveur en cas de refus par les filtres de sécurité (docs/06 §3) : l'API rejoue la
# même demande sur le modèle recommandé pour la catégorie du refus. Absent des lots.
FALLBACK_BETA = "server-side-fallback-2026-07-01"


@dataclass(frozen=True)
class RawResult:
    text: str
    model: str
    usage: Usage
    stop_reason: str | None


class Refused(Exception):
    """L'IA (et son repli) a refusé de répondre."""


@dataclass(frozen=True)
class BatchItem:
    custom_id: str
    result: RawResult | None
    error: str | None


class ScoreClient(Protocol):
    async def score(self, params: dict[str, Any]) -> RawResult: ...

    async def create_batch(self, requests: list[tuple[str, dict[str, Any]]]) -> str: ...

    async def batch_ended(self, batch_id: str) -> bool: ...

    def batch_results(self, batch_id: str) -> AsyncIterator[BatchItem]: ...


def _raw(message: Any) -> RawResult:
    text = "".join(block.text for block in message.content if block.type == "text")
    usage = message.usage
    return RawResult(
        text=text,
        model=message.model,
        stop_reason=message.stop_reason,
        usage=Usage(
            input_tokens=usage.input_tokens or 0,
            cache_read_tokens=usage.cache_read_input_tokens or 0,
            cache_write_tokens=usage.cache_creation_input_tokens or 0,
            output_tokens=usage.output_tokens or 0,
            web_searches=getattr(getattr(usage, "server_tool_use", None), "web_search_requests", 0)
            or 0,
        ),
    )


class AnthropicScoreClient:
    def __init__(self, settings: Settings) -> None:
        key = settings.anthropic_api_key.get_secret_value() if settings.anthropic_api_key else ""
        self._client = anthropic.AsyncAnthropic(api_key=key, timeout=120.0, max_retries=3)

    async def score(self, params: dict[str, Any]) -> RawResult:
        message = await self._client.beta.messages.create(
            **params, betas=[FALLBACK_BETA], fallbacks="default"
        )
        result = _raw(message)
        if result.stop_reason == "refusal":
            raise Refused("réponse refusée par les filtres de sécurité")
        return result

    async def create_batch(self, requests: list[tuple[str, dict[str, Any]]]) -> str:
        batch = await self._client.messages.batches.create(
            requests=[{"custom_id": custom_id, "params": params} for custom_id, params in requests]  # type: ignore[typeddict-item]
        )
        return batch.id

    async def batch_ended(self, batch_id: str) -> bool:
        batch = await self._client.messages.batches.retrieve(batch_id)
        return batch.processing_status == "ended"

    async def batch_results(self, batch_id: str) -> AsyncIterator[BatchItem]:
        async for entry in await self._client.messages.batches.results(batch_id):
            outcome = entry.result
            if outcome.type == "succeeded":
                raw = _raw(outcome.message)
                if raw.stop_reason == "refusal":
                    yield BatchItem(entry.custom_id, None, "refus")
                else:
                    yield BatchItem(entry.custom_id, raw, None)
            else:
                yield BatchItem(entry.custom_id, None, outcome.type)


def client_factory(settings: Settings) -> ScoreClient:
    return AnthropicScoreClient(settings)
