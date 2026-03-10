from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool, QueuePool
from .core.config import settings
from app.models.base import Base

# 创建异步引擎，配置连接池参数以支持 SSH 隧道
# pool_pre_ping: 每次从连接池获取连接时都检测连接是否有效
# pool_recycle: 超过 3600 秒的连接会被回收（防止隧道失效）
# pool_size: 最多保持 5 个已建立的连接
# max_overflow: 允许最多 10 个额外的临时连接
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,        # ✅ 检测连接有效性
    pool_recycle=3600,         # ✅ 回收 1 小时以上的连接
    pool_size=5,               # ✅ 连接池大小
    max_overflow=10,           # ✅ 允许溢出连接
)

# 创建异步 Session 工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)


# FastAPI 依赖注入：获取数据库连接
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session