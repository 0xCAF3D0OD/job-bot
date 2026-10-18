"""Le jeton de liaison de l'extension expire côté serveur (docs/76 §1)

Revision ID: 0053
Revises: 0052
Create Date: 2026-10-18

Un jeton créé par « Relier ce navigateur » doit être lu par l'extension dans les 2 minutes ;
jusqu'ici, seule la page le révoquait, et pas si elle était fermée avant. `expires_at` : posé à
la création d'un jeton de liaison, effacé à sa première utilisation. Passé ce délai, le jeton
ne sert plus, même si la page n'est plus là. Les jetons créés à la main n'en ont pas.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0053"
down_revision: str | None = "0052"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ROLE = "jobbot_app"


def _function(condition: str) -> None:
    op.execute(
        "create or replace function account_of_extension_token(hash text) returns bigint "
        "language sql stable security definer set search_path = public as $$ "
        f"select user_id from extension_tokens where token_hash = hash and {condition} $$"
    )
    op.execute("revoke all on function account_of_extension_token(text) from public")
    op.execute(f"grant execute on function account_of_extension_token(text) to {ROLE}")


def upgrade() -> None:
    op.add_column("extension_tokens", sa.Column("expires_at", sa.DateTime(timezone=True)))
    _function("revoked_at is null and (expires_at is null or expires_at > now())")


def downgrade() -> None:
    _function("revoked_at is null")
    op.drop_column("extension_tokens", "expires_at")
