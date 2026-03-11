"""Add engine specs

Revision ID: 002_add_engine_specs
Revises: 001_add_engines
Create Date: 2026-03-10 23:53:43.529885

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_add_engine_specs"
down_revision: Union[str, Sequence[str], None] = "001_add_engines"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "engine_specs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("config", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("generation", sa.Integer(), nullable=False),
        sa.Column("engine_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["engine_id"], ["engines.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("engine_specs")
