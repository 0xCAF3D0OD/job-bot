"""Les lieux du filtre (bug du 2026-10-29 : « Berne » écartée avec « bern » dans les lieux).

Une clé de lieu, la même côté annonce et côté critères : minuscules, sans accents, variantes
français, allemand, italien et anglais ramenées à un seul nom (Bern, Berne → bern), et le texte
parasite de l'annonce retiré (taux, pays, codes postaux : « Zurich 80-100 % » → zurich).
Les cantons, par leur abréviation (BE) ou leur nom (Valais, Wallis), comprennent toutes
leurs communes.

Distinct de normalize_location (core/normalize.py), qui sert à l'empreinte de dédoublonnage et ne
doit pas changer.
"""

import re

from jobbot.core.normalize import normalize_text

CANTONS = {
    "AG", "AI", "AR", "BE", "BL", "BS", "FR", "GE", "GL", "GR", "JU", "LU", "NE", "NW",
    "OW", "SG", "SH", "SO", "SZ", "TG", "TI", "UR", "VD", "VS", "ZG", "ZH",
}  # fmt: skip

# Les variantes d'une même ville, ramenées à un nom (normalisé : minuscules, sans accents).
_CITY_ALIASES = {
    "bern": ("berne", "berna"),
    "zurich": ("zuerich", "zurigo", "zuri"),
    "geneve": ("genf", "ginevra", "geneva", "genevra"),
    "biel": ("bienne", "biel bienne", "bienne biel"),
    "basel": ("bale", "basilea", "basle"),
    "luzern": ("lucerne", "lucerna"),
    "fribourg": ("freiburg", "friburgo", "freiburg im uechtland"),
    "neuchatel": ("neuenburg",),
    "solothurn": ("soleure", "soletta"),
    "schaffhausen": ("schaffhouse", "sciaffusa"),
    "st gallen": ("sankt gallen", "saint gall", "st gall", "san gallo"),
    "zug": ("zoug", "zugo"),
    "chur": ("coire", "coira"),
    "sion": ("sitten",),
    "sierre": ("siders",),
    "thun": ("thoune",),
    "murten": ("morat",),
    "delemont": ("delsberg",),
    "bellinzona": ("bellinzone",),
    "lugano": ("lugan",),
    "winterthur": ("winterthour",),
    "aarau": ("arau",),
    "baden": (),
    "lausanne": ("losanna",),
    "montreux": (),
    "yverdon les bains": ("yverdon",),
    "la chaux de fonds": ("chaux de fonds",),
}
ALIASES = {
    variant: name for name, variants in _CITY_ALIASES.items() for variant in (name, *variants)
}

# Les noms de canton, dans les langues du pays, vers leur abréviation. Les cantons qui portent le
# nom de leur chef-lieu (Berne, Zurich, Genève…) restent des villes : on les saisit par BE, ZH, GE.
_CANTON_NAMES = {
    "VD": ("vaud", "waadt"),
    "VS": ("valais", "wallis", "vallese"),
    "TI": ("tessin", "ticino"),
    "GR": ("grisons", "graubunden", "graubuenden", "grigioni"),
    "AG": ("argovie", "aargau", "argovia"),
    "TG": ("thurgovie", "thurgau", "turgovia"),
    "JU": ("jura", "canton du jura"),
    "BL": ("bale campagne", "basel landschaft", "baselland"),
    "BS": ("bale ville", "basel stadt"),
    "AR": ("appenzell rhodes exterieures", "appenzell ausserrhoden"),
    "AI": ("appenzell rhodes interieures", "appenzell innerrhoden"),
    "NW": ("nidwald", "nidwalden"),
    "OW": ("obwald", "obwalden"),
    "SZ": ("schwyz",),
    "UR": ("uri",),
    "GL": ("glaris", "glarus"),
}
CANTON_NAMES = {name: code for code, names in _CANTON_NAMES.items() for name in names}

