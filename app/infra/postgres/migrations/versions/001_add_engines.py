"""Add engines

Revision ID: 001_add_engines
Revises: 000_init
Create Date: 2026-03-10 23:53:23.853457

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_add_engines"
down_revision: Union[str, Sequence[str], None] = "000_init"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "engines",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("engines")
