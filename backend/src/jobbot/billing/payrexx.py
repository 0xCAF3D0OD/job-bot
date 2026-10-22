"""Payrexx, le prestataire de paiement de Plus (docs/125 §6) : la page de paiement est la sienne,
jobA1 ne voit jamais la carte. L'API s'authentifie par l'en-tête `X-API-KEY` ; un webhook est
signé (HMAC-SHA256 du corps brut, en hexadécimal) et ne sert qu'à déclencher une relecture de la
transaction auprès de l'API : on ne croit jamais le contenu d'un webhook sur parole."""

import hashlib
import hmac
from typing import Any

import httpx

from jobbot.settings import Settings

API = "https://api.payrexx.com/v1.0"
TIMEOUT = 20.0


class PayrexxError(Exception):
    """Payrexx a refusé ou n'a pas répondu."""


def _key(settings: Settings) -> str:
    assert settings.payrexx_api_secret is not None
    return settings.payrexx_api_secret.get_secret_value()


async def _request(
    settings: Settings, method: str, path: str, json: dict[str, Any] | None = None
) -> dict[str, Any]:
    url = f"{API}/{path}"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.request(
                method,
                url,
                params={"instance": settings.payrexx_instance},
                headers={"X-API-KEY": _key(settings)},
                json=json,
            )
    except httpx.HTTPError as exc:
        raise PayrexxError(f"Payrexx injoignable ({type(exc).__name__})") from exc
    if response.status_code >= 400:
        raise PayrexxError(f"Payrexx : erreur {response.status_code}")
    body: dict[str, Any] = response.json()
    if body.get("status") not in (None, "success"):
        raise PayrexxError(f"Payrexx : {body.get('message') or body.get('status')}")
    return body


async def create_gateway(settings: Settings, *, reference: str, back: str) -> tuple[str, str]:
    """La page de paiement de Plus, en abonnement mensuel. Rend (id, lien)."""
    from jobbot.plans import PLUS_PRICE_CHF

    body = await _request(
        settings,
        "POST",
        "Gateway/",
        {
            "amount": PLUS_PRICE_CHF * 100,
            "currency": "CHF",
            "purpose": "jobA1 Plus, un mois",
            "referenceId": reference,
            "language": "fr",
            "successRedirectUrl": f"{back}&paiement=ok",
            "failedRedirectUrl": f"{back}&paiement=echec",
            "cancelRedirectUrl": f"{back}&paiement=annule",
            "subscriptionState": True,
            "subscriptionInterval": "P1M",
            "subscriptionPeriod": "P1M",
            "subscriptionCancellationInterval": "P0D",
        },
    )
    gateway = body["data"][0]
    return str(gateway["id"]), str(gateway["link"])


async def gateway_status(settings: Settings, gateway_id: str) -> str:
    body = await _request(settings, "GET", f"Gateway/{gateway_id}/")
    return str(body["data"][0].get("status") or "")


async def transaction(settings: Settings, transaction_id: str) -> dict[str, Any]:
    body = await _request(settings, "GET", f"Transaction/{transaction_id}/")
    data: dict[str, Any] = body["data"][0]
    return data


async def cancel_subscription(settings: Settings, subscription_id: str) -> None:
    await _request(settings, "DELETE", f"Subscription/{subscription_id}/")


def signed(settings: Settings, raw: bytes, signature: str | None) -> bool:
    """Le webhook vient bien de Payrexx (la clé de signature de l'instance)."""
    if not signature or settings.payrexx_webhook_key is None:
        return False
    key = settings.payrexx_webhook_key.get_secret_value().encode()
    expected = hmac.new(key, raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.strip().lower())
