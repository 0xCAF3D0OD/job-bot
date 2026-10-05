"""Lecture des pages d'offres jobup : lien de candidature, texte complet

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("offers", sa.Column("apply_url", sa.Text()))
    op.add_column("offers", sa.Column("apply_kind", sa.Text()))
    op.add_column("offers", sa.Column("description", sa.Text()))
    op.add_column("offers", sa.Column("employment_type", sa.Text()))
    op.add_column(
        "offers", sa.Column("enrich_status", sa.Text(), nullable=False, server_default="pending")
    )
    op.add_column(
        "offers", sa.Column("enrich_attempts", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column("offers", sa.Column("enriched_at", sa.DateTime(timezone=True)))
    op.create_check_constraint(
        "offers_apply_kind_check",
        "offers",
        "apply_kind IS NULL OR apply_kind IN ('external', 'jobup')",
    )
    op.create_check_constraint(
        "offers_enrich_status_check",
        "offers",
        "enrich_status IN ('pending', 'ok', 'expired', 'failed', 'skipped')",
    )
    # Les offres sans lien jobup n'ont pas de page lisible (Indeed bloque les robots).
    op.execute(
        "UPDATE offers SET enrich_status = 'skipped' WHERE id NOT IN "
        "(SELECT offer_id FROM offer_links WHERE source = 'jobup')"
    )


def downgrade() -> None:
    op.drop_constraint("offers_enrich_status_check", "offers")
    op.drop_constraint("offers_apply_kind_check", "offers")
    for column in (
        "enriched_at",
        "enrich_attempts",
        "enrich_status",
        "employment_type",
        "description",
        "apply_kind",
        "apply_url",
    ):
        op.drop_column("offers", column)
