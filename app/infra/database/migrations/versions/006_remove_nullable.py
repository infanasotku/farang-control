"""Remove nullable for engine state

Revision ID: 006_remove_nullable
Revises: 005_add_registry_fields_to_state
Create Date: 2026-03-13 01:06:33.210770

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006_remove_nullable"
down_revision: Union[str, Sequence[str], None] = "005_add_registry_fields_to_state"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column("engine_runtime_states", "current_instance_id", existing_type=sa.UUID(), nullable=False)
    op.alter_column("engine_runtime_states", "current_epoch", existing_type=sa.INTEGER(), nullable=False)
    op.drop_constraint(
        op.f("fk_engine_runtime_states_current_instance_id"), "engine_runtime_states", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_engine_runtime_states_current_instance_id",
        "engine_runtime_states",
        "engine_instances",
        ["current_instance_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_engine_runtime_states_current_instance_id", "engine_runtime_states", type_="foreignkey")
    op.create_foreign_key(
        op.f("fk_engine_runtime_states_current_instance_id"),
        "engine_runtime_states",
        "engine_instances",
        ["current_instance_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.alter_column("engine_runtime_states", "current_epoch", existing_type=sa.INTEGER(), nullable=True)
    op.alter_column("engine_runtime_states", "current_instance_id", existing_type=sa.UUID(), nullable=True)
