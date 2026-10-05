"""Prix publics des modèles (dollars par million de jetons), pour le budget mensuel.

Écriture en cache : 1,25 fois l'entrée ; lecture en cache : 0,1 fois l'entrée ; lots : moitié prix.
Un modèle inconnu est compté au prix le plus élevé de la table, par prudence.
"""

from dataclasses import dataclass
from decimal import Decimal

PRICES: dict[str, tuple[Decimal, Decimal]] = {
    "claude-opus-5": (Decimal("5"), Decimal("25")),
    "claude-opus-4-8": (Decimal("5"), Decimal("25")),
    "claude-sonnet-5": (Decimal("2"), Decimal("10")),
    "claude-haiku-4-5": (Decimal("1"), Decimal("5")),
}
_FALLBACK = max(PRICES.values())
MILLION = Decimal(1_000_000)
WEB_SEARCH_USD = Decimal("0.01")


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    output_tokens: int = 0
    # Recherches web de l'outil serveur (0,01 $ l'unité).
    web_searches: int = 0


def cost_usd(model: str, usage: Usage, *, batch: bool = False) -> Decimal:
    # L'API renvoie parfois l'identifiant daté (« claude-haiku-4-5-20251001 »).
    price_in, price_out = PRICES.get(
        model, next((p for name, p in PRICES.items() if model.startswith(name)), _FALLBACK)
    )
    total = (
        usage.input_tokens * price_in
        + usage.cache_write_tokens * price_in * Decimal("1.25")
        + usage.cache_read_tokens * price_in * Decimal("0.1")
        + usage.output_tokens * price_out
    ) / MILLION
    total += Decimal(usage.web_searches) * WEB_SEARCH_USD
    if batch:
        total /= 2
    return total.quantize(Decimal("0.00001"))
