"""add assumption group and forecast fields

Revision ID: bc3a435227c2
Revises: 838e3a098023
Create Date: 2026-03-03 07:46:36.809894

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bc3a435227c2'
down_revision: Union[str, Sequence[str], None] = '838e3a098023'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('assumptions', sa.Column('group', sa.String(length=50), nullable=True))
    op.add_column('assumptions', sa.Column('forecast_method', sa.String(length=50), nullable=True))
    op.add_column('assumptions', sa.Column('forecast_params', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('assumptions', 'forecast_params')
    op.drop_column('assumptions', 'forecast_method')
    op.drop_column('assumptions', 'group')