# Le canton des villes les plus fréquentes, pour une annonce qui ne donne que la ville.
CITY_CANTON = {
    "bern": "BE", "biel": "BE", "thun": "BE", "zurich": "ZH", "winterthur": "ZH",
    "geneve": "GE", "basel": "BS", "lausanne": "VD", "montreux": "VD", "yverdon les bains": "VD",
    "luzern": "LU", "fribourg": "FR", "neuchatel": "NE", "la chaux de fonds": "NE",
    "solothurn": "SO", "schaffhausen": "SH", "st gallen": "SG", "zug": "ZG", "chur": "GR",
    "sion": "VS", "sierre": "VS", "murten": "FR", "delemont": "JU", "bellinzona": "TI",
    "lugano": "TI", "aarau": "AG", "baden": "AG",
}  # fmt: skip

# Taux d'activité (« 80-100 % », « 80-100% », « 100 % ») et texte parasite d'un lieu.
_RATE = re.compile(
    r"\d{1,3}\s*%?\s*(?:-|\u2013|\u2014|à|a|bis|to)\s*\d{1,3}\s*%|\d{1,3}\s*%", re.IGNORECASE
)
_NOISE = {
    "suisse", "schweiz", "switzerland", "svizzera", "svizra", "ch", "swiss",
    "canton", "kanton", "cantone", "region", "regio", "umgebung", "und", "et", "environs",
    "area", "greater", "ville", "stadt", "city",
}  # fmt: skip


def _segments(location: str) -> list[list[str]]:
    """Les morceaux d'un lieu, mots normalisés, sans taux, codes postaux ni texte parasite."""
    text = _RATE.sub(" ", location)
    text = re.sub(r"\(([^)]*)\)", r", \1", text)
    out = []
    for part in re.split(r"[,;/|\n]| - | \u2013 ", text):
        words = [
            word
            for word in normalize_text(part).split()
            if word not in _NOISE and not re.fullmatch(r"\d{4,5}|\d{1,3}", word)
        ]
        if words:
            out.append(words)
    return out


def place_key(location: str | None) -> str:
    """La ville d'une annonce ou d'un critère, sous son nom unique.

    « Zurich 80-100 % » → zurich ; « Berne, Suisse » → bern.
    """
    if not location:
        return ""
    for words in _segments(location):
        while len(words) > 1 and words[-1].upper() in CANTONS:
            words = words[:-1]
        if len(words) == 1 and words[0].upper() in CANTONS:
            continue
        key = " ".join(words)
        return ALIASES.get(key, key)
    return ""


def canton_in(location: str | None) -> str | None:
    """Le canton nommé dans le lieu : abréviation (« Lausanne, VD ») ou nom (« Sion, Valais »)."""
    if not location:
        return None
    for match in re.finditer(r"(?<![A-Za-z])([A-Z]{2})(?![A-Za-z])", location):
        if match.group(1) in CANTONS:
            return match.group(1)
    for words in _segments(location):
        name = " ".join(words)
        if name in CANTON_NAMES:
            return CANTON_NAMES[name]
    return None


# Les chefs-lieux qui donnent leur nom au canton : saisis dans les critères, ils valent le canton
# entier (« geneve » accepte Meyrin ; « zurich », Winterthour), car un canton comprend ses communes.
CANTON_CAPITALS = {
    "bern": "BE", "zurich": "ZH", "geneve": "GE", "fribourg": "FR", "neuchatel": "NE",
    "luzern": "LU", "zug": "ZG", "solothurn": "SO", "schaffhausen": "SH", "st gallen": "SG",
}  # fmt: skip


def criterion_place(entry: str) -> tuple[str, str]:
    """Un lieu saisi dans les critères : (« canton », BE) ou (« ville », lausanne)."""
    raw = entry.strip()
    if raw.upper() in CANTONS:
        return "canton", raw.upper()
    name = normalize_text(raw)
    if name in CANTON_NAMES:
        return "canton", CANTON_NAMES[name]
    city = place_key(raw)
    if city in CANTON_CAPITALS:
        return "canton", CANTON_CAPITALS[city]
    return "city", city
