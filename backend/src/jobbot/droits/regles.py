"""Les règles de « Tes droits » (§72r), lues dans `docs/droits/regles.md`, le seul fichier
juridique.

Le fichier est écrit pour être relu par une personne : rubriques `## clé`, champs `- Champ :
valeur`, tableaux.
Ce module le lit une fois et en tire les paramètres du calcul, le tableau des indemnités et les
textes affichés.
Une rubrique ou un paramètre manquant fait échouer le chargement (et les tests) : jamais de valeur
devinée.
"""

from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

FILE = Path("docs") / "droits" / "regles.md"
TOPICS = ("vacances", "formation", "gain", "frais", "maladie", "opposition")
AGES = ("moins_25", "25_54", "55_plus")
MONTHS = ("12_17", "18_21", "22_24")


class RulesMissing(Exception):
    """Le fichier des règles est introuvable ou incomplet."""


@dataclass(frozen=True)
class Line:
    title: str
    detail: str
    source: str


@dataclass(frozen=True)
class Section:
    key: str
    fields: dict[str, str]
    tables: list[list[dict[str, str]]] = field(default_factory=list)

    def get(self, name: str) -> str:
        if name not in self.fields:
            raise RulesMissing(f"champ « {name} » absent de la rubrique « {self.key} »")
        return self.fields[name]


@dataclass(frozen=True)
class Rules:
    params: dict[str, float]
    allowances: dict[tuple[str, str, str], int]
    sections: dict[str, Section]
    sources: dict[str, tuple[str, str]]

    def section(self, key: str) -> Section:
        if key not in self.sections:
            raise RulesMissing(f"rubrique « {key} » absente")
        return self.sections[key]

    def lines(self, key: str) -> list[Line]:
        table = self.section(key).tables[0] if self.section(key).tables else []
        return [Line(row["Comment ça marche"], row["Précision"], row["Source"]) for row in table]

    def allowance(self, age: str, children: bool | None, months: str) -> int | None:
        """Le nombre maximum d'indemnités, ou None si une donnée manque pour le connaître."""
        exact = self.allowances.get((age, "*", months))
        if exact is not None:
            return exact
        if children is None:
            return None
        return self.allowances.get((age, "oui" if children else "non", months))


def _cells(row: str) -> list[str]:
    return [cell.strip() for cell in row.strip().strip("|").split("|")]


def parse(text: str) -> Rules:
    sections: dict[str, Section] = {}
    current: Section | None = None
    header: list[str] | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("## "):
            current = Section(line[3:].strip(), {})
            sections[current.key] = current
            header = None
            continue
        if current is None:
            continue
        if line.startswith("- ") and " : " in line and header is None:
            name, value = line[2:].split(" : ", 1)
            current.fields[name.strip()] = value.strip()
        elif line.startswith("|"):
            cells = _cells(line)
            if header is None:
                header = cells
                current.tables.append([])
            elif all(set(cell) <= {"-", ":"} for cell in cells):
                continue
            else:
                current.tables[-1].append(dict(zip(header, cells, strict=True)))
        else:
            header = None

    def table(key: str) -> list[dict[str, str]]:
        found = sections.get(key)
        if found is None or not found.tables:
            raise RulesMissing(f"tableau « {key} » absent")
        return found.tables[0]

    params = {row["Clé"]: float(row["Valeur"]) for row in table("paramètres")}
    allowances = {
        (row["Âge"], row["Enfants"], row["Mois cotisés"]): int(row["Indemnités"])
        for row in table("indemnités")
    }
    sources = {row["Clé"]: (row["Nom"], row["Adresse"]) for row in table("sources")}
    rules = Rules(params, allowances, sections, sources)
    for name in (
        "taux_plein",
        "taux_reduit",
        "seuil_journalier",
        "jours_par_mois",
        "delai_cadre_mois",
        "vacances_jours",
        "vacances_tranche",
        "vacances_annonce",
        "maladie_jours",
        "maladie_max",
        "opposition_jours",
    ):
        if name not in params:
            raise RulesMissing(f"paramètre « {name} » absent")
    for key in ("page", "devoirs", "assistant", *TOPICS):
        rules.section(key)
    for age in AGES:
        for months in MONTHS:
            if (
                rules.allowance(age, True, months) is None
                or rules.allowance(age, False, months) is None
            ):
                raise RulesMissing(f"indemnités absentes pour {age}, {months}")
    return rules


def _find() -> Path:
    # Dans le dépôt, le fichier est à la racine (docs/droits) ; dans l'image, copié à côté du
    # serveur (/app/docs).
    for parent in Path(__file__).resolve().parents:
        candidate = parent / FILE
        if candidate.is_file():
            return candidate
    raise RulesMissing("docs/droits/regles.md introuvable")


@cache
def load() -> Rules:
    return parse(_find().read_text("utf-8"))
