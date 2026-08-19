"""Add snapshot of instance registry to engine state

Revision ID: 005_add_registry_fields_to_state
Revises: 004_add_engine_instances
Create Date: 2026-03-12 00:30:36.783897

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005_add_registry_fields_to_state"
down_revision: Union[str, Sequence[str], None] = "004_add_engine_instances"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("engine_runtime_states", sa.Column("current_instance_id", sa.UUID(), nullable=True))
    op.add_column("engine_runtime_states", sa.Column("current_epoch", sa.Integer(), nullable=True))
    op.add_column("engine_runtime_states", sa.Column("last_seq_no", sa.Integer(), nullable=False))
    op.create_foreign_key(
        "fk_engine_runtime_states_current_instance_id",
        "engine_runtime_states",
        "engine_instances",
        ["current_instance_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_engine_runtime_states_current_instance_id", "engine_runtime_states", type_="foreignkey")
    op.drop_column("engine_runtime_states", "last_seq_no")
    op.drop_column("engine_runtime_states", "current_epoch")
    op.drop_column("engine_runtime_states", "current_instance_id")
