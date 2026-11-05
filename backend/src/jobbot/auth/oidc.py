"""Se connecter avec Google, Microsoft ou Apple (docs/65, complément du 2026-11-05).

OpenID Connect, schéma « code d'autorisation » avec PKCE (S256), `state` et `nonce` :

1. `start` tire un `state`, un `nonce` et un vérificateur PKCE, les garde côté serveur sous un
   numéro de parcours tiré au hasard (le cookie `jobbot_oidc`), puis envoie la personne chez le
   fournisseur ;
2. au retour, le parcours est repris par ce cookie (une seule fois), le `state` reçu comparé en
   temps constant, le code échangé (avec le vérificateur) contre le jeton d'identité ;
3. le jeton d'identité est vérifié : signature (clés publiées par le fournisseur), émetteur,
   destinataire (`aud`), expiration et `nonce`.

Rien n'est gardé du fournisseur que son identifiant stable (`sub`), l'e-mail et s'il est vérifié.
Les jetons d'accès ne sont ni gardés ni journalisés.

Les parcours vivent en mémoire, comme les essais de connexion (`service.Throttle`) : l'API tourne
en un seul processus. 10 minutes au plus, 2000 parcours au plus.
"""

import base64
import hashlib
import hmac
import json
import re
import secrets
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlencode

import httpx
import jwt

from jobbot.settings import Settings

PROVIDERS = ("apple", "google", "microsoft")
LABELS = {"apple": "Apple", "google": "Google", "microsoft": "Microsoft"}
FLOW_COOKIE = "jobbot_oidc"
FLOW_TTL_S = 600
FLOW_MAX = 2000
# Un peu de marge pour les horloges (secondes).
LEEWAY_S = 60
JWKS_TTL_S = 3600
HTTP_TIMEOUT_S = 10.0
APPLE_ISSUER = "https://appleid.apple.com"
GOOGLE_ISSUERS = ("https://accounts.google.com", "accounts.google.com")
MICROSOFT_ISSUER = re.compile(r"^https://login\.microsoftonline\.com/([0-9a-f-]{36})/v2\.0$")
GUID = re.compile(r"^[0-9a-f-]{36}$")


class OidcError(Exception):
    """Parcours inconnu, `state` ou `nonce` faux, jeton refusé, fournisseur injoignable. Le
    message est pour le journal (jamais de jeton ni d'e-mail) ; `reason` pour l'écran."""

    def __init__(self, message: str, reason: str = "refuse") -> None:
        super().__init__(message)
        self.reason = reason


@dataclass(frozen=True)
class Endpoints:
    authorize: str
    token: str
    jwks: str


def endpoints(settings: Settings, provider: str) -> Endpoints:
    if provider == "google":
        return Endpoints(
            "https://accounts.google.com/o/oauth2/v2/auth",
            "https://oauth2.googleapis.com/token",
            "https://www.googleapis.com/oauth2/v3/certs",
        )
    if provider == "microsoft":
        base = f"https://login.microsoftonline.com/{settings.oauth_microsoft_tenant.strip()}"
        return Endpoints(
            f"{base}/oauth2/v2.0/authorize",
            f"{base}/oauth2/v2.0/token",
            f"{base}/discovery/v2.0/keys",
        )
    return Endpoints(
        f"{APPLE_ISSUER}/auth/authorize", f"{APPLE_ISSUER}/auth/token", f"{APPLE_ISSUER}/auth/keys"
    )


def client_id(settings: Settings, provider: str) -> str:
    return {
        "google": settings.oauth_google_client_id,
        "microsoft": settings.oauth_microsoft_client_id,
        "apple": settings.oauth_apple_service_id,
    }[provider].strip()


def _secret(value: Any) -> str:
    return str(value.get_secret_value()).strip() if value else ""


def apple_private_key(settings: Settings) -> str:
    """La clé .p8 ; une variable d'environnement sur une ligne peut l'écrire avec « \\n »."""
    return _secret(settings.oauth_apple_private_key).replace("\\n", "\n")


def apple_client_secret(settings: Settings, now: float | None = None) -> str:
    """Le secret client d'Apple : un JWT ES256 signé avec la clé .p8, valable 5 minutes."""
    issued = int(now if now is not None else time.time())
    return jwt.encode(
        {
            "iss": settings.oauth_apple_team_id.strip(),
            "iat": issued,
            "exp": issued + 300,
            "aud": APPLE_ISSUER,
            "sub": settings.oauth_apple_service_id.strip(),
        },
        apple_private_key(settings),
        algorithm="ES256",
        headers={"kid": settings.oauth_apple_key_id.strip()},
    )


