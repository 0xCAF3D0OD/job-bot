"""Une adresse de réception par compte, les sites suivis par compte (docs/65 §3)

Revision ID: 0048
Revises: 0047
Create Date: 2026-10-16

- `users.mail_code` : la partie après « + » de l'adresse de réception d'un compte invité
  (`boite+code@domaine`) ; l'exploitant garde l'adresse de la boîte elle-même.
- `account_sites` : un site en pause l'est pour un compte ; sans ligne, il est suivi. La pause
  actuelle (`sites.active`) devient celle de l'exploitant, puis la colonne disparaît.
- `searches.confirm_url` et `confirmed_at` : l'e-mail d'un site qui demande de confirmer
  l'alerte, avec son lien ; « fait » quand la personne l'a ouvert.
- `collected_message_ids` : les e-mails déjà rangés, dans tous les comptes, pour ne pas les
  relire ; elle ne rend que leurs Message-ID.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0048"
down_revision: str | None = "0047"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ROLE = "jobbot_app"
CURRENT = "nullif(current_setting('app.user_id', true), '')::bigint"


def upgrade() -> None:
    op.add_column("users", sa.Column("mail_code", sa.Text(), unique=True))
    op.add_column("searches", sa.Column("confirm_url", sa.Text()))
    op.add_column("searches", sa.Column("confirmed_at", sa.DateTime(timezone=True)))

    op.create_table(
        "account_sites",
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
            server_default=sa.text(CURRENT),
        ),
        sa.Column(
            "site_id",
            sa.BigInteger(),
            sa.ForeignKey("sites.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("active", sa.Boolean(), nullable=False),
    )
    op.execute(
        "insert into account_sites (user_id, site_id, active) "
        "select (select min(id) from users), id, false from sites where not active"
    )
    op.drop_column("sites", "active")
    op.execute(f"grant all on account_sites to {ROLE}")
    op.execute("alter table account_sites enable row level security")
    op.execute(
        "create policy account_isolation on account_sites "
        f"using (user_id = {CURRENT}) with check (user_id = {CURRENT})"
    )

    op.execute(
        "create function collected_message_ids(ids text[]) returns setof text "
        "language sql stable security definer set search_path = public as $$ "
        "select distinct message_id from searches where message_id = any(ids) $$"
    )
    op.execute("revoke all on function collected_message_ids(text[]) from public")
    op.execute(f"grant execute on function collected_message_ids(text[]) to {ROLE}")


def downgrade() -> None:
    op.execute("drop function collected_message_ids(text[])")
    op.add_column(
        "sites", sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true())
    )
    op.execute(
        "update sites set active = false where id in (select site_id from account_sites "
        "where not active and user_id = (select min(id) from users))"
    )
    op.drop_table("account_sites")
    op.drop_column("searches", "confirmed_at")
    op.drop_column("searches", "confirm_url")
    op.drop_column("users", "mail_code")
