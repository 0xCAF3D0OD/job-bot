"""« Se connecter avec jobA1 » depuis Get'emAll (docs/140) : code d'autorisation, échange, jeton.

Schéma « code d'autorisation » d'OAuth 2 avec PKCE (S256), sans OpenID Connect :

1. la personne, connectée à jobA1, autorise Get'emAll : jobA1 tire un code `jbc_…` de 60 s ;
2. le serveur de Get'emAll échange ce code, avec son secret client et le `code_verifier`,
   contre un identifiant propre à Get'emAll et un jeton `jbg_…` qui ne sert qu'à lire le suivi.

Du code et du jeton, seule l'empreinte est gardée. L'identifiant est tiré au hasard et reste le
même d'une autorisation à l'autre : jamais l'id du compte jobA1.
"""

import base64
import hashlib
import hmac
import re
import secrets
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, or_, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from jobbot import accounts
from jobbot.auth.service import token_hash
from jobbot.db.models import PartnerCode, PartnerLink
from jobbot.llm.redact import _names
from jobbot.settings import Settings

PARTNER = "getemall"
CODE_PREFIX = "jbc_"
TOKEN_PREFIX = "jbg_"
CODE_TTL = timedelta(seconds=60)
# PKCE (RFC 7636) : le défi est l'empreinte SHA-256 du vérificateur, en base64url sans « = ».
CHALLENGE = re.compile(r"^[A-Za-z0-9_-]{43}$")
VERIFIER = re.compile(r"^[A-Za-z0-9._~-]{43,128}$")
STATE = re.compile(r"^[A-Za-z0-9._~-]{8,200}$")


class InvalidCode(Exception):
    """Code inconnu, déjà lu, expiré, d'une autre adresse de retour, ou PKCE faux."""


@dataclass(frozen=True)
class Granted:
    # Pour le journal seulement : jamais rendu à Get'emAll.
    account: int
    subject: str
    token: str
    orp: bool


def secret_matches(settings: Settings, given: str) -> bool:
    """Le secret client de Get'emAll, comparé en temps constant."""
    expected = settings.getemall_client_secret
    if expected is None or not expected.get_secret_value().strip():
        return False
    return hmac.compare_digest(expected.get_secret_value().encode(), given.encode())


def pkce_matches(verifier: str, challenge: str) -> bool:
    if not VERIFIER.match(verifier):
        return False
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    computed = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return hmac.compare_digest(computed, challenge)


async def drop_old_codes(session: AsyncSession) -> None:
    """Un code lu ou expiré ne sert plus à rien : effacé à l'échange ou à l'autorisation
    suivante du compte (docs/140 §5)."""
    await session.execute(
        delete(PartnerCode).where(
            or_(PartnerCode.used_at.is_not(None), PartnerCode.expires_at < func.now())
        )
    )


async def create_code(
    session: AsyncSession, *, redirect_uri: str, code_challenge: str, orp: bool
) -> str:
    """Un code pour le compte connecté. L'adresse de retour a déjà été comparée à la liste."""
    await drop_old_codes(session)
    code = CODE_PREFIX + secrets.token_urlsafe(16)
    session.add(
        PartnerCode(
            partner=PARTNER,
            token_hash=token_hash(code),
            code_challenge=code_challenge,
            redirect_uri=redirect_uri,
            orp=orp,
            expires_at=datetime.now(UTC) + CODE_TTL,
        )
    )
    await session.flush()
    return code


async def exchange(
    sessionmaker: async_sessionmaker[AsyncSession],
    *,
    code: str,
    verifier: str,
    redirect_uri: str,
) -> Granted:
    """Brûle le code, vérifie le PKCE et l'adresse de retour, puis rend l'identifiant et un
    nouveau jeton. Un jeton déjà donné à Get'emAll pour ce compte cesse de servir."""
    if not code.startswith(CODE_PREFIX):
        raise InvalidCode
    async with sessionmaker.begin() as session:
        row = (
            await session.execute(
                text("select * from take_partner_code(:hash)"), {"hash": token_hash(code)}
            )
        ).first()
    if (
        row is None
        or row.partner != PARTNER
        or row.expired
        or not hmac.compare_digest(row.redirect_uri, redirect_uri)
        or not pkce_matches(verifier, row.code_challenge)
    ):
        raise InvalidCode
    token = TOKEN_PREFIX + secrets.token_urlsafe(32)
    with accounts.use(int(row.user_id)):
        async with sessionmaker.begin() as session:
            subject = await session.scalar(
                insert(PartnerLink)
                .values(
                    partner=PARTNER,
                    subject=secrets.token_urlsafe(24),
                    token_hash=token_hash(token),
                    orp=row.orp,
                )
                .on_conflict_do_update(
                    index_elements=["user_id", "partner"],
                    set_={
                        "token_hash": token_hash(token),
                        "orp": row.orp,
                        "authorized_at": func.now(),
                        "last_used_at": None,
                        "revoked_at": None,
                    },
                )
                .returning(PartnerLink.subject)
            )
            await drop_old_codes(session)
    assert subject is not None
    return Granted(account=int(row.user_id), subject=subject, token=token, orp=bool(row.orp))


async def authenticate(session: AsyncSession, token: str | None) -> PartnerLink | None:
    """La liaison de ce jeton, au nom du compte déjà retrouvé (`account_of_partner_token`)."""
    if not token or not token.startswith(TOKEN_PREFIX):
        return None
    link = await session.scalar(
        select(PartnerLink).where(
            PartnerLink.token_hash == token_hash(token),
            PartnerLink.partner == PARTNER,
            PartnerLink.revoked_at.is_(None),
        )
    )
    if link is not None:
        link.last_used_at = datetime.now(UTC)
    return link


async def current_link(session: AsyncSession) -> PartnerLink | None:
    return await session.scalar(select(PartnerLink).where(PartnerLink.partner == PARTNER))


async def revoke(session: AsyncSession) -> bool:
    """« Retirer » : le jeton cesse de servir ; l'identifiant reste, pour une prochaine fois."""
    link = await current_link(session)
    if link is None or link.revoked_at is not None:
        return False
    link.revoked_at = datetime.now(UTC)
    return True


def without_names(value: str, names: Iterable[str | None]) -> str:
    """Retire les noms des personnes de contact notées (docs/140 §3), en plus de `redact`."""
    for name in sorted({part for n in names for part in _names(n)}, key=len, reverse=True):
        value = re.sub(rf"\b{re.escape(name)}\b", "[nom retiré]", value, flags=re.IGNORECASE)
    return value
