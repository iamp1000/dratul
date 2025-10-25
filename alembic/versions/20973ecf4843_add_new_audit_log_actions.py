"""Add new audit log actions

Revision ID: 20973ecf4843
Revises: 839c539607c7
Create Date: 2025-10-25 22:13:55.919585

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20973ecf4843'
down_revision: Union[str, Sequence[str], None] = '839c539607c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
