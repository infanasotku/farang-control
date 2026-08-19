"""Add unique constraint to engine state for engine_id

Revision ID: 007_add_unique_constraint_to_state
Revises: 006_remove_nullable
Create Date: 2026-03-14 00:35:38.055959

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "007_add_uq_constraint_to_state"
down_revision: Union[str, Sequence[str], None] = "006_remove_nullable"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(op.f("uq_engine_instance_id_engine_id"), "engine_instances", type_="unique")
    op.create_unique_constraint("uq_engine_id", "engine_runtime_states", ["engine_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_engine_id", "engine_runtime_states", type_="unique")
    op.create_unique_constraint(
        op.f("uq_engine_instance_id_engine_id"),
        "engine_instances",
        ["id", "engine_id"],
        postgresql_nulls_not_distinct=False,
    )
