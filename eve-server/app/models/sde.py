from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SdeMarketGroup(Base):
    """SDE 市场分类表的只读 ORM 映射。"""

    __tablename__ = "marketGroups"
    __table_args__ = {"schema": "sde"}

    market_group_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parent_group_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    zh_name: Mapped[str | None] = mapped_column(String, nullable=True)
    en_name: Mapped[str | None] = mapped_column(String, nullable=True)
    de_name: Mapped[str | None] = mapped_column(String, nullable=True)


class SdeType(Base):
    """SDE 物品类型表的只读 ORM 映射。"""

    __tablename__ = "types"
    __table_args__ = {"schema": "sde"}

    type_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    market_group_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    zh_name: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    en_name: Mapped[str | None] = mapped_column(String, nullable=True)
    de_name: Mapped[str | None] = mapped_column(String, nullable=True)
    volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    published: Mapped[bool | None] = mapped_column(Boolean, nullable=True, index=True)