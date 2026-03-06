from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey, Float, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base
from sqlalchemy import Column, Boolean
class User(Base):
    __tablename__ = "users"

    # ================= 平台内部账户（虚拟户口本） =================
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 网站订阅/权限等级 (例如: 0-试用, 1-基础, 2-高级)
    sub_level = Column(Integer, default=2) 
    
    # 玩家第一次通过 SSO 授权进入网站的时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 最后一次活跃时间（可选，方便清理僵尸用户）
    last_login_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联：一个物理玩家 (User) 可以拥有多个 EVE 角色 (Character)
    characters = relationship("Character", back_populates="owner", cascade="all, delete-orphan")
    # 👇 追加这个字段，默认所有新注册的用户都是激活状态
    is_active = Column(Boolean, default=True, server_default='true', nullable=False)
class Character(Base):
    __tablename__ = "characters"

    # ================= 核心主键与关联 =================
    # EVE 官方的 character_id (注意：关闭自增，必须手动填入 ESI 返回的 ID)
    id = Column(BigInteger, primary_key=True, autoincrement=False)
    
    # 归属的平台玩家 ID
    owner_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)

    # ================= ESI 公开数据 (GET /characters/{character_id}/) =================
    # 以下字段建议在每次用户 SSO 登录时，调用一次该接口进行覆盖更新
    name = Column(String(255), nullable=False, index=True)         # 角色名称
    corporation_id = Column(BigInteger, nullable=False, index=True) # 军团 ID (必有)
    alliance_id = Column(BigInteger, index=True)                   # 联盟 ID (可能为空，不是所有人都有联盟)
    faction_id = Column(Integer, index=True)                       # 势力 ID (可能为空，参与势力战争的才有)
    
    security_status = Column(Float)                                # 角色安等 (例如: 5.0, -10.0)
    gender = Column(String(50))                                    # 性别 ('male', 'female')
    birthday = Column(DateTime(timezone=True))                     # 角色创建(出生)时间
    
    bloodline_id = Column(Integer)                                 # 血统 ID
    race_id = Column(Integer)                                      # 种族 ID
    ancestry_id = Column(Integer)                                  # 祖先 ID
    
    title = Column(String(255))                                    # 角色头衔 (可能为空)
    description = Column(Text)                                     # 角色简介 (可能非常长，必须用 Text)

    # ================= SSO 授权令牌核心数据 =================
    access_token = Column(Text)                                    # ESI 访问令牌 (JWT较长，使用 Text)
    refresh_token = Column(Text)                                   # ESI 刷新令牌 (用于长期获取新 access_token)
    token_expires = Column(DateTime(timezone=True))                # Token 的绝对过期时间
    scopes = Column(Text)                                          # 该角色授权了哪些权限范围 (用逗号分隔保存)

    # 关联反向映射
    owner = relationship("User", back_populates="characters")