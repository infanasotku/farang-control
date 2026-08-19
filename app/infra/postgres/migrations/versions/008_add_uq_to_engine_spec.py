"""Add unique constraint to engine spec for engine_id

Revision ID: 008_add_uq_to_engine_spec
Revises: 007_add_uq_constraint_to_state
Create Date: 2026-03-14 00:47:12.124463

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "008_add_uq_to_engine_spec"
down_revision: Union[str, Sequence[str], None] = "007_add_uq_constraint_to_state"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("engine_instances", sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_unique_constraint("uq_engine_spec_engine_id", "engine_specs", ["engine_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_engine_spec_engine_id", "engine_specs", type_="unique")
    op.drop_column("engine_instances", "created_at")
