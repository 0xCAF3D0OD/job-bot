"""Télétravail (docs/26) : relevé à la notation, règle « ouvert depuis la Suisse »

Revision ID: 0036
Revises: 0035
Create Date: 2026-10-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0036"
down_revision: str | None = "0035"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OLD_KINDS = (
    "'locations', 'remote_ok', 'min_rate', 'excluded_types', 'banned_words', 'unspoken_languages'"
)
NEW_KINDS = (
    "'locations', 'remote_policy', 'min_rate', 'excluded_types', 'banned_words', "
    "'unspoken_languages'"
)
BOTH_KINDS = f"{OLD_KINDS}, 'remote_policy'"


def upgrade() -> None:
    op.add_column("evaluations", sa.Column("remote", sa.Text()))
    op.add_column("evaluations", sa.Column("remote_days", sa.SmallInteger()))
    op.add_column("evaluations", sa.Column("remote_region", sa.Text()))
    op.add_column("evaluations", sa.Column("remote_from_switzerland", sa.Boolean()))
    op.drop_constraint("criteria_kind_check", "criteria", type_="check")
    op.create_check_constraint("criteria_kind_check", "criteria", f"kind IN ({BOTH_KINDS})")
    # La case « télétravail complet accepté » devient un choix : cochée, il s'agit des
    # offres ouvertes depuis la Suisse ; décochée, refusé.
    op.execute(
        """
        INSERT INTO criteria (kind, value)
        SELECT 'remote_policy',
               to_jsonb(CASE WHEN value = 'true'::jsonb THEN 'from_switzerland' ELSE 'refuse' END)
        FROM criteria WHERE kind = 'remote_ok'
        ON CONFLICT (kind) DO NOTHING
        """
    )
    op.execute("DELETE FROM criteria WHERE kind = 'remote_ok'")
    op.drop_constraint("criteria_kind_check", "criteria", type_="check")
    op.create_check_constraint("criteria_kind_check", "criteria", f"kind IN ({NEW_KINDS})")


def downgrade() -> None:
    op.drop_constraint("criteria_kind_check", "criteria", type_="check")
    op.create_check_constraint("criteria_kind_check", "criteria", f"kind IN ({BOTH_KINDS})")
    op.execute(
        """
        INSERT INTO criteria (kind, value)
        SELECT 'remote_ok', to_jsonb(value <> '"refuse"'::jsonb)
        FROM criteria WHERE kind = 'remote_policy'
        ON CONFLICT (kind) DO NOTHING
        """
    )
    op.execute("DELETE FROM criteria WHERE kind = 'remote_policy'")
    op.drop_constraint("criteria_kind_check", "criteria", type_="check")
    op.create_check_constraint("criteria_kind_check", "criteria", f"kind IN ({OLD_KINDS})")
    for column in ("remote_from_switzerland", "remote_region", "remote_days", "remote"):
        op.drop_column("evaluations", column)
