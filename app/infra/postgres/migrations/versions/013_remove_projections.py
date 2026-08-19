"""Remove engine projections table

Revision ID: 013_remove_projections
Revises: 012_make_phase_nullable
Create Date: 2026-05-23 19:55:29.730676

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "013_remove_projections"
down_revision: Union[str, Sequence[str], None] = "012_make_phase_nullable"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_table("engine_projections")


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table(
        "engine_projections",
        sa.Column("engine_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("name", sa.VARCHAR(length=20), autoincrement=False, nullable=False),
        sa.Column("config", postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=False),
        sa.Column("enabled", sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.Column("phase", sa.VARCHAR(length=20), autoincrement=False, nullable=True),
        sa.Column("sync", sa.VARCHAR(length=20), autoincrement=False, nullable=True),
        sa.Column("last_seen_at", postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint("engine_id", name=op.f("engine_projections_pkey")),
    )
