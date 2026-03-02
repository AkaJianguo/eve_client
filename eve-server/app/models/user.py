from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey
from sqlalchemy.sql import func
# 统一使用我们在 app/models/base.py 里定义的 Base
from .base import Base 

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    # 订阅等级：0-试用, 1-Alpha, 2-Omega
    sub_level = Column(Integer, default=2) 
    created_at = Column(DateTime, server_default=func.now())

class Character(Base):
    __tablename__ = "characters"
    # 直接使用 EVE 官方 character_id 作为主键
    id = Column(BigInteger, primary_key=True) 
    name = Column(String)
    corporation_id = Column(BigInteger)
    
    # 关联平台用户，建立 1对多 关系
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # ESI 令牌字段，用于后续自动化查询
    access_token = Column(String)
    refresh_token = Column(String)
    token_expires = Column(DateTime)