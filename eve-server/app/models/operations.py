from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class CharacterWalletBalance(Base):
    __tablename__ = "character_wallet_balances"

    character_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("characters.id"), primary_key=True)
    balance: Mapped[float] = mapped_column(Numeric(20, 2), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    character = relationship("Character", back_populates="wallet_balance")


class CharacterWalletJournalEntry(Base):
    __tablename__ = "character_wallet_journal_entries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    character_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("characters.id"), index=True, nullable=False)
    amount: Mapped[float | None] = mapped_column(Numeric(20, 2))
    balance: Mapped[float | None] = mapped_column(Numeric(20, 2))
    context_id: Mapped[int | None] = mapped_column(BigInteger)
    context_id_type: Mapped[str | None] = mapped_column(String(64))
    date: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    first_party_id: Mapped[int | None] = mapped_column(BigInteger)
    reason: Mapped[str | None] = mapped_column(Text)
    ref_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    second_party_id: Mapped[int | None] = mapped_column(BigInteger)
    tax: Mapped[float | None] = mapped_column(Numeric(20, 2))
    tax_receiver_id: Mapped[int | None] = mapped_column(BigInteger)
    fetched_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    character = relationship("Character", back_populates="wallet_journal_entries")


class CharacterWalletTransaction(Base):
    __tablename__ = "character_wallet_transactions"

    transaction_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    character_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("characters.id"), index=True, nullable=False)
    client_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    date: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    is_buy: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_personal: Mapped[bool] = mapped_column(Boolean, nullable=False)
    journal_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    location_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    quantity: Mapped[int] = mapped_column(BigInteger, nullable=False)
    type_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    unit_price: Mapped[float] = mapped_column(Numeric(20, 2), nullable=False)
    fetched_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    character = relationship("Character", back_populates="wallet_transactions")


class CharacterAsset(Base):
    __tablename__ = "character_assets"

    item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    character_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("characters.id"), index=True, nullable=False)
    type_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    is_blueprint_copy: Mapped[bool | None] = mapped_column(Boolean)
    is_singleton: Mapped[bool] = mapped_column(Boolean, nullable=False)
    location_flag: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    location_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    location_type: Mapped[str] = mapped_column(String(32), nullable=False)
    quantity: Mapped[int] = mapped_column(BigInteger, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    position_x: Mapped[float | None] = mapped_column(Float)
    position_y: Mapped[float | None] = mapped_column(Float)
    position_z: Mapped[float | None] = mapped_column(Float)
    fetched_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    character = relationship("Character", back_populates="assets")