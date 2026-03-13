"""add market history table

Revision ID: 7c9d3f4b2e1a
Revises: 0d3e7a1f6c2a
Create Date: 2026-03-10 14:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7c9d3f4b2e1a"
down_revision: Union[str, Sequence[str], None] = "0d3e7a1f6c2a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "market_history",
        sa.Column("type_id", sa.Integer(), nullable=False),
        sa.Column("region_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("average", sa.Numeric(20, 2), nullable=False),
        sa.Column("highest", sa.Numeric(20, 2), nullable=False),
        sa.Column("lowest", sa.Numeric(20, 2), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=False),
        sa.Column("order_count", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("type_id", "region_id", "date"),
    )
    op.create_index("ix_market_history_date", "market_history", ["date"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_market_history_date", table_name="market_history")
    op.drop_table("market_history")