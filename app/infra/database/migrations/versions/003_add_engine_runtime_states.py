"""Add engine runtime states

Revision ID: 003_add_engine_runtime_states
Revises: 002_add_engine_specs
Create Date: 2026-03-10 23:55:32.159232

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_add_engine_runtime_states"
down_revision: Union[str, Sequence[str], None] = "002_add_engine_specs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "engine_runtime_states",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("reported_phase", sa.String(length=20), nullable=False),
        sa.Column("observed_generation", sa.Integer(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("engine_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["engine_id"], ["engines.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("engine_runtime_states")
