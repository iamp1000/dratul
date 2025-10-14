"""add is_online_booking to location_schedules

Revision ID: 4
Revises: 3
Create Date: 2024-03-15 10:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4'
down_revision = '3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('location_schedules', sa.Column('is_online_booking', sa.Boolean(), server_default=sa.text('true'), nullable=False))


def downgrade():
    op.drop_column('location_schedules', 'is_online_booking')