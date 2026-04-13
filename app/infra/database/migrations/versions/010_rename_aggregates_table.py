"""Rename engine_aggregates->engine_projections

Revision ID: 010_rename_aggregates_table
Revises: 009_add_engine_aggregates
Create Date: 2026-04-13 21:00:44.681090

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "010_rename_aggregates_table"
down_revision: Union[str, Sequence[str], None] = "009_add_engine_aggregates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "engine_projections",
        sa.Column("engine_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=20), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("phase", sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint("engine_id"),
    )
    op.drop_table("engine_aggregates")


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table(
        "engine_aggregates",
        sa.Column("engine_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("name", sa.VARCHAR(length=20), autoincrement=False, nullable=False),
        sa.Column("config", postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=False),
        sa.Column("enabled", sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.Column("phase", sa.VARCHAR(length=20), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint("engine_id", name=op.f("engine_aggregates_pkey")),
    )
    op.drop_table("engine_projections")
