# Alembic Checklist

这份文档用于记录 `eve-server` 的数据库迁移标准流程，避免再次出现迁移链断裂、空迁移、误用全局 `alembic` 等问题。

## 适用范围

- 项目目录：`eve-server`
- Python 虚拟环境：`eve-server/.venv`
- Alembic 配置入口：`eve-server/alembic/env.py`
- 模型聚合入口：`eve-server/app/models/__init__.py`

## 每次操作前的固定检查

1. 进入后端目录。
2. 确认使用项目虚拟环境，不要使用系统全局 Python 或全局 `alembic`。
3. 确认数据库连接正常。
4. 确认新增模型已经在 `app/models/__init__.py` 中导入。

## 标准操作流程

### 1. 激活环境

```bash
cd /Users/wangjianguo/Desktop/EVE/eve_client/eve-server
source .venv/bin/activate
```

### 2. 查看当前迁移状态

```bash
/Users/wangjianguo/Desktop/EVE/eve_client/eve-server/.venv/bin/alembic current
/Users/wangjianguo/Desktop/EVE/eve_client/eve-server/.venv/bin/alembic history
```

### 3. 修改模型

例如修改这些文件：

- `eve-server/app/models/user.py`
- `eve-server/app/models/universe.py`
- `eve-server/app/models/industry.py`

如果新增了一个新的模型文件，必须同步更新：

- `eve-server/app/models/__init__.py`

示例：

```python
from .industry import IndustryJob
```

如果不导入，`Base.metadata` 可能不会注册该表，`--autogenerate` 就可能生成空迁移。

### 4. 生成迁移

```bash
/Users/wangjianguo/Desktop/EVE/eve_client/eve-server/.venv/bin/alembic revision --autogenerate -m "describe_change"
```

命名建议：

- `add_industry_jobs`
- `add_user_status`
- `create_market_tables`

### 5. 检查新迁移文件

生成后检查：

- `eve-server/alembic/versions/*.py`

重点确认：

1. 是否真的出现了 `op.create_table(...)`、`op.add_column(...)`、`op.create_index(...)`
2. 是否误删了不该删的表或字段
3. `down_revision` 是否正确
4. 没有空的 `upgrade()` / `downgrade()`

### 6. 执行迁移

```bash
/Users/wangjianguo/Desktop/EVE/eve_client/eve-server/.venv/bin/alembic upgrade head
```

### 7. 再次核对状态

```bash
/Users/wangjianguo/Desktop/EVE/eve_client/eve-server/.venv/bin/alembic current
```

## 最短安全流程

```bash
cd /Users/wangjianguo/Desktop/EVE/eve_client/eve-server
source .venv/bin/activate
/Users/wangjianguo/Desktop/EVE/eve_client/eve-server/.venv/bin/alembic revision --autogenerate -m "your_change"
/Users/wangjianguo/Desktop/EVE/eve_client/eve-server/.venv/bin/alembic upgrade head
```

## 这个项目的特殊注意点

### 1. `env.py` 依赖 `app.models`

当前 `eve-server/alembic/env.py` 使用：

```python
from app.models import Base
```

这意味着模型注册依赖 `eve-server/app/models/__init__.py` 的导入清单。

### 2. 不要用系统全局 Alembic

错误示例：

```bash
alembic upgrade head
```

如果 PATH 指到了系统 Python，可能会使用错误版本的 Alembic 和依赖。

正确示例：

```bash
/Users/wangjianguo/Desktop/EVE/eve_client/eve-server/.venv/bin/alembic upgrade head
```

### 3. 当前数据库连接来源

本地开发默认使用：

- `eve-server/.env.development`

当前开发配置是：

```text
DATABASE_URL=postgresql+asyncpg://eve_admin:EveAdmin123!@localhost:5432/eve_db
```

如果你是宿主机本地执行 Alembic，就用 `localhost`。

如果你是在 Docker 容器里执行，可能要改成容器可访问的地址，例如：

- `db`
- `host.docker.internal`

## 常用命令速查

查看当前版本：

```bash
/Users/wangjianguo/Desktop/EVE/eve_client/eve-server/.venv/bin/alembic current
```

查看历史：

```bash
/Users/wangjianguo/Desktop/EVE/eve_client/eve-server/.venv/bin/alembic history
```

生成迁移：

```bash
/Users/wangjianguo/Desktop/EVE/eve_client/eve-server/.venv/bin/alembic revision --autogenerate -m "message"
```

升级到最新：

```bash
/Users/wangjianguo/Desktop/EVE/eve_client/eve-server/.venv/bin/alembic upgrade head
```

回退一个版本：

```bash
/Users/wangjianguo/Desktop/EVE/eve_client/eve-server/.venv/bin/alembic downgrade -1
```

## 绝对不要做的事

1. 不要手动清空 `eve-server/alembic/versions`
2. 不要删除已经被数据库记录过的 revision 文件
3. 不要数据库手动改了表结构却不补迁移
4. 不要混用系统 Python 和 `.venv`
5. 不要在已经执行过的旧迁移文件上随意改结构逻辑

## 常见故障排查

### 1. 报错：`zsh: command not found: python`

原因：系统没有 `python` 命令别名。

解决：

```bash
/Users/wangjianguo/Desktop/EVE/eve_client/eve-server/.venv/bin/python your_script.py
```

### 2. 报错：`ConnectionRefusedError: ('127.0.0.1', 5432)`

原因：数据库没启动，或者端口不通。

检查：

```bash
lsof -iTCP:5432 -sTCP:LISTEN
nc -zv 127.0.0.1 5432
```

### 3. 报错：`AssertionError` 且和 revision 解析有关

常见原因：

- `alembic/versions` 被清空
- 数据库的 `alembic_version` 仍然保留旧 revision
- 当前 revision 值非法或对应文件不存在

处理思路：

1. 看 `alembic current`
2. 看 `alembic history`
3. 查数据库里的 `alembic_version`
4. 确认 `eve-server/alembic/versions` 是否完整

### 4. 生成了空迁移

原因通常是模型没有被 Alembic 扫描到。

优先检查：

1. `eve-server/alembic/env.py` 是否使用了正确的 `target_metadata`
2. `eve-server/app/models/__init__.py` 是否导入了新模型
3. 你是否真的使用了 `--autogenerate`

## 本次初始化结果

当前首个迁移文件是：

- `eve-server/alembic/versions/9bf3d1e1abb4_initial_schema.py`

当前数据库中已经验证存在：

- `users`
- `characters`
- `universe_names`
- `alembic_version`

当前 Alembic 版本号：

- `9bf3d1e1abb4`
