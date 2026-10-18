"""Un identifiant unique sans tenir compte des majuscules (docs/69 §1)

Revision ID: 0050
Revises: 0049
Create Date: 2026-10-18

« Bob » et « bob » ne peuvent plus coexister : la plateforme les traitait déjà comme le même
identifiant à l'invitation, la base le garantit désormais, même pour deux demandes simultanées.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0050"
down_revision: str | None = "0049"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("create unique index users_username_lower on users (lower(username))")


def downgrade() -> None:
    op.execute("drop index users_username_lower")
