"""Filtre « Contrat » : la catégorie du contrat de chaque offre (issue #468, Kevin, 18.11.2026)

Revision ID: 0093
Revises: 0092
Create Date: 2026-11-18

Nouvelle colonne `offers.contract` : « cdi », « cdd », « stage », « temporaire » ou « non_precise ».
Elle est tirée du seul champ du contrat donné par le site (`employment_type`), sans devinette :
un mot clair d'une seule catégorie, sinon « Non précisé ». Les offres existantes sont classées
ici, avec les mêmes listes que `jobbot.core.contract` (recopiées : une migration ne dépend pas du
code ; un test vérifie qu'elles restent identiques). Le compte par catégorie est écrit dans le
journal de la migration.

Données (docs/regles-securite-donnees.md) : une valeur dérivée d'une colonne de `offers`, même
niveau « Personnelle » (D-1), cloisonnée par la RLS de la table, exportée et effacée avec la ligne.
Retour arrière : la colonne est retirée, `employment_type` ne change pas.
"""

import logging
import re
import unicodedata
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0093"
down_revision: str | None = "0092"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

log = logging.getLogger("alembic.runtime.migration")

UNSPECIFIED = "non_precise"
CONTRACT_WORDS: dict[str, tuple[str, ...]] = {
    "cdi": (
        "cdi", "duree indeterminee", "contrat fixe", "poste fixe", "emploi fixe",
        "festanstellung", "festangestellt", "feste anstellung", "unbefristet",
        "permanent", "tempo indeterminato",
    ),
    "cdd": (
        "cdd", "duree determinee", "duree limitee", "befristet", "fixed term",
        "tempo determinato",
    ),
    "stage": (
        "stage", "stagiaire", "internship", "intern", "praktikum", "praktikant",
        "praktikantin", "tirocinio", "stagista",
    ),
    "temporaire": (
        "temporaire", "interim", "interimaire", "temporary", "temporar", "temporaer",
        "temporaneo", "temporanea",
    ),
}  # fmt: skip


def _normalize(value: str) -> str:
    # Recopié de jobbot.core.normalize.normalize_text.
    decomposed = unicodedata.normalize("NFKD", value)
    without_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^\w]+|_", " ", without_accents.casefold()).split())


def classify(employment_type: str | None) -> str:
    # Recopié de jobbot.core.contract.classify_contract.
    text = f" {_normalize(employment_type or '')} "
    found = {c for c, words in CONTRACT_WORDS.items() if any(f" {w} " in text for w in words)}
    return found.pop() if len(found) == 1 else UNSPECIFIED


def upgrade() -> None:
    op.add_column(
        "offers", sa.Column("contract", sa.Text(), nullable=False, server_default=UNSPECIFIED)
    )
    bind = op.get_bind()
    values = [
        row.employment_type
        for row in bind.execute(
            sa.text("SELECT DISTINCT employment_type FROM offers WHERE employment_type IS NOT NULL")
        )
    ]
    for value in values:
        category = classify(value)
        if category != UNSPECIFIED:
            bind.execute(
                sa.text("UPDATE offers SET contract = :category WHERE employment_type = :value"),
                {"category": category, "value": value},
            )
    counts = {
        row.contract: row.n
        for row in bind.execute(
            sa.text("SELECT contract, count(*) AS n FROM offers GROUP BY 1 ORDER BY 1")
        )
    }
    log.info("Contrat des offres : %s", counts or "aucune offre")


def downgrade() -> None:
    op.drop_column("offers", "contract")