def client_secret(settings: Settings, provider: str) -> str:
    if provider == "apple":
        return apple_client_secret(settings)
    if provider == "google":
        return _secret(settings.oauth_google_client_secret)
    return _secret(settings.oauth_microsoft_client_secret)


def redirect_uri(settings: Settings, provider: str) -> str:
    """L'adresse de retour déclarée chez le fournisseur, fixée par la configuration."""
    return f"{settings.public_url.rstrip('/')}/api/auth/oauth/{provider}/callback"


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def pkce_challenge(verifier: str) -> str:
    return _b64url(hashlib.sha256(verifier.encode("ascii")).digest())


# --- Les parcours en cours ---------------------------------------------------------------


@dataclass
class Flow:
    provider: str
    state: str
    nonce: str
    verifier: str
    # La page où revenir après la connexion (`?suite=`), déjà vérifiée.
    next_path: str | None
    # Lier à ce compte (Compte, Connexions) au lieu de se connecter.
    link_account: int | None
    created: float = field(default_factory=time.monotonic)


@dataclass
class Flows:
    items: dict[str, Flow] = field(default_factory=dict)

    def _prune(self) -> None:
        now = time.monotonic()
        for key in [k for k, f in self.items.items() if now - f.created > FLOW_TTL_S]:
            del self.items[key]
        while len(self.items) >= FLOW_MAX:
            # Le plus ancien part : un parcours abandonné ne bloque personne.
            del self.items[next(iter(self.items))]

    def start(self, provider: str, next_path: str | None, link_account: int | None) -> str:
        """Le numéro du parcours (pour le cookie) ; le parcours lui-même reste ici."""
        self._prune()
        key = secrets.token_urlsafe(32)
        self.items[key] = Flow(
            provider=provider,
            state=secrets.token_urlsafe(32),
            nonce=secrets.token_urlsafe(32),
            verifier=secrets.token_urlsafe(48),
            next_path=next_path,
            link_account=link_account,
        )
        return key

    def get(self, key: str) -> Flow | None:
        return self.items.get(key)

    def take(self, key: str | None, provider: str, state: str | None) -> Flow:
        """Le parcours, retiré : il ne sert qu'une fois, même si le `state` est faux."""
        flow = self.items.pop(key, None) if key else None
        if flow is None or time.monotonic() - flow.created > FLOW_TTL_S:
            raise OidcError("parcours inconnu ou expiré", "expire")
        if flow.provider != provider:
            raise OidcError("parcours d'un autre fournisseur")
        if not state or not hmac.compare_digest(flow.state.encode(), state.encode()):
            raise OidcError("state invalide")
        return flow


flows = Flows()


def authorize_url(settings: Settings, provider: str, flow: Flow) -> str:
    params = {
        "client_id": client_id(settings, provider),
        "redirect_uri": redirect_uri(settings, provider),
        "response_type": "code",
        "scope": "openid email" if provider == "apple" else "openid email profile",
        "state": flow.state,
        "nonce": flow.nonce,
        "code_challenge": pkce_challenge(flow.verifier),
        "code_challenge_method": "S256",
    }
    if provider == "apple":
        # Avec la portée « email », Apple renvoie par un formulaire (POST).
        params["response_mode"] = "form_post"
    if provider == "google":
        params["prompt"] = "select_account"
    if provider == "microsoft":
        params["prompt"] = "select_account"
    return f"{endpoints(settings, provider).authorize}?{urlencode(params)}"


# --- L'échange du code et la vérification du jeton d'identité -----------------------------


@dataclass(frozen=True)
class Identity:
    provider: str
    subject: str
    email: str | None
    email_verified: bool


@dataclass
class KeyCache:
    keys: dict[str, tuple[float, dict[str, Any]]] = field(default_factory=dict)

    def put(self, url: str, document: dict[str, Any]) -> None:
        self.keys[url] = (time.monotonic(), document)

    def fresh(self, url: str) -> dict[str, Any] | None:
        found = self.keys.get(url)
        if found and time.monotonic() - found[0] < JWKS_TTL_S:
            return found[1]
        return None


key_cache = KeyCache()


async def _fetch_json(client: httpx.AsyncClient, url: str) -> dict[str, Any]:
    response = await client.get(url, timeout=HTTP_TIMEOUT_S)
    response.raise_for_status()
    data: dict[str, Any] = response.json()
    return data


