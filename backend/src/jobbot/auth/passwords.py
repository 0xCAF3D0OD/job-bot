"""Mots de passe hachés avec scrypt (bibliothèque standard), jamais gardés en clair."""

import base64
import hashlib
import hmac
import secrets

# Paramètres scrypt : environ 16 Mo de mémoire et quelques dizaines de ms par essai.
N, R, P = 2**14, 8, 1
KEY_LENGTH = 64
MIN_LENGTH = 12


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    key = hashlib.scrypt(password.encode(), salt=salt, n=N, r=R, p=P, dklen=KEY_LENGTH)
    return f"scrypt${N}${R}${P}${_b64(salt)}${_b64(key)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt, key = stored.split("$")
        if scheme != "scrypt":
            return False
        expected = base64.b64decode(key)
        found = hashlib.scrypt(
            password.encode(),
            salt=base64.b64decode(salt),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(found, expected)


def check_strength(password: str) -> str | None:
    """Raison du refus, ou None si le mot de passe convient."""
    if len(password) < MIN_LENGTH:
        return f"au moins {MIN_LENGTH} caractères"
    if password.strip() != password:
        return "pas d'espace au début ni à la fin"
    return None
