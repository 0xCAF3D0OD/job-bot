"""Jours fériés par canton et jour ouvrable suivant (MODIFICATIONS du 9 novembre, §11).

Les recherches d'un mois se remettent au plus tard le 5 du mois suivant (art. 26 al. 2 OACI) ;
si ce jour tombe un samedi, un dimanche ou un jour férié du canton de l'ORP de la personne,
l'échéance passe au premier jour ouvrable qui suit. Le canton vient du NPA du domicile (Vaud par
défaut, décision de Kevin du 9 novembre).

Les listes reprennent les jours fériés officiels (lois cantonales sur le repos public) ; les fêtes
qui ne valent que dans une partie du canton ne sont pas retenues.
"""

from datetime import date, timedelta

CANTONS = (
    "AG", "AI", "AR", "BE", "BL", "BS", "FR", "GE", "GL", "GR", "JU", "LU", "NE",
    "NW", "OW", "SG", "SH", "SO", "SZ", "TG", "TI", "UR", "VD", "VS", "ZG", "ZH",
)  # fmt: skip
DEFAULT_CANTON = "VD"

_ALL = set(CANTONS)
# Fêtes cantonales : quels cantons les chôment.
_BERCHTOLD = {"AG", "BE", "FR", "GL", "JU", "LU", "OW", "SH", "SO", "TG", "VD", "ZG", "ZH"}
_EPIPHANY = {"SZ", "TI", "UR"}
_SAINT_JOSEPH = {"NW", "SZ", "TI", "UR", "VS"}
_LABOUR_DAY = {"BL", "BS", "JU", "NE", "SH", "TG", "TI", "ZH"}
_GOOD_FRIDAY = _ALL - {"TI", "VS"}
_EASTER_MONDAY = _ALL - {"VS"}
_WHIT_MONDAY = _ALL - {"VS"}
_CORPUS_CHRISTI = {"AI", "FR", "JU", "LU", "NW", "OW", "SO", "SZ", "TI", "UR", "VS", "ZG"}
_ASSUMPTION = {"AI", "FR", "JU", "LU", "NW", "OW", "SO", "SZ", "TI", "UR", "VS", "ZG"}
_ALL_SAINTS = {
    "AI", "FR", "GL", "JU", "LU", "NW", "OW", "SG", "SO", "SZ", "TI", "UR", "VS", "ZG",
}  # fmt: skip
_IMMACULATE = {"AI", "LU", "NW", "OW", "SZ", "TI", "UR", "VS", "ZG"}
_SAINT_STEPHEN = _ALL - {"GE", "JU", "NE", "VD", "VS"}


def easter(year: int) -> date:
    """Dimanche de Pâques (calendrier grégorien, algorithme de Meeus)."""
    a, b, c = year % 19, year // 100, year % 100
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7  # noqa: E741
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def _sunday(year: int, month: int, nth: int) -> date:
    first = date(year, month, 1)
    return first + timedelta(days=(6 - first.weekday()) % 7 + 7 * (nth - 1))


def holidays(year: int, canton: str = DEFAULT_CANTON) -> set[date]:
    """Les jours fériés d'une année dans un canton (un canton inconnu compte comme Vaud)."""
    canton = canton if canton in _ALL else DEFAULT_CANTON
    sunday = easter(year)
    days = {
        date(year, 1, 1),
        sunday + timedelta(days=39),  # Ascension
        date(year, 8, 1),
        date(year, 12, 25),
    }
    movable = [
        (_GOOD_FRIDAY, sunday - timedelta(days=2)),
        (_EASTER_MONDAY, sunday + timedelta(days=1)),
        (_WHIT_MONDAY, sunday + timedelta(days=50)),
        (_CORPUS_CHRISTI, sunday + timedelta(days=60)),
    ]
    fixed = [
        (_BERCHTOLD, date(year, 1, 2)),
        (_EPIPHANY, date(year, 1, 6)),
        (_SAINT_JOSEPH, date(year, 3, 19)),
        (_LABOUR_DAY, date(year, 5, 1)),
        (_ASSUMPTION, date(year, 8, 15)),
        (_ALL_SAINTS, date(year, 11, 1)),
        (_IMMACULATE, date(year, 12, 8)),
        (_SAINT_STEPHEN, date(year, 12, 26)),
        ({"NE"}, date(year, 3, 1)),
        ({"JU"}, date(year, 6, 23)),
        ({"TI"}, date(year, 6, 29)),
        ({"OW"}, date(year, 9, 25)),
        ({"GE"}, date(year, 12, 31)),
        # Jeûne genevois : le jeudi qui suit le premier dimanche de septembre.
        ({"GE"}, _sunday(year, 9, 1) + timedelta(days=4)),
        # Lundi du Jeûne fédéral : le lendemain du troisième dimanche de septembre.
        ({"VD"}, _sunday(year, 9, 3) + timedelta(days=1)),
        # Näfelser Fahrt : le premier jeudi d'avril.
        ({"GL"}, date(year, 4, 1) + timedelta(days=(3 - date(year, 4, 1).weekday()) % 7)),
    ]
    days.update(day for cantons, day in movable + fixed if canton in cantons)
    return days


def working_day(day: date, canton: str = DEFAULT_CANTON) -> date:
    """Le jour même s'il est ouvrable, sinon le premier jour ouvrable qui suit."""
    while day.weekday() >= 5 or day in holidays(day.year, canton):
        day += timedelta(days=1)
    return day


# Le canton d'un NPA suisse, par tranches (les NPA suivent les régions postales, pas les frontières
# cantonales : quelques communes en bordure peuvent tomber dans le canton voisin ; les jours fériés
# ne diffèrent alors qu'à la marge). Première tranche qui contient le NPA.
_NPA: list[tuple[int, int, str]] = [
    (1200, 1259, "GE"), (1290, 1290, "GE"), (1298, 1298, "GE"), (1000, 1469, "VD"),
    (1470, 1489, "FR"), (1490, 1599, "VD"), (1607, 1610, "VD"), (1600, 1799, "FR"),
    (1880, 1885, "VD"), (1870, 1899, "VS"), (1800, 1869, "VD"), (1900, 1999, "VS"),
    (2000, 2499, "NE"), (2500, 2799, "BE"), (2800, 2999, "JU"), (3900, 3999, "VS"),
    (3000, 3899, "BE"), (4000, 4099, "BS"), (4100, 4499, "BL"), (4500, 4799, "SO"),
    (4800, 4899, "AG"), (4900, 4999, "BE"), (5000, 5999, "AG"), (6055, 6078, "OW"),
    (6000, 6299, "LU"), (6300, 6349, "ZG"), (6370, 6399, "NW"), (6350, 6369, "LU"),
    (6400, 6459, "SZ"), (6460, 6499, "UR"), (6535, 6565, "GR"), (6500, 6999, "TI"),
    (7000, 7799, "GR"), (8200, 8299, "SH"), (8500, 8599, "TG"), (8750, 8799, "GL"),
    (8840, 8849, "SZ"), (8000, 8999, "ZH"), (9050, 9059, "AI"), (9100, 9199, "AR"),
    (9500, 9599, "TG"), (9000, 9999, "SG"),
]  # fmt: skip


def canton_of_postcode(postcode: str | None) -> str | None:
    """Le canton d'un NPA à quatre chiffres, ou None."""
    if not postcode or not postcode.strip().isdigit() or len(postcode.strip()) != 4:
        return None
    number = int(postcode.strip())
    return next((canton for low, high, canton in _NPA if low <= number <= high), None)
