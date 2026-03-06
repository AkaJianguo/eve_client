# app/models/universe.py
from sqlalchemy import Column, Integer, String
from app.models.base import Base # 👈 必须是从 base.py 导出的那个 Base

class UniverseName(Base):
    """EVE 全宇宙 ID 翻译字典表"""
    __tablename__ = "universe_names"
    
    # EVE 的 ID 是全局唯一的，所以直接用作主键，查询速度拉满
    id = Column(Integer, primary_key=True, index=True, autoincrement=False)
    name = Column(String, nullable=False, index=True)
    category = Column(String, nullable=False) # 记录它是角色、军团、星系还是物品