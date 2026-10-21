"""Une adresse de réception par compte (docs/65 §3).

La plateforme lit une seule boîte. L'exploitant y reçoit à l'adresse de la boîte ; un compte
invité à « boite+code@domaine », que la boîte reçoit aussi (adressage « plus » de Gmail et
de la plupart des fournisseurs). À la collecte, l'adresse de destination dit à quel compte
l'e-mail appartient. Aucun mot de passe de boîte d'une autre personne n'est gardé.
"""

import re
import secrets
import string
import unicodedata

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot import accounts
from jobbot.db.models import User
from jobbot.settings import Settings

CODE_ALPHABET = string.ascii_lowercase + string.digits
CODE_LENGTH = 8


def base_address(settings: Settings) -> str | None:
    address = (settings.mail_address or settings.imap_user).strip().lower()
    return address if "@" in address else None


def plus_address(base: str, code: str) -> str:
    local, _, domain = base.partition("@")
    return f"{local.split('+')[0]}+{code}@{domain}"


def alert_domain(settings: Settings) -> str | None:
    """Le domaine des adresses d'alerte des invités (docs/104), s'il est réglé."""
    domain = settings.alert_domain.strip().lower().lstrip("@").rpartition("@")[2]
    return domain if "." in domain else None


def alert_box(settings: Settings) -> str | None:
    """La boîte du domaine, si le réglage est une adresse entière (« alertes@joba1.ch »,
    0.82.3) : chez un hébergeur sans redirection « catch-all », l'invité reçoit à
    « alertes+nom-code@joba1.ch », que la seule redirection de « alertes@ » fait suivre."""
    value = settings.alert_domain.strip().lower().lstrip("@")
    box = value.partition("@")[0] if "@" in value else ""
    return box.split("+")[0] or None


def name_slug(username: str) -> str:
    """Le nom du compte pour une adresse : minuscules, sans accents, lettres et chiffres."""
    plain = unicodedata.normalize("NFKD", username).encode("ascii", "ignore").decode().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", plain).strip("-")[:20].strip("-")
    return slug or "compte"


def domain_address(domain: str, username: str, code: str, box: str | None = None) -> str:
    # Le code reste à la fin, après le dernier tiret : c'est lui qui désigne le compte.
    local = f"{name_slug(username)}-{code}"
    return f"{box}+{local}@{domain}" if box else f"{local}@{domain}"


async def account_address(session: AsyncSession, settings: Settings) -> str | None:
    """L'adresse à donner aux sites pour le compte en cours ; créée à la première demande."""
    base = base_address(settings)
    if await accounts.is_owner(session):
        return base if base is not None and settings.imap_configured else None
    domain = alert_domain(settings)
    # Un invité reçoit sur le domaine des alertes, lu par la boîte des invités (docs/113) ou
    # par celle de l'exploitant ; sans domaine, à « boite+code@… » de l'exploitant.
    if not (settings.imap_configured or (domain and settings.guest_imap_configured)):
        return None
    if domain is None and base is None:
        return None
    user = await session.get_one(User, accounts.current())
    if user.mail_code is None:
        user.mail_code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))
        await session.flush()
    if domain is not None:
        return domain_address(domain, user.username, user.mail_code, alert_box(settings))
    assert base is not None
    return plus_address(base, user.mail_code)


async def recipients_map(session: AsyncSession) -> dict[str, int]:
    """Code d'adresse → compte, pour les comptes qui en ont un."""
    rows = await session.execute(select(User.mail_code, User.id).where(User.mail_code.is_not(None)))
    return {str(code): int(user_id) for code, user_id in rows}


def route(
    recipients: tuple[str, ...],
    base: str | None,
    codes: dict[str, int],
    owner: int,
    domain: str | None = None,
) -> int | None:
    """Le compte d'un e-mail selon ses destinataires : un code connu désigne son compte ; un
    code inconnu, personne (l'e-mail n'est pas rangé) ; sinon l'exploitant, comme avant. Le
    code se lit dans « boite+code@… » ou, avec le domaine des alertes, dans « nom-code@domaine »."""
    unknown = False
    if domain is not None:
        for address in recipients:
            name, _, host = address.lower().partition("@")
            if host != domain:
                continue
            code = name.rpartition("-")[2]
            if code in codes:
                return codes[code]
            unknown = True
    if base is not None:
        local, _, base_domain = base.partition("@")
        local = local.split("+")[0]
        for address in recipients:
            name, _, host = address.lower().partition("@")
            if host != base_domain or "+" not in name or name.split("+")[0] != local:
                continue
            code = name.partition("+")[2]
            if code in codes:
                return codes[code]
            unknown = True
    if unknown:
        return None
    return owner
