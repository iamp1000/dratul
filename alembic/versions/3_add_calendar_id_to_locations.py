"""add calendar_id to locations

Revision ID: 3
Revises: 4c8291eccb75
Create Date: 2024-03-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3'
down_revision = '4c8291eccb75'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('locations', sa.Column('calendar_id', sa.String(255), nullable=True))


def downgrade():
    op.drop_column('locations', 'calendar_id')