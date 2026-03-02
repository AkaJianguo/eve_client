import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# 1. 导入你的配置和模型基类
from app.core.config import settings
from app.models.user import Base  # 确保路径正确，Base 包含了所有模型的元数据

# 这是 Alembic 的配置对象
config = context.config

# 2. 动态设置数据库连接地址（从你的 .env 读取）
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# 解释日志配置文件
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 3. 设置目标元数据，用于自动生成迁移脚本
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """在离线模式下运行迁移。"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """辅助函数：在连接上下文中运行迁移。"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """在在线模式下运行迁移（支持异步引擎）。"""
    
    # 这一步非常关键：使用异步引擎配置
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())