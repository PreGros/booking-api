"""add user_id to bookings

Revision ID: 63ca5be7cec0
Revises: d71697fb35a7
Create Date: 2026-11-01 22:44:58.055686

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '63ca5be7cec0'
down_revision: Union[str, Sequence[str], None] = 'd71697fb35a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("DELETE FROM bookings")  # no real data yet; a NOT NULL column can't be added to existing rows
    op.add_column('bookings', sa.Column('user_id', sa.Integer(), nullable=False))
    op.create_index(op.f('ix_bookings_user_id'), 'bookings', ['user_id'], unique=False)
    op.create_foreign_key(None, 'bookings', 'users', ['user_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_bookings_user_id'), table_name='bookings')
    op.drop_column('bookings', 'user_id')
