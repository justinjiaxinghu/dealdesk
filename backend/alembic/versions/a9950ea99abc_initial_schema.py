"""initial schema

Revision ID: a9950ea99abc
Revises:
Create Date: 2026-02-27 16:02:46.927417

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a9950ea99abc'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- deals ---
    op.create_table(
        "deals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("address", sa.String(500), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("state", sa.String(50), nullable=False),
        sa.Column("property_type", sa.String(50), nullable=False),
        sa.Column("latitude", sa.Float, nullable=True),
        sa.Column("longitude", sa.Float, nullable=True),
        sa.Column("square_feet", sa.Float, nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # --- documents ---
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "deal_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("deals.id"),
            nullable=False,
        ),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column(
            "processing_status",
            sa.String(30),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("processing_steps", sa.JSON, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("page_count", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # --- extracted_fields ---
    op.create_table(
        "extracted_fields",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id"),
            nullable=False,
        ),
        sa.Column("field_key", sa.String(255), nullable=False),
        sa.Column("value_text", sa.Text, nullable=True),
        sa.Column("value_number", sa.Float, nullable=True),
        sa.Column("unit", sa.String(50), nullable=True),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0"),
        sa.Column("source_page", sa.Integer, nullable=True),
    )

    # --- market_tables ---
    op.create_table(
        "market_tables",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id"),
            nullable=False,
        ),
        sa.Column("table_type", sa.String(100), nullable=False),
        sa.Column("headers", sa.JSON, nullable=True),
        sa.Column("rows", sa.JSON, nullable=True),
        sa.Column("source_page", sa.Integer, nullable=True),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0"),
    )

    # --- assumption_sets ---
    op.create_table(
        "assumption_sets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "deal_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("deals.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # --- assumptions ---
    op.create_table(
        "assumptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "set_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assumption_sets.id"),
            nullable=False,
        ),
        sa.Column("key", sa.String(255), nullable=False),
        sa.Column("value_number", sa.Float, nullable=True),
        sa.Column("unit", sa.String(50), nullable=True),
        sa.Column("range_min", sa.Float, nullable=True),
        sa.Column("range_max", sa.Float, nullable=True),
        sa.Column(
            "source_type", sa.String(30), nullable=False, server_default="manual"
        ),
        sa.Column("source_ref", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # --- model_results ---
    op.create_table(
        "model_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "set_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assumption_sets.id"),
            nullable=False,
        ),
        sa.Column("noi_stabilized", sa.Float, nullable=False),
        sa.Column("exit_value", sa.Float, nullable=False),
        sa.Column("total_cost", sa.Float, nullable=False),
        sa.Column("profit", sa.Float, nullable=False),
        sa.Column("profit_margin_pct", sa.Float, nullable=False),
        sa.Column("computed_at", sa.DateTime, nullable=False),
    )

    # --- exports ---
    op.create_table(
        "exports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "deal_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("deals.id"),
            nullable=False,
        ),
        sa.Column(
            "set_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assumption_sets.id"),
            nullable=False,
        ),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column(
            "export_type", sa.String(20), nullable=False, server_default="xlsx"
        ),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("exports")
    op.drop_table("model_results")
    op.drop_table("assumptions")
    op.drop_table("assumption_sets")
    op.drop_table("market_tables")
    op.drop_table("extracted_fields")
    op.drop_table("documents")
    op.drop_table("deals")
