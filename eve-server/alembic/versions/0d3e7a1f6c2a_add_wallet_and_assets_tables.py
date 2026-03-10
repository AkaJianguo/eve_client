"""add wallet and assets tables

Revision ID: 0d3e7a1f6c2a
Revises: 9bf3d1e1abb4
Create Date: 2026-03-09 16:58:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0d3e7a1f6c2a"
down_revision: Union[str, Sequence[str], None] = "9bf3d1e1abb4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "character_wallet_balances",
        sa.Column("character_id", sa.BigInteger(), nullable=False),
        sa.Column("balance", sa.Numeric(20, 2), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"]),
        sa.PrimaryKeyConstraint("character_id"),
    )

    op.create_table(
        "character_wallet_journal_entries",
        sa.Column("id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("character_id", sa.BigInteger(), nullable=False),
        sa.Column("amount", sa.Numeric(20, 2), nullable=True),
        sa.Column("balance", sa.Numeric(20, 2), nullable=True),
        sa.Column("context_id", sa.BigInteger(), nullable=True),
        sa.Column("context_id_type", sa.String(length=64), nullable=True),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("first_party_id", sa.BigInteger(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("ref_type", sa.String(length=128), nullable=False),
        sa.Column("second_party_id", sa.BigInteger(), nullable=True),
        sa.Column("tax", sa.Numeric(20, 2), nullable=True),
        sa.Column("tax_receiver_id", sa.BigInteger(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_character_wallet_journal_entries_character_id"), "character_wallet_journal_entries", ["character_id"], unique=False)
    op.create_index(op.f("ix_character_wallet_journal_entries_date"), "character_wallet_journal_entries", ["date"], unique=False)
    op.create_index(op.f("ix_character_wallet_journal_entries_ref_type"), "character_wallet_journal_entries", ["ref_type"], unique=False)

    op.create_table(
        "character_wallet_transactions",
        sa.Column("transaction_id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("character_id", sa.BigInteger(), nullable=False),
        sa.Column("client_id", sa.BigInteger(), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_buy", sa.Boolean(), nullable=False),
        sa.Column("is_personal", sa.Boolean(), nullable=False),
        sa.Column("journal_ref_id", sa.BigInteger(), nullable=False),
        sa.Column("location_id", sa.BigInteger(), nullable=False),
        sa.Column("quantity", sa.BigInteger(), nullable=False),
        sa.Column("type_id", sa.BigInteger(), nullable=False),
        sa.Column("unit_price", sa.Numeric(20, 2), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"]),
        sa.PrimaryKeyConstraint("transaction_id"),
    )
    op.create_index(op.f("ix_character_wallet_transactions_character_id"), "character_wallet_transactions", ["character_id"], unique=False)
    op.create_index(op.f("ix_character_wallet_transactions_date"), "character_wallet_transactions", ["date"], unique=False)
    op.create_index(op.f("ix_character_wallet_transactions_type_id"), "character_wallet_transactions", ["type_id"], unique=False)

    op.create_table(
        "character_assets",
        sa.Column("item_id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("character_id", sa.BigInteger(), nullable=False),
        sa.Column("type_id", sa.BigInteger(), nullable=False),
        sa.Column("is_blueprint_copy", sa.Boolean(), nullable=True),
        sa.Column("is_singleton", sa.Boolean(), nullable=False),
        sa.Column("location_flag", sa.String(length=64), nullable=False),
        sa.Column("location_id", sa.BigInteger(), nullable=False),
        sa.Column("location_type", sa.String(length=32), nullable=False),
        sa.Column("quantity", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("position_x", sa.Float(), nullable=True),
        sa.Column("position_y", sa.Float(), nullable=True),
        sa.Column("position_z", sa.Float(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"]),
        sa.PrimaryKeyConstraint("item_id"),
    )
    op.create_index(op.f("ix_character_assets_character_id"), "character_assets", ["character_id"], unique=False)
    op.create_index(op.f("ix_character_assets_location_flag"), "character_assets", ["location_flag"], unique=False)
    op.create_index(op.f("ix_character_assets_location_id"), "character_assets", ["location_id"], unique=False)
    op.create_index(op.f("ix_character_assets_type_id"), "character_assets", ["type_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_character_assets_type_id"), table_name="character_assets")
    op.drop_index(op.f("ix_character_assets_location_id"), table_name="character_assets")
    op.drop_index(op.f("ix_character_assets_location_flag"), table_name="character_assets")
    op.drop_index(op.f("ix_character_assets_character_id"), table_name="character_assets")
    op.drop_table("character_assets")

    op.drop_index(op.f("ix_character_wallet_transactions_type_id"), table_name="character_wallet_transactions")
    op.drop_index(op.f("ix_character_wallet_transactions_date"), table_name="character_wallet_transactions")
    op.drop_index(op.f("ix_character_wallet_transactions_character_id"), table_name="character_wallet_transactions")
    op.drop_table("character_wallet_transactions")

    op.drop_index(op.f("ix_character_wallet_journal_entries_ref_type"), table_name="character_wallet_journal_entries")
    op.drop_index(op.f("ix_character_wallet_journal_entries_date"), table_name="character_wallet_journal_entries")
    op.drop_index(op.f("ix_character_wallet_journal_entries_character_id"), table_name="character_wallet_journal_entries")
    op.drop_table("character_wallet_journal_entries")

    op.drop_table("character_wallet_balances")