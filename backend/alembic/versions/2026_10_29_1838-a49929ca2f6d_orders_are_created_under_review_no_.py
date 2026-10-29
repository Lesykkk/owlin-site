"""orders are created under review, no pending

Revision ID: a49929ca2f6d
Revises: e128479538fd
Create Date: 2026-10-29 18:38:36.218782

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a49929ca2f6d'
down_revision: Union[str, Sequence[str], None] = 'e128479538fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CONSTRAINT = "ck_orders_status"


def upgrade() -> None:
    """Upgrade schema."""
    # Orders are now created under review and never pending. Alembic does not detect changes to
    # CHECK constraints or defaults, so this is written by hand. Drafts left over from the old
    # two-step flow have no screenshots and nothing refers to them, so they are removed.
    op.execute("DELETE FROM orders WHERE status = 'pending'")
    op.drop_constraint(op.f(CONSTRAINT), "orders", type_="check")
    op.create_check_constraint(op.f(CONSTRAINT), "orders", "status IN ('review', 'approved', 'rejected')")
    op.alter_column("orders", "status", server_default="review")


def downgrade() -> None:
    """Downgrade schema. Deleted drafts are not restored."""
    op.alter_column("orders", "status", server_default="pending")
    op.drop_constraint(op.f(CONSTRAINT), "orders", type_="check")
    op.create_check_constraint(
        op.f(CONSTRAINT), "orders", "status IN ('pending', 'review', 'approved', 'rejected')"
    )
