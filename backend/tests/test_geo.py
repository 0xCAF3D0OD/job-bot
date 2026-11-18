"""Le point d'un lieu d'annonce, pour le filtre « Distance » (issue #468) : pas de devinette."""

import pytest

from jobbot.core.geo import Point, distance_km, locate, locate_zip

RENENS = locate_zip("1020")


def km(location: str) -> float | None:
    point = locate(location)
    return None if point is None or RENENS is None else round(distance_km(RENENS, point), 1)


def test_home_from_postcode() -> None:
    assert RENENS is not None
    assert Point(46.5353, 6.5897) == RENENS
    assert locate_zip("9999") is None and locate_zip(None) is None


@pytest.mark.parametrize(
    ("location", "expected"),
    [
        ("1020 Renens VD", 0.0),
        ("Renens", 0.0),
        ("Lausanne", 4.1),
        ("Lausanne 80-100 %", 4.1),
        ("Lausanne, Vaud", 4.1),
        ("Morges, VD", 7.7),
        ("Genève", 50.2),
        ("Berne, Suisse", 77.9),
        ("Bienne", 84.5),
        ("Biel/Bienne", 84.5),
        ("Zurich (ZH)", 175.0),
        ("8001 Zürich", 174.9),
        ("Buchs AG", 148.4),
        ("Wil SG", 213.7),
    ],
)
def test_known_places(location: str, expected: float) -> None:
    assert km(location) == expected


@pytest.mark.parametrize(
    "location",
    [
        None,
        "",
        "Région lémanique",
        "Suisse romande",
        "Remote",
        # Le même nom dans plusieurs cantons, sans canton : on ne choisit pas.
        "Buchs",
        "Wil",
        "Ecublens",
        # Deux lieux loin l'un de l'autre : on ne choisit pas.
        "Neuchâtel / Berne",
    ],
)
def test_unclear_places_stay_unknown(location: str | None) -> None:
    assert locate(location) is None


def test_no_external_call(monkeypatch: pytest.MonkeyPatch) -> None:
    """Le fichier du dépôt suffit : aucun accès réseau, même au premier chargement."""
    import socket

    from jobbot.core import geo

    geo._index.cache_clear()

    def refuse(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("appel réseau")

    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)
    assert geo.locate("Lausanne") is not None
