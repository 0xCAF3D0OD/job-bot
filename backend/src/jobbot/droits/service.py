"""« Tes droits » (§72r, §72t, §72v) : ta situation, gardée dans ton compte, et ses chiffres.

Niveau (docs/regles-securite-donnees.md, D-1) : la situation de chômage est **sensible**. Rangée
dans la table `settings` du compte (clé `droits_situation`) : cloisonnée par la RLS (C-1), dans
l'export (V-2), effacée avec le compte (V-3). Jamais journalisée (J-1), jamais envoyée à l'IA
(I-1) : l'Assistant écrit `{{clé}}` et le chiffre est mis à l'affichage (`fill`).

Les chiffres viennent des règles de `docs/droits/regles.md` (`regles.load`). Une donnée manque :
le chiffre qui en a besoin vaut None, l'écran affiche « À compléter ». Jamais de chiffre deviné.
"""

import re
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.db.models import Setting
from jobbot.droits.regles import AGES, MONTHS, Rules

KEY = "droits_situation"
FIELDS = ("inscription", "mois", "age", "enfants", "gain", "touchees", "vacances_prises")


@dataclass(frozen=True)
class Situation:
    inscription: date | None = None
    mois: str | None = None
    age: str | None = None
    enfants: bool | None = None
    gain: int | None = None
    touchees: int | None = None
    vacances_prises: int | None = None


@dataclass(frozen=True)
class Figures:
    total: int | None
    restants: int | None
    taux: int | None
    fin: date | None
    vacances_acquis: int | None
    vacances_disponibles: int | None
    avs: bool


def _situation(value: Any) -> Situation:
    if not isinstance(value, dict):
        return Situation()

    def number(name: str) -> int | None:
        raw = value.get(name)
        return raw if isinstance(raw, int) and not isinstance(raw, bool) and raw >= 0 else None

    inscription = None
    if isinstance(value.get("inscription"), str):
        try:
            inscription = date.fromisoformat(value["inscription"])
        except ValueError:
            inscription = None
    return Situation(
        inscription=inscription,
        mois=value.get("mois") if value.get("mois") in MONTHS else None,
        age=value.get("age") if value.get("age") in AGES else None,
        enfants=value.get("enfants") if isinstance(value.get("enfants"), bool) else None,
        gain=number("gain"),
        touchees=number("touchees"),
        vacances_prises=number("vacances_prises"),
    )


async def load(session: AsyncSession) -> Situation:
    value = await session.scalar(select(Setting.value).where(Setting.key == KEY))
    return _situation(value)


async def save(session: AsyncSession, situation: Situation) -> None:
    """Enregistre la situation entière ; vide, la clé est retirée (rien n'est gardé vide)."""
    stored: dict[str, Any] = {}
    for name in FIELDS:
        value = getattr(situation, name)
        if value is None:
            continue
        stored[name] = value.isoformat() if isinstance(value, date) else value
    if not stored:
        await session.execute(delete(Setting).where(Setting.key == KEY))
        return
    await session.execute(
        insert(Setting)
        .values(key=KEY, value=stored)
        .on_conflict_do_update(index_elements=["user_id", "key"], set_={"value": stored})
    )


def _add_months(start: date, months: int) -> date:
    year, month = divmod(start.month - 1 + months, 12)
    year += start.year
    month += 1
    day = start.day
    while True:
        try:
            return date(year, month, day)
        except ValueError:
            day -= 1


def rate(rules: Rules, situation: Situation) -> int | None:
    """80 % avec des enfants à charge, ou si l'indemnité pleine ne dépasse pas le seuil journalier ;
    sinon 70 %.
    """
    full = int(rules.params["taux_plein"])
    reduced = int(rules.params["taux_reduit"])
    if situation.enfants is True:
        return full
    if situation.enfants is None or situation.gain is None:
        return None
    daily = (
        Decimal(situation.gain)
        * Decimal(full)
        / Decimal(100)
        / Decimal(str(rules.params["jours_par_mois"]))
    )
    return full if daily <= Decimal(str(rules.params["seuil_journalier"])) else reduced


