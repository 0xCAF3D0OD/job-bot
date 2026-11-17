"""L'échelle unique de la note (décision de Kevin du 17.11.2026, LISEZMOI §65) : 85 Très proche,
75 Proche, 50 À creuser, en dessous Loin. Les mêmes seuils que `SCORE_SCALE` de l'interface
(frontend/src/format.ts) : le cercle, « M'avertir dès », le filtre Note et le Bilan."""

VERY_CLOSE = 85
CLOSE = 75
DIG = 50
# Les trois valeurs de « M'avertir dès » ; le défaut est « Proche ».
NOTIFY_LEVELS = (DIG, CLOSE, VERY_CLOSE)
NOTIFY_DEFAULT = CLOSE


def word(score: int) -> str:
    """Les mots de la note (docs/121 §C.5)."""
    if score >= VERY_CLOSE:
        return "Très proche"
    if score >= CLOSE:
        return "Proche"
    if score >= DIG:
        return "À creuser"
    return "Loin"


def nearest_level(value: int) -> int:
    """Le niveau de « M'avertir dès » le plus proche d'une valeur d'avant (70 → 75, 55 → 50,
    80 → 85) ; à égalité, le plus haut."""
    return min(NOTIFY_LEVELS, key=lambda level: (abs(level - value), -level))
