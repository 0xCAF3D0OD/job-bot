"""Priorité des sources de l'adresse d'une entreprise (docs/12 §2)."""

# Une source ne remplace qu'une adresse venue d'une source moins sûre ; la saisie de Kevin
# n'est jamais remplacée.
PRIORITY = {"letter": 1, "registry": 2, "page": 3, "manual": 4}


def weaker_sources(source: str) -> list[str]:
    """Sources qu'une adresse venue de `source` peut remplacer."""
    return [s for s, rank in PRIORITY.items() if rank < PRIORITY[source]]
