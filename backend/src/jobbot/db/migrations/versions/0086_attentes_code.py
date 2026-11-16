"""Les attentes de code, vues par le relevé partagé (décision de Kevin du 15.11)

Revision ID: 0086
Revises: 0085
Create Date: 2026-11-15

`code_waits_until()` : la fin la plus lointaine des attentes de code en cours, tous comptes
confondus (le réglage `code_expected` de chaque compte). Le relevé partagé de la boîte des
invités tourne tant qu'elle est dans le futur. La fonction ne rend qu'une date : ni compte,
ni adresse, ni code.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0086"
down_revision: str | None = "0085"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP = "jobbot_app"


def upgrade() -> None:
    op.execute(
        "create function code_waits_until() returns timestamptz language sql stable "
        "security definer set search_path = public, pg_temp as $$ "
        "select max((value->>'until')::timestamptz) from settings "
        "where key = 'code_expected' and jsonb_typeof(value) = 'object' $$"
    )
    op.execute("revoke all on function code_waits_until() from public")
    op.execute(f"grant execute on function code_waits_until() to {APP}")


def downgrade() -> None:
    op.execute("drop function code_waits_until()")
