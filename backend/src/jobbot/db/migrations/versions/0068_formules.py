"""Les formules (docs/125)

Revision ID: 0068
Revises: 0067
Create Date: 2026-10-22

`users.plan` : la formule du compte, « essentiel » (gratuite, par défaut) ou « plus ». Les
limites de chaque formule sont dans le code (`jobbot.plans`), comptées sur `llm_calls`.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0068"
down_revision: str | None = "0067"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("plan", sa.Text(), nullable=False, server_default="essentiel"))


def downgrade() -> None:
    op.drop_column("users", "plan")
