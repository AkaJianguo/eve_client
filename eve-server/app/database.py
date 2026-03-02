from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from .core.config import settings

# 创建异步引擎
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# 创建异步 Session 工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# 基础模型类
class Base(DeclarativeBase):
    pass

# FastAPI 依赖注入：获取数据库连接
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session