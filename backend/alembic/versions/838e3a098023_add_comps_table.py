"""add comps table

Revision ID: 838e3a098023
Revises: a9950ea99abc
Create Date: 2026-03-01 14:28:09.085647

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '838e3a098023'
down_revision: Union[str, Sequence[str], None] = 'a9950ea99abc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'comps',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('deal_id', sa.CHAR(36), sa.ForeignKey('deals.id'), nullable=False),
        sa.Column('address', sa.String(500), nullable=False),
        sa.Column('city', sa.String(100), nullable=False),
        sa.Column('state', sa.String(50), nullable=False),
        sa.Column('property_type', sa.String(50), nullable=False),
        sa.Column('source', sa.String(30), nullable=False),
        sa.Column('source_url', sa.Text, nullable=True),
        sa.Column('year_built', sa.Integer, nullable=True),
        sa.Column('unit_count', sa.Integer, nullable=True),
        sa.Column('square_feet', sa.Float, nullable=True),
        sa.Column('sale_price', sa.Float, nullable=True),
        sa.Column('price_per_unit', sa.Float, nullable=True),
        sa.Column('price_per_sqft', sa.Float, nullable=True),
        sa.Column('cap_rate', sa.Float, nullable=True),
        sa.Column('rent_per_unit', sa.Float, nullable=True),
        sa.Column('occupancy_rate', sa.Float, nullable=True),
        sa.Column('noi', sa.Float, nullable=True),
        sa.Column('expense_ratio', sa.Float, nullable=True),
        sa.Column('opex_per_unit', sa.Float, nullable=True),
        sa.Column('fetched_at', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.UniqueConstraint('deal_id', 'address', name='uq_comps_deal_address'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('comps')
