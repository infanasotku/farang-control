"""Add liveness and sync states to projection

Revision ID: 011_add_new_stated
Revises: 010_rename_aggregates_table
Create Date: 2026-04-14 20:39:50.659854

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "011_add_new_stated"
down_revision: Union[str, Sequence[str], None] = "010_rename_aggregates_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("engine_projections", sa.Column("sync", sa.String(length=20), nullable=True))
    op.execute("""
UPDATE engine_projections
SET sync = CASE
    WHEN s.observed_generation = spec.generation THEN 'in_sync'
    ELSE 'outdated'
END
FROM engine_runtime_states as s,
     engine_specs as spec
WHERE engine_projections.engine_id = s.engine_id
  AND engine_projections.engine_id = spec.engine_id;
""")

    op.add_column("engine_projections", sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("""
UPDATE engine_projections
SET last_seen_at = s.last_seen_at
FROM engine_runtime_states as s
WHERE engine_projections.engine_id = s.engine_id;
""")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("engine_projections", "last_seen_at")
    op.drop_column("engine_projections", "sync")
