"""Où se trouve une offre, pour le filtre « Distance depuis… » (issue #468, Kevin, 18.11.2026).

Les coordonnées viennent d'une copie des numéros postaux suisses de GeoNames (geonames.org,
CC BY 4.0), dans `jobbot/data/geonames/` avec son README (source, version, licence). Aucun appel
externe : le fichier est lu une fois, au premier besoin.

Pas de devinette : un lieu donne des coordonnées seulement s'il désigne un endroit sans ambiguïté.
- un numéro postal connu (« 1020 Renens VD ») ;
- sinon un nom de localité ou de commune ; s'il existe dans plusieurs cantons, le canton cité
  (« Buchs AG ») ou connu de la ville tranche ; sans canton, le nom n'est retenu que si tous les
  endroits qui le portent sont à moins de 10 km les uns des autres (les numéros d'une même ville).
Sinon : aucune coordonnée, et l'offre va dans « Lieu non précisé », jamais exclue en silence.
"""

import csv
import io
import math
import re
from dataclasses import dataclass
from functools import cache
from importlib import resources

from jobbot.core.places import ALIASES, CITY_CANTON, _segments, canton_in, place_key

DATA = "zipcodes.ch.csv"
# Au-delà, deux endroits du même nom ne sont pas « la même ville » : on ne choisit pas.
SAME_PLACE_KM = 10.0
EARTH_KM = 6371.0
_ZIP = re.compile(r"(?<![\d.,])([1-9]\d{3})(?![\d.,%])")


@dataclass(frozen=True)
class Point:
    lat: float
    lon: float


def distance_km(a: Point, b: Point) -> float:
    """La distance à vol d'oiseau (formule de haversine), en kilomètres."""
    p1, p2 = math.radians(a.lat), math.radians(b.lat)
    dp, dl = p2 - p1, math.radians(b.lon - a.lon)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_KM * math.asin(math.sqrt(h))


def _mean(points: list[Point]) -> Point:
    return Point(sum(p.lat for p in points) / len(points), sum(p.lon for p in points) / len(points))


def _name_key(name: str) -> str:
    """« Biel/Bienne 6 » → biel ; « Renens VD 1 » → renens ; « St. Gallen » → st gallen."""
    key = place_key(re.sub(r"\s+\d+$", "", name))
    return ALIASES.get(key, key)


@dataclass(frozen=True)
class _Index:
    by_zip: dict[str, Point]
    # nom → canton → point moyen de ses numéros postaux
    by_name: dict[str, dict[str, Point]]


@cache
def _index() -> _Index:
    zips: dict[str, list[Point]] = {}
    names: dict[str, dict[str, list[Point]]] = {}
    source = resources.files("jobbot.data.geonames").joinpath(DATA)
    for row in csv.DictReader(io.StringIO(source.read_text(encoding="utf-8"))):
        try:
            point = Point(float(row["latitude"]), float(row["longitude"]))
        except (TypeError, ValueError):
            continue
        zips.setdefault(row["zipcode"], []).append(point)
        canton = row["state_code"]
        for name in {row["place"], row["community"]}:
            key = _name_key(name or "")
            if key:
                names.setdefault(key, {}).setdefault(canton, []).append(point)
    return _Index(
        by_zip={z: _mean(p) for z, p in zips.items()},
        by_name={k: {c: _mean(p) for c, p in by_c.items()} for k, by_c in names.items()},
    )


def locate_zip(postcode: str | None) -> Point | None:
    """Le point d'un numéro postal suisse (le domicile saisi dans les coordonnées)."""
    return _index().by_zip.get((postcode or "").strip())


def locate(location: str | None) -> Point | None:
    """Le point d'un lieu d'annonce, ou None s'il n'est pas reconnu sans ambiguïté."""
    if not location:
        return None
    index = _index()
    for match in _ZIP.finditer(location):
        if match.group(1) in index.by_zip:
            return index.by_zip[match.group(1)]
    canton = canton_in(location)
    keys = [place_key(location)] + [
        ALIASES.get(k, k) for k in (" ".join(w) for w in _segments(location))
    ]
    found = [
        p for p in (_by_name(index, k, canton) for k in dict.fromkeys(k for k in keys if k)) if p
    ]
    # Deux lieux différents (« Neuchâtel / Berne ») : on ne choisit pas.
    if found and all(distance_km(found[0], p) <= SAME_PLACE_KM for p in found):
        return found[0]
    return None


def _by_name(index: _Index, key: str, canton: str | None) -> Point | None:
    by_canton = index.by_name.get(key)
    if not by_canton:
        return None
    wanted = canton or CITY_CANTON.get(key)
    if wanted:
        return by_canton.get(wanted)
    points = list(by_canton.values())
    centre = _mean(points)
    if all(distance_km(centre, p) <= SAME_PLACE_KM / 2 for p in points):
        return centre
    return None
