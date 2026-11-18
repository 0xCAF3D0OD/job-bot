"""Le type de contrat d'une offre, pour le filtre « Contrat » (issue #468, Kevin, 18.11.2026).

Cinq catégories : CDI, CDD, Stage, Temporaire et « Non précisé ». Le classement ne lit que le
champ du contrat donné par le site (`employment_type`) et ne devine rien : un mot clair d'une seule
catégorie, en français, allemand, anglais ou italien, sinon « Non précisé ». C'est le cas aussi
quand le champ est vide, quand il ne parle que du temps de travail (« Temps plein ») ou quand il
cite deux catégories (« CDI ou CDD »).

La migration 0093 recopie ces listes (une migration ne dépend pas du code) ; un test vérifie
qu'elles restent identiques.
"""

from enum import StrEnum

from jobbot.core.normalize import normalize_text


class Contract(StrEnum):
    CDI = "cdi"
    CDD = "cdd"
    STAGE = "stage"
    TEMPORARY = "temporaire"
    UNSPECIFIED = "non_precise"


# Des mots entiers, déjà normalisés (minuscules, sans accents, ponctuation en espaces).
CONTRACT_WORDS: dict[Contract, tuple[str, ...]] = {
    Contract.CDI: (
        "cdi", "duree indeterminee", "contrat fixe", "poste fixe", "emploi fixe",
        "festanstellung", "festangestellt", "feste anstellung", "unbefristet",
        "permanent", "tempo indeterminato",
    ),
    Contract.CDD: (
        "cdd", "duree determinee", "duree limitee", "befristet", "fixed term",
        "tempo determinato",
    ),
    Contract.STAGE: (
        "stage", "stagiaire", "internship", "intern", "praktikum", "praktikant",
        "praktikantin", "tirocinio", "stagista",
    ),
    Contract.TEMPORARY: (
        "temporaire", "interim", "interimaire", "temporary", "temporar", "temporaer",
        "temporaneo", "temporanea",
    ),
}  # fmt: skip


def classify_contract(employment_type: str | None) -> Contract:
    """La catégorie du contrat, ou « Non précisé » si le site ne le dit pas clairement."""
    text = f" {normalize_text(employment_type or '')} "
    found = {
        contract
        for contract, words in CONTRACT_WORDS.items()
        if any(f" {word} " in text for word in words)
    }
    return found.pop() if len(found) == 1 else Contract.UNSPECIFIED