def figures(rules: Rules, situation: Situation) -> Figures:
    total = None
    if situation.age and situation.mois:
        total = rules.allowance(situation.age, situation.enfants, situation.mois)
    restants = None
    if total is not None and situation.touchees is not None:
        restants = max(0, total - situation.touchees)
    fin = None
    if situation.inscription:
        months = int(rules.params["delai_cadre_mois"])
        fin = _add_months(situation.inscription, months) - timedelta(days=1)
    acquis = None
    if situation.touchees is not None:
        tranche = int(rules.params["vacances_tranche"])
        acquis = int(rules.params["vacances_jours"]) * (situation.touchees // tranche)
    disponibles = None
    if acquis is not None and situation.vacances_prises is not None:
        disponibles = max(0, acquis - situation.vacances_prises)
    return Figures(
        total=total,
        restants=restants,
        taux=rate(rules, situation),
        fin=fin,
        vacances_acquis=acquis,
        vacances_disponibles=disponibles,
        avs=situation.age == "55_plus",
    )


MONTH_NAMES = (
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
)


def long_date(value: date) -> str:
    return (
        f"{value.day}{'er' if value.day == 1 else ''} {MONTH_NAMES[value.month - 1]} {value.year}"
    )


PLACEHOLDER = re.compile(r"\{\{\s*([a-z_]+)\s*\}\}")
# Les chiffres que l'Assistant peut citer sans les connaître : il écrit {{clé}}, le serveur les met
# à l'affichage.
PLACEHOLDERS = {
    "jours_restants": "les indemnités qui te restent",
    "jours_total": "ton nombre total d'indemnités",
    "taux": "ton taux d'indemnisation",
    "fin_estimee": "la fin estimée de ton délai-cadre",
    "vacances": "tes jours de vacances",
}
MISSING = "à compléter dans Ta situation"


def values(figs: Figures) -> dict[str, str]:
    def days(count: int | None) -> str:
        return MISSING if count is None else f"{count} jour{'s' if count > 1 else ''}"

    if figs.vacances_disponibles is not None:
        holidays = f"{days(figs.vacances_disponibles)} disponibles"
    elif figs.vacances_acquis is not None:
        holidays = f"{days(figs.vacances_acquis)} acquis"
    else:
        holidays = MISSING
    return {
        "jours_restants": days(figs.restants),
        "jours_total": days(figs.total),
        "taux": MISSING if figs.taux is None else f"{figs.taux} %",
        "fin_estimee": MISSING if figs.fin is None else long_date(figs.fin),
        "vacances": holidays,
    }


def fill(text: str, filled: dict[str, str]) -> str:
    """Remplace chaque {{clé}} connue par le chiffre du compte ; une clé inconnue est retirée."""
    return PLACEHOLDER.sub(lambda match: filled.get(match.group(1), ""), text)


class Filler:
    """Remplace les {{clé}} d'un texte qui arrive par morceaux : retient la fin tant qu'une clé
    n'est pas fermée.
    """

    def __init__(self, filled: dict[str, str]) -> None:
        self.filled = filled
        self.held = ""

    def feed(self, chunk: str) -> str:
        text = self.held + chunk
        start = text.rfind("{{")
        if start != -1 and "}}" not in text[start:] and len(text) - start < 40:
            self.held = text[start:]
            text = text[:start]
        elif text.endswith("{"):
            self.held = "{"
            text = text[:-1]
        else:
            self.held = ""
        return fill(text, self.filled)

    def flush(self) -> str:
        rest, self.held = self.held, ""
        return fill(rest, self.filled)


MARK = re.compile(r"\s*\{\{droits:([a-z]+)\}\}\s*$")


def mark(subject: str) -> str:
    """La marque au bout d'une réponse qui a lu les règles : le lien et la source y reviennent."""
    return f"\n\n{{{{droits:{subject}}}}}"


def split(content: str) -> tuple[str, str | None]:
    found = MARK.search(content)
    if found is None:
        return content, None
    return content[: found.start()], found.group(1)


def link(rules: Rules, subject: str) -> dict[str, str | None]:
    """« Voir dans Tes droits », une action au plus, la pastille source (§72r)."""
    page = rules.section("page")
    if (
        subject in rules.sections
        and subject != "page"
        and "Action" in rules.section(subject).fields
    ):
        section = rules.section(subject)
        return {
            "subject": subject,
            "to": f"/compte/droits/{subject}",
            "action": section.get("Action"),
            "source": section.get("Source affichée"),
            "verified": section.get("Vérifié"),
        }
    return {
        "subject": "general",
        "to": "/compte/droits",
        "action": None,
        "source": page.get("Source affichée"),
        "verified": page.get("Vérifié"),
    }
