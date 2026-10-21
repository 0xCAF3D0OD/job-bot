"""Les codes et les messages des sites (docs/112)

Revision ID: 0061
Revises: 0060
Create Date: 2026-10-21

Un e-mail d'un site rangé dans le journal peut être autre chose qu'une alerte :
- `searches.kind` : vide pour une alerte ; « code » (un code de vérification) ou « message »
  (bienvenue, alerte modifiée, mot de passe oublié…) ;
- `searches.code` : le code lu, effacé au bout de 30 minutes.

La table garde ses règles d'accès par compte (docs/78) : rien à changer de ce côté.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0061"
down_revision: str | None = "0060"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("searches", sa.Column("kind", sa.Text()))
    op.add_column("searches", sa.Column("code", sa.Text()))
    op.create_index("ix_searches_kind", "searches", ["kind"])


def downgrade() -> None:
    op.drop_index("ix_searches_kind", table_name="searches")
    op.drop_column("searches", "code")
    op.drop_column("searches", "kind")
