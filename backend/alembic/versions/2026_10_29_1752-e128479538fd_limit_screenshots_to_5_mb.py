"""limit screenshots to 5 MB

Revision ID: e128479538fd
Revises: 8f965209201e
Create Date: 2026-10-29 17:52:58.209822

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e128479538fd'
down_revision: Union[str, Sequence[str], None] = '8f965209201e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CONSTRAINT = "ck_order_screenshots_size"


def upgrade() -> None:
    """Upgrade schema."""
    # Alembic does not detect changes to CHECK constraints, so this is written by hand.
    # Existing rows must already fit: the check fails if a screenshot is larger than 5 MB.
    op.drop_constraint(op.f(CONSTRAINT), "order_screenshots", type_="check")
    op.create_check_constraint(op.f(CONSTRAINT), "order_screenshots", "size_bytes > 0 AND size_bytes <= 5242880")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f(CONSTRAINT), "order_screenshots", type_="check")
    op.create_check_constraint(op.f(CONSTRAINT), "order_screenshots", "size_bytes > 0 AND size_bytes <= 26214400")
