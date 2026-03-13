from datetime import date

from sqlalchemy import BigInteger, Date, Index, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class MarketHistory(Base):
    __tablename__ = "market_history"

    type_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    region_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    average: Mapped[float] = mapped_column(Numeric(20, 2), nullable=False)
    highest: Mapped[float] = mapped_column(Numeric(20, 2), nullable=False)
    lowest: Mapped[float] = mapped_column(Numeric(20, 2), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    order_count: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        Index("ix_market_history_date", "date"),
    )