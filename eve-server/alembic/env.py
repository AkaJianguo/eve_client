# 在 alembic/env.py 中修改
from app.models.base import Base
from app.models.user import User, Character  # 必须导入模型，Alembic 才能检测到

target_metadata = Base.metadata