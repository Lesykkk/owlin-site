"""ets2 and ets2mp access are on by default

Revision ID: 00076b9eaf2a
Revises: a49929ca2f6d
Create Date: 2026-10-30 02:22:11.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '00076b9eaf2a'
down_revision: Union[str, Sequence[str], None] = 'a49929ca2f6d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ETS2 and ETS2 Multiplayer are free for everybody and are not sold. Every user already got them
    # by hand; this makes new users get them too (the signup trigger inserts only user_id).
    op.alter_column("user_subscriptions", "ets2_access", server_default=sa.true())
    op.alter_column("user_subscriptions", "ets2mp_access", server_default=sa.true())


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("user_subscriptions", "ets2_access", server_default=sa.false())
    op.alter_column("user_subscriptions", "ets2mp_access", server_default=sa.false())
