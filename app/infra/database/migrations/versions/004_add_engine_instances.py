"""Add engine instances

Revision ID: 004_add_engine_instances
Revises: 003_add_engine_runtime_states
Create Date: 2026-03-12 00:21:25.900222

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004_add_engine_instances"
down_revision: Union[str, Sequence[str], None] = "003_add_engine_runtime_states"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "engine_instances",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("engine_id", sa.UUID(), nullable=False),
        sa.Column("epoch", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["engine_id"], ["engines.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("engine_id", "epoch", name="uq_engine_instance_engine_id_epoch"),
        sa.UniqueConstraint("id", "engine_id", name="uq_engine_instance_id_engine_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("engine_instances")
