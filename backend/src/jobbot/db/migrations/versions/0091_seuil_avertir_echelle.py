"""« M'avertir dès » sur l'échelle unique 50 / 75 / 85 (§65, Kevin, 17.11.2026, 16 h 46)

Revision ID: 0091
Revises: 0090
Create Date: 2026-11-17

`settings.notify_score_threshold` ne prend plus que 50, 75 ou 85, les seuils du cercle de score et
du filtre Note (`jobbot.scoring.scale`). Les valeurs 50, 75 et 85 ne bougent pas ; toute autre
valeur va au niveau le plus proche, le plus haut à égalité : 70 (l'ancien défaut) → 75, 55 → 50,
80 → 85. Le nouveau défaut est 75. Aucun message à la personne : l'écran affichait déjà le mot du
niveau le plus proche (« Proche » pour 70).

Le compte des valeurs avant et après est écrit dans le journal de la migration. Une valeur d'une
table déjà cloisonnée (`settings`) : la règle de sécurité existante s'applique. Retour arrière :
aucun (on ne sait plus quelle valeur d'avant correspondait) ; le niveau reste celui choisi.
"""

import logging
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0091"
down_revision: str | None = "0090"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

log = logging.getLogger("alembic.runtime.migration")
LEVELS = (50, 75, 85)
COUNT = sa.text(
    "SELECT value::text AS value, count(*) AS n FROM settings "
    "WHERE key = 'notify_score_threshold' GROUP BY 1 ORDER BY 1"
)


def nearest(value: int) -> int:
    # Recopié de jobbot.scoring.scale.nearest_level : une migration ne dépend pas du code.
    return min(LEVELS, key=lambda level: (abs(level - value), -level))


def upgrade() -> None:
    bind = op.get_bind()
    before = {row.value: row.n for row in bind.execute(COUNT)}
    log.info("« M'avertir dès » avant : %s", before or "aucune valeur")
    for raw in before:
        try:
            value = round(float(raw))
        except ValueError:
            continue
        target = nearest(value)
        if str(target) != raw:
            bind.execute(
                sa.text(
                    "UPDATE settings SET value = to_jsonb(CAST(:target AS integer)) "
                    "WHERE key = 'notify_score_threshold' AND value::text = :raw"
                ),
                {"target": target, "raw": raw},
            )
    after = {row.value: row.n for row in bind.execute(COUNT)}
    log.info("« M'avertir dès » après : %s", after or "aucune valeur")


def downgrade() -> None:
    pass
