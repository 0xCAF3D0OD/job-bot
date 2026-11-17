"""L'échelle unique de la note (§65, Kevin 17.11.2026) : les mots aux limites et le niveau le plus
proche de « M'avertir dès »."""

import pytest

from jobbot.insights.service import _score_band
from jobbot.scoring.scale import NOTIFY_DEFAULT, nearest_level, word


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (49, "Loin"),
        (50, "À creuser"),
        (74, "À creuser"),
        (75, "Proche"),
        (84, "Proche"),
        (85, "Très proche"),
    ],
)
def test_mots_aux_limites(score: int, expected: str) -> None:
    assert word(score) == expected


@pytest.mark.parametrize(
    ("value", "level"),
    [
        (50, 50),
        (75, 75),
        (85, 85),
        (70, 75),
        (55, 50),
        (80, 85),
        (62, 50),
        (63, 75),
        (0, 50),
        (100, 85),
    ],
)
def test_niveau_le_plus_proche(value: int, level: int) -> None:
    assert nearest_level(value) == level


def test_defaut_proche() -> None:
    assert NOTIFY_DEFAULT == 75


@pytest.mark.parametrize(
    ("score", "key"),
    [(49, "far"), (50, "dig"), (74, "dig"), (75, "close"), (85, "close"), (None, "none")],
)
def test_tranches_du_bilan(score: int | None, key: str) -> None:
    assert _score_band(score)[0] == key