async def signing_key(client: httpx.AsyncClient, url: str, kid: str | None) -> Any:
    """La clé publique du fournisseur pour ce `kid` ; relue une fois si elle est inconnue (les
    fournisseurs changent de clé)."""
    for attempt in range(2):
        document = key_cache.fresh(url) if attempt == 0 else None
        if document is None:
            document = await _fetch_json(client, url)
            key_cache.put(url, document)
        for key in document.get("keys", []):
            if key.get("kid") == kid:
                return jwt.PyJWK.from_dict(key).key
    raise OidcError("clé de signature inconnue")


async def exchange(
    client: httpx.AsyncClient, settings: Settings, provider: str, code: str, verifier: str
) -> str:
    """Le jeton d'identité contre le code ; le jeton d'accès n'est pas gardé."""
    try:
        response = await client.post(
            endpoints(settings, provider).token,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri(settings, provider),
                "client_id": client_id(settings, provider),
                "client_secret": client_secret(settings, provider),
                "code_verifier": verifier,
            },
            headers={"accept": "application/json"},
            timeout=HTTP_TIMEOUT_S,
        )
    except httpx.HTTPError as exc:
        raise OidcError(f"fournisseur injoignable : {type(exc).__name__}", "indisponible") from None
    if response.status_code != 200:
        # Le corps peut citer le code : seulement le statut et le type d'erreur au journal.
        try:
            kind = str(response.json().get("error", ""))[:60]
        except ValueError:
            kind = ""
        raise OidcError(f"échange refusé ({response.status_code} {kind})")
    token = response.json().get("id_token")
    if not isinstance(token, str) or not token:
        raise OidcError("pas de jeton d'identité")
    return token


def _truthy(value: Any) -> bool:
    # Apple écrit « true » en texte.
    return value is True or (isinstance(value, str) and value.lower() == "true")


async def verify_id_token(
    client: httpx.AsyncClient,
    settings: Settings,
    provider: str,
    token: str,
    nonce: str,
) -> Identity:
    """Signature, émetteur, destinataire, expiration et `nonce` vérifiés ; sinon OidcError."""
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError:
        raise OidcError("jeton d'identité illisible") from None
    algorithm = header.get("alg")
    if algorithm not in ("RS256", "ES256"):
        raise OidcError("algorithme refusé")
    try:
        key = await signing_key(client, endpoints(settings, provider).jwks, header.get("kid"))
    except httpx.HTTPError as exc:
        raise OidcError(f"clés injoignables : {type(exc).__name__}", "indisponible") from None
    try:
        claims: dict[str, Any] = jwt.decode(
            token,
            key=key,
            algorithms=[algorithm],
            audience=client_id(settings, provider),
            leeway=LEEWAY_S,
            options={"require": ["iss", "aud", "exp", "iat", "sub"], "verify_iss": False},
        )
    except jwt.ExpiredSignatureError:
        raise OidcError("jeton d'identité expiré") from None
    except jwt.PyJWTError as exc:
        raise OidcError(f"jeton d'identité refusé : {type(exc).__name__}") from None
    _check_issuer(settings, provider, claims)
    received = claims.get("nonce")
    if not isinstance(received, str) or not hmac.compare_digest(received.encode(), nonce.encode()):
        raise OidcError("nonce invalide")
    email = claims.get("email")
    email = email.strip() if isinstance(email, str) and email.strip() else None
    # Microsoft ne garantit pas l'e-mail (il peut être choisi dans un annuaire) : jamais vérifié.
    verified = (
        provider != "microsoft" and email is not None and _truthy(claims.get("email_verified"))
    )
    return Identity(provider, str(claims["sub"]), email, verified)


def _check_issuer(settings: Settings, provider: str, claims: dict[str, Any]) -> None:
    issuer = str(claims.get("iss", ""))
    if provider == "google":
        ok = issuer in GOOGLE_ISSUERS
    elif provider == "apple":
        ok = issuer == APPLE_ISSUER
    else:
        # « common » : chaque annuaire a son émetteur, qui doit citer l'annuaire du jeton.
        match = MICROSOFT_ISSUER.match(issuer)
        tenant = settings.oauth_microsoft_tenant.strip().lower()
        found = match.group(1) if match else ""
        ok = bool(found) and found == str(claims.get("tid", "")).lower()
        if ok and GUID.match(tenant):
            ok = found == tenant
    if not ok:
        raise OidcError("émetteur refusé")


def apple_first_email(raw_user: str | None) -> str | None:
    """Le champ `user` qu'Apple joint à la première connexion seulement (JSON)."""
    if not raw_user:
        return None
    try:
        data = json.loads(raw_user)
    except ValueError:
        return None
    email = data.get("email") if isinstance(data, dict) else None
    return email.strip() if isinstance(email, str) and email.strip() else None
