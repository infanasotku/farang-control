"""Init

Revision ID: 000_init
Revises:
Create Date: 2026-03-10 23:48:21.972309

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "000_init"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
