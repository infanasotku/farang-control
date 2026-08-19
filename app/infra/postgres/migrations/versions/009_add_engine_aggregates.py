"""Add engine_aggregates table for read engine only

Revision ID: 009_add_engine_aggregates
Revises: 008_add_uq_to_engine_spec
Create Date: 2026-04-13 20:07:26.573204

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "009_add_engine_aggregates"
down_revision: Union[str, Sequence[str], None] = "008_add_uq_to_engine_spec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "engine_aggregates",
        sa.Column("engine_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=20), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("phase", sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint("engine_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("engine_aggregates")
