"""Make engine_projections.phase nullable. It is caused by removing non business phase: unknown

Revision ID: 012_make_phase_nullable
Revises: 011_add_new_stated
Create Date: 2026-04-14 21:18:00.860812

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "012_make_phase_nullable"
down_revision: Union[str, Sequence[str], None] = "011_add_new_stated"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column("engine_projections", "phase", existing_type=sa.VARCHAR(length=20), nullable=True)
    op.execute("UPDATE engine_projections SET phase=NULL WHERE phase = 'unknown'")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("UPDATE engine_projections SET phase='unknown' WHERE phase IS NULL")
    op.alter_column("engine_projections", "phase", existing_type=sa.VARCHAR(length=20), nullable=False)
