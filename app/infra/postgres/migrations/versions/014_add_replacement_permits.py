"""Add replacement permits to engine runtime state.

Revision ID: 014_add_replacement_permits
Revises: 013_remove_projections
Create Date: 2026-08-27

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "014_add_replacement_permits"
down_revision: Union[str, Sequence[str], None] = "013_remove_projections"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "engine_runtime_states",
        sa.Column("replacement_permit_digest", sa.LargeBinary(length=32), nullable=True),
    )
    op.add_column(
        "engine_runtime_states",
        sa.Column("replacement_permit_expires_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("engine_runtime_states", "replacement_permit_expires_at")
    op.drop_column("engine_runtime_states", "replacement_permit_digest")
