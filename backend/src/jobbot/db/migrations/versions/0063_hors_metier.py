"""Les recommandations hors métier écartées (docs/116 §3)

Revision ID: 0063
Revises: 0062
Create Date: 2026-10-21

`searches.off_topic_count` : dans un e-mail de recommandations (jobup « Suggestions
d'offres »), les offres dont le titre ne partage aucun mot avec les alertes ni le domaine du
compte ; comptées pour le journal, pas rangées.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0063"
down_revision: str | None = "0062"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "searches",
        sa.Column("off_topic_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("searches", "off_topic_count")
