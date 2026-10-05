"""Priorité des sources de l'adresse d'une entreprise (docs/12 §2)."""

# Une source ne remplace qu'une adresse venue d'une source moins sûre ; la saisie de Kevin
# n'est jamais remplacée.
PRIORITY = {"letter": 1, "web": 2, "registry": 3, "page": 4, "manual": 5}


def weaker_sources(source: str) -> list[str]:
    """Sources qu'une adresse venue de `source` peut remplacer."""
    return [s for s, rank in PRIORITY.items() if rank < PRIORITY[source]]
