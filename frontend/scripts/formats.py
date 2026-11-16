"""Le format que vérifie un audit d'écran : AUDIT_FORMAT=telephone (jusqu'à 820 px), ordinateur (dès 821 px), ou
rien pour les deux. La CI lance chaque format dans son propre contrôle, et seulement si la PR le touche
(scripts/ci_formats.py, décision de Kevin du 14.11.2026) ; en local, sans AUDIT_FORMAT, rien ne change."""

import os

PHONE_MAX = 820  # la limite de usePhone.ts et des styles
FORMAT = os.environ.get("AUDIT_FORMAT", "").strip()
if FORMAT not in ("", "telephone", "ordinateur"):
    raise SystemExit(f"AUDIT_FORMAT={FORMAT!r} : telephone, ordinateur ou rien")


def checked(width: int) -> bool:
    """Cette largeur est-elle vérifiée par ce passage ?"""
    if FORMAT == "telephone":
        return width <= PHONE_MAX
    if FORMAT == "ordinateur":
        return width > PHONE_MAX
    return True
