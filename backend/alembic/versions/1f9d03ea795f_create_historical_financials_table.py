"""create historical_financials table

Revision ID: 1f9d03ea795f
Revises: bc3a435227c2
Create Date: 2026-03-03 07:55:38.122201

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f9d03ea795f'
down_revision: Union[str, Sequence[str], None] = 'bc3a435227c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'historical_financials',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('deal_id', sa.CHAR(36), sa.ForeignKey('deals.id'), nullable=False),
        sa.Column('period_label', sa.String(50), nullable=False),
        sa.Column('metric_key', sa.String(100), nullable=False),
        sa.Column('value', sa.Float, nullable=False),
        sa.Column('unit', sa.String(50), nullable=True),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.UniqueConstraint('deal_id', 'period_label', 'metric_key', name='uq_hf_deal_period_metric'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('historical_financials')
