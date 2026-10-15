"""« 1 offre », « 3 offres » : de vrais accords plutôt que « offre(s) » (docs/43 n° 2)."""


def plural(count: int, one: str, many: str) -> str:
    return f"{count} {one if count == 1 else many}"
