# EVE Server

## 项目结构图

```text
eve-server/
├── .env.development                 # 开发环境变量
├── .env.production                  # 生产环境变量
├── .gitignore                       # Git 忽略规则
├── ALEMBIC_CHECKLIST.md             # Alembic 迁移操作清单
├── alembic.ini                      # Alembic 主配置文件
├── debug_models.py                  # Base.metadata 模型注册诊断脚本
├── readme.md                        # 后端项目说明文档
├── requirements.txt                 # Python 依赖清单
├── alembic/                         # 数据库迁移目录
│   ├── env.py                       # Alembic 运行入口，负责加载模型元数据
│   ├── README                       # Alembic 默认说明文件
│   ├── script.py.mako               # 迁移文件模板
│   └── versions/                    # 历史迁移版本
│       ├── 9bf3d1e1abb4_initial_schema.py
│       └── 0d3e7a1f6c2a_add_wallet_and_assets_tables.py
└── app/                             # FastAPI 应用主体
    ├── main.py                      # FastAPI 程序入口与路由挂载
    ├── database.py                  # 异步数据库引擎与 Session 工厂
    ├── api/                         # API 路由层
    │   ├── __init__.py              # 导出统一 api_router
    │   ├── router.py                # 聚合所有 API 版本的总入口
    │   ├── deps.py                  # 认证依赖，如当前用户解析
    │   ├── v1/
    │   │   ├── __init__.py          # 导出 v1 api_router
    │   │   ├── router.py            # v1 路由聚合入口
    │   │   ├── endpoints/           # 按业务拆分的接口文件
    │   │   │   ├── __init__.py
    │   │   │   ├── assets.py        # 角色资产相关接口
    │   │   │   ├── auth.py          # EVE SSO 登录与回调
    │   │   │   ├── industry.py      # 工业任务相关接口
    │   │   │   ├── market.py        # 市场历史查询与缓存接口
    │   │   │   ├── sde.py           # SDE 市场分类树与物品检索接口
    │   │   │   ├── universe.py      # Universe 名称解析接口
    │   │   │   ├── users.py         # 当前用户信息接口
    │   │   │   └── wallet.py        # 角色钱包相关接口
    │   │   └── schemas/             # v1 接口的请求/响应模型
    │   │       ├── __init__.py
    │   │       ├── assets.py
    │   │       ├── auth.py
    │   │       ├── industry.py
    │   │       ├── market.py
    │   │       ├── sde.py
    │   │       ├── universe.py
    │   │       ├── users.py
    │   │       └── wallet.py
    │   └── v2/                      # 预留给未来版本升级的占位目录
    │       ├── __init__.py
    │       ├── router.py
    │       ├── endpoints/
    │       │   └── __init__.py
    │       └── schemas/
    │           └── __init__.py
    ├── core/                        # 核心配置与安全能力
    │   ├── config.py                # Pydantic Settings 配置入口
    │   └── security.py              # JWT 签发逻辑
    ├── crud/                        # 数据访问层
    │   ├── __init__.py
    │   ├── character_ops.py         # 资产与钱包同步写库逻辑
    │   └── user.py                  # 用户与角色写库逻辑
    ├── models/                      # SQLAlchemy ORM 模型层
    │   ├── __init__.py              # 聚合所有模型，供 Alembic 扫描
    │   ├── base.py                  # Declarative Base
    │   ├── operations.py            # 角色资产、钱包余额、钱包日记、钱包交易模型
    │   ├── universe.py              # UniverseName 模型
    │   ├── market.py                # 市场历史模型
    │   ├── sde.py                   # SDE 静态数据只读映射
    │   └── user.py                  # User / Character 模型
    ├── schemas/                     # 预留给跨版本复用的共享 Schema
    ├── services/                    # 外部服务封装层
    │   ├── __init__.py
    │   ├── eve_esi.py               # EVE ESI 查询逻辑
    │   └── eve_sso.py               # EVE SSO 鉴权逻辑
    └── utils/                       # 工具函数目录
```

## 模块关系图

```mermaid
flowchart TD
    Client[Client / Frontend] --> Main[app/main.py]

    Main --> ApiRouter[app/api/router.py]
    Main --> Database[app/database.py]

    ApiRouter --> V1Router[app/api/v1/router.py]
    ApiRouter --> V2Router[app/api/v2/router.py]

    V1Router --> Assets[app/api/v1/endpoints/assets.py]
    V1Router --> Auth[app/api/v1/endpoints/auth.py]
    V1Router --> Users[app/api/v1/endpoints/users.py]
    V1Router --> Industry[app/api/v1/endpoints/industry.py]
    V1Router --> Market[app/api/v1/endpoints/market.py]
    V1Router --> SDE[app/api/v1/endpoints/sde.py]
    V1Router --> Universe[app/api/v1/endpoints/universe.py]
    V1Router --> Wallet[app/api/v1/endpoints/wallet.py]

    Auth --> SSO[app/services/eve_sso.py]
    Auth --> ESI[app/services/eve_esi.py]
    Auth --> UserCrud[app/crud/user.py]
    Assets --> OpsCrud[app/crud/character_ops.py]
    Wallet --> OpsCrud
    Market --> ESI
    Market --> OpsModel

    Users --> Deps[app/api/deps.py]
    Deps --> UserModel[app/models/user.py]

    Industry --> Deps
    Industry --> ESI
    Universe --> ESI
    ESI --> UniverseModel[app/models/universe.py]
    OpsCrud --> OpsModel[app/models/operations.py]

    Database --> Postgres[(PostgreSQL)]

    Alembic[alembic/env.py] --> ModelsInit[app/models/__init__.py]
    ModelsInit --> Metadata[Base.metadata]
```

## 目录分析

- `alembic/`: 数据库迁移系统，当前已有初始迁移、资产与钱包持久化迁移，以及市场历史表迁移。
- `app/api/`: 版本化 API 入口层，当前通过 `app/api/router.py` 统一聚合 v1 与预留的 v2 路由。
- `app/api/v1/endpoints/`: 按功能拆分的接口目录，后续新增模块直接在这里落文件。
- `app/api/v1/schemas/`: v1 接口请求/响应模型，Swagger、请求校验和返回结构约束以这里为准。
- `app/api/v2/`: 未来版本占位目录，当前为空实现，但已经接入总路由，后续升级不需要再改动现有 v1 结构。
- `app/core/`: 全局配置与安全逻辑，目前包含环境变量读取和 JWT 签发。
- `app/crud/`: 面向数据库的持久化逻辑，当前主要是 SSO 登录后的用户和角色写入。
- `app/models/`: ORM 模型定义，Alembic 是否能正确生成迁移依赖这里的模型被 `__init__.py` 导入。
- `app/models/sde.py`: 仅用于读取 `sde.marketGroups` / `sde.market_groups`、`sde.types` 这类静态数据表，不参与 Alembic 建表。
- `app/services/`: 对外部系统的封装，当前主要是 EVE SSO 与 ESI，并且通过共享 `aiohttp.ClientSession` 复用外部 HTTP 连接。
- `app/database.py`: 提供异步 SQLAlchemy 引擎与 `get_db()` 依赖。
- `app/schemas/`: 目前保留为空目录，建议未来只放跨版本复用或不直接绑定某个 API 版本的共享 Schema。
- `ALEMBIC_CHECKLIST.md`: 迁移操作手册，后续改表结构时优先参考。

## 服务层说明

## 本地开发启动方式

当前后端支持两种本地开发方式。

### 1. 本机直接运行

适用于你先在宿主机建立 SSH 隧道，再直接运行 Python 服务：

```bash
cd eve-server
source .venv/bin/activate

ssh -p 22222 -N -L 5432:127.0.0.1:5432 ubuntu@43.163.228.205 -i ~/.ssh/NEW_Key.pem
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

这种模式下使用 `.env.development`，数据库地址保持 `localhost:5432`。

### 2. Docker 开发模式

如果后端运行在 Docker 容器内，容器不能再用 `localhost` 访问宿主机 SSH 隧道，而是要通过 `host.docker.internal`。

当前仓库已经提供：

- `.env.docker`：Docker 开发专用环境文件
- `.env.docker.example`：示例模板

启动步骤：

```bash
ssh -p 22222 -N -L 5432:127.0.0.1:5432 ubuntu@43.163.228.205 -i ~/.ssh/NEW_Key.pem
EVE_SERVER_ENV_FILE=./eve-server/.env.docker docker compose up --build
```


`.env.docker` 中的数据库连接串使用的是 `host.docker.internal:5432`，这正是为了访问宿主机上建立的 SSH 隧道。

建议先单独开一个终端保持 SSH 隧道常驻，再在另一个终端执行 Docker 命令；如果 SSH 会话中断，容器内的后端会立即失去数据库连接。

## 当前前后端联通状态

当前后端已经和前端页面完成一轮真实联调，主要包括：

- `GET /api/v1/auth/login`：跳转到 EVE 官方 SSO
- `GET /api/v1/auth/callback`：浏览器场景下完成 JWT 签发后，重定向回前端 `/login/callback`
- `GET /api/v1/users/me`：前端回调落地后读取当前用户状态
- `GET /api/v1/industry/jobs/me`：前端 `Industry` 页面已接入真实数据
- `GET /api/v1/wallet/balance` / `journal` / `transactions`：前端 `Wallet` 页面已接入
- `GET /api/v1/assets/me`：前端 `Assets` 页面已接入真实数据
- `GET /api/v1/market/history/{type_id}`：前端 `Market` 页面已接入市场历史数据
- `GET /api/v1/sde/market-groups/tree`：前端 `MarketBrowser` 页面左侧分类树数据
- `GET /api/v1/sde/types`：前端 `MarketBrowser` 页面按分类读取物品列表
- `GET /api/v1/sde/types/search`：前端 `MarketBrowser` 页面按名称检索物品
- `GET /api/v1/market/orders/{type_id}`：前端 `MarketBrowser` 页面右侧实时盘口数据

当前钱包接口还额外具备以下行为：

- 优先从数据库读取余额、财务日记和市场交易缓存
- 缓存过期时先返回旧值，再后台异步刷新，避免前端长时间等待 ESI
- 冷启动无缓存时才同步请求一次 ESI 并回写数据库
- 接口响应附带 `cache_status`，供前端展示缓存命中状态
- 服务生命周期内会定期预热最近活跃角色的钱包缓存

当前数据库也已经具备以下持久化表：

- `character_wallet_balances`
- `character_wallet_journal_entries`
- `character_wallet_transactions`
- `character_assets`
- `market_history`

市场浏览器额外依赖以下 SDE 静态表存在于当前数据库：

- `sde.marketGroups` 或 `sde.market_groups`
- `sde.types`

如果这些表不存在，新的 `/api/v1/sde/*` 接口会返回明确的 `503`，提示当前数据库未导入 SDE，而不是返回模糊的 `500`。

当前市场浏览器右侧实时盘口不依赖 SDE，而是透传 ESI 市场订单接口：

- `/api/v1/market/orders/{type_id}` 会请求 `markets/{region_id}/orders/`
- 后端会复用 `resolve_ids(...)` 统一解析订单中的 `location_id`、`system_id`
- 统一名称解析链路为 `L1 内存缓存 -> sde.vw_universal_names -> UniverseName -> ESI`
- `UniverseName` 只在 ESI 回源成功后写入，用来缓存 SDE 里没有的动态名称
- 对全局市场物品，后端会自动将请求星域重定向到全局市场星域
- 当前全局市场白名单已包含 `44992`（PLEX）

这意味着当前后端不再只是 Swagger 可调试状态，而是已经承担真实的浏览器登录回调和前端业务页面数据来源。

如果需要按步骤检查浏览器登录、JWT 落地、用户读取和 Industry 页面数据流，见仓库根目录文档：`API_INTEGRATION_CHECKLIST.md`。

## 当前接口优先级建议

如果继续配合前端推进，后端下一阶段最值得优先补的接口通常是：

1. Dashboard 汇总接口
2. Industry 列表的分页、排序、筛选参数
3. Market 更完整的情报接口，例如区域切换、价格摘要或订单数据
4. Wallet / Assets 的时间范围过滤、位置树还原和价值估算

建议优先做“汇总接口 + 列表分页”这一类前端收益最高的接口，而不是先扩太多零散 endpoint。

## 前端对接重点

当前前端已经依赖这些后端行为：

- 401 时返回统一错误结构
- 浏览器访问 `/api/v1/auth/callback` 时执行前端重定向
- `/api/v1/users/me` 返回稳定字段
- `/api/v1/industry/jobs/me` 返回前端可直接消费的名称扩展字段
- `/api/v1/wallet/*` 返回适合前端表格直接消费的 entries / transactions 结构
- `/api/v1/assets/me` 返回适合前端表格直接消费的 assets 结构和名称扩展字段
- `/api/v1/market/history/{type_id}` 返回按日期升序的市场历史数组，供 ECharts 直接消费

当前 `Wallet` 和 `Assets` 接口还额外承担两件事：

- 在请求 ESI 后把结果同步写入本地数据库
- 对前端暴露服务端分页与汇总字段，避免浏览器一次吞掉过大结果集

`Wallet` 在此基础上又新增了一层缓存编排逻辑：

- `balance`、`journal`、`transactions` 三个接口都会先查本地库
- 命中新鲜缓存时直接返回
- 命中过期缓存时返回旧数据，并通过后台任务刷新该角色的对应缓存
- 如果本地完全没有缓存，才会走一次同步 ESI 请求

这让前端大多数场景下不再直接受 ESI 响应时延影响。

后续新增接口时，尽量延续这个风格，避免前端为单个接口写特殊适配逻辑。

## Market 历史接口策略

当前市场历史接口采用“本地缓存优先，过期按需回源”的模式：

- 路由文件位于 `app/api/v1/endpoints/market.py`
- 模型位于 `app/models/market.py`
- 返回 schema 位于 `app/api/v1/schemas/market.py`
- ESI 拉取逻辑封装在 `app/services/eve_esi.py` 的 `get_market_history(...)`

处理流程如下：

- 前端传入 `type_id`，默认区域为吉他 `10000002`
- 后端先查询 `market_history` 中该物品该区域的最新日期
- 如果本地无数据，或最新日期早于配置允许的缓存窗口，则回源 ESI
- ESI 返回后使用 PostgreSQL `ON CONFLICT DO NOTHING` 批量入库
- 最终按日期升序返回本地数据库中的完整历史数组

这让首次查询会稍慢一些，但后续同一物品的请求可以直接命中本地缓存。

## Market Browser 接口策略

市场浏览器当前由 [eve-server/app/api/v1/endpoints/sde.py](eve-server/app/api/v1/endpoints/sde.py) 和 [eve-server/app/api/v1/endpoints/market.py](eve-server/app/api/v1/endpoints/market.py) 共同支撑，用于支持前端左侧分类树、右侧星域切换和实时盘口的经典市场浏览体验。

当前相关接口包括：

- `GET /api/v1/sde/market-groups/tree`
- `GET /api/v1/sde/types?group_id=...`
- `GET /api/v1/sde/types/search?name=...`
- `GET /api/v1/market/orders/{type_id}?region_id=...`

实现约定如下：

- 市场分类树直接读取 `sde.vw_unified_market_tree` 统一视图，再由后端装配为前端树节点结构
- 物品名称优先取中文名，再回退到通用名/英文名
- 搜索接口默认只返回前 50 条结果，避免前端一次吞下过大数据集
- 实时盘口接口直接透传 ESI 市场订单，并复用统一名称解析服务补齐 `location_name`、`system_name`
- 对全局市场物品，后端会自动将请求星域切换到全局市场星域
- 当前库若未导入 SDE，会返回明确的 `503` 错误，方便联调期快速定位数据缺口

## SDE 导入说明

市场浏览器功能依赖数据库中的 SDE 静态表，而这些表不属于当前 Alembic 迁移管理范围。

当前代码默认会读取：

- `sde.vw_unified_market_tree`
- `sde.types`

这意味着即使你已经完成了 `alembic upgrade head`，如果数据库里还没有导入 SDE，下面这些接口仍然不会有真实数据：

- `GET /api/v1/sde/market-groups/tree`
- `GET /api/v1/sde/types`
- `GET /api/v1/sde/types/search`

### 最低要求

要让市场浏览器正常工作，至少需要满足下面几点：

1. 当前数据库存在 `sde` schema。
2. `sde.vw_unified_market_tree` 已创建，并至少包含 `key`、`parent_key`、`name`、`iconname`、`is_group`、`type_id` 这些字段中的核心树结构字段。
3. `sde.types` 已导入。
4. `sde.types` 至少包含这些字段中的一部分：
    `type_id`、`market_group_id`、`published`、`volume`、`zh_name`、`name`、`en_name`。

### 推荐导入顺序

如果你准备把 SDE 导入当前线上数据库或宿主机 SSH 隧道指向的目标库，推荐顺序如下：

1. 先确认 SSH 隧道已经建立，或者当前 `DATABASE_URL` 已经指向正确的线上数据库：

```bash
ssh -p 22222 -N -L 5432:127.0.0.1:5432 ubuntu@43.163.228.205 -i ~/.ssh/NEW_Key.pem
```

1. 确认目标库可连接：

```bash
docker compose exec -T eve-server sh -lc 'echo "$DATABASE_URL"'
```

1. 创建 `sde` schema（如果还没有）：

```bash
docker compose exec -T eve-server sh -lc 'python - <<"PY"
import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as session:
        await session.execute(text("CREATE SCHEMA IF NOT EXISTS sde;"))
        await session.commit()

asyncio.run(main())
PY'
```

1. 将你现有的 SDE SQL、CSV 或导出脚本导入到统一市场树视图所依赖的基础对象中，并确保最终可查询到 `sde.vw_unified_market_tree` 与 `sde.types`。

### 导入后验证

导入完成后，建议至少执行下面几个检查：

```bash
docker compose exec -T eve-server sh -lc 'python - <<"PY"
import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as session:
        print(await session.scalar(text("SELECT COUNT(*) FROM sde.vw_unified_market_tree")))
        print(await session.scalar(text("SELECT COUNT(*) FROM sde.types WHERE COALESCE(published, 0) <> 0")))

asyncio.run(main())
PY'
curl http://127.0.0.1:8000/api/v1/sde/market-groups/tree
curl "http://127.0.0.1:8000/api/v1/sde/types/search?name=三钛"
```

### 当前接口的失败表现

如果库里没有导入 SDE，后端现在会主动返回明确错误：

- `503 sde_table_missing`：缺少 `sde.vw_unified_market_tree` 或 `sde.types`
- `503 sde_query_failed`：表存在，但查询执行失败
- `503 sde_table_shape_invalid`：表结构和当前接口读取约定不匹配

这类报错优先说明“静态数据没准备好”或“字段名不一致”，而不是业务接口本身有问题。

## 调试建议

如果前端页面异常但 Swagger 正常，优先按下面顺序排查：

1. 浏览器 Network 中请求是否走到 `/api/v1/...`
2. Docker 或本机代理是否把 `/api` 正确转发到后端
3. 后端是否返回 401 并触发前端登录跳转
4. 接口响应字段是否和前端当前读取字段一致

当前后端有两条外部 HTTP 服务链路：

- `app/services/eve_esi.py`: 负责角色公开档案查询、Universe 名称解析，以及 `L1 内存缓存 + sde.vw_universal_names + UniverseName + ESI` 的分层回退逻辑。
- `app/services/eve_sso.py`: 负责 SSO Token 换取和 Token 验证。

两者采用统一模式：共享 `aiohttp.ClientSession`、在 `app/main.py` 的 `lifespan` 中执行 `start()` / `close()`，并在生命周期未命中时通过 `get_session()` 兜底创建 session 并记录 warning。这样可以复用外部 HTTP 连接，并避免服务退出时留下未关闭连接池告警。

当前 `User-Agent` 也采用统一命名规范，但按功能区分：

- `WangJianGuo-EVE-ESI/1.0`
- `WangJianGuo-EVE-SSO/1.0`

这样在日志、抓包和平台侧排查时，可以快速区分是 SSO 请求还是 ESI 数据请求。

## Token 刷新策略

EVE 的 `access_token` 有较短有效期，因此不要假设数据库里保存的 token 永远可用。

当前后端已经在业务层提供：

- `app/crud/user.py` 中的 `ensure_character_access_token(...)`
- `app/crud/user.py` 中的 `get_character_with_valid_token(...)`

推荐约定是：

1. 任何未来需要使用角色 `access_token` 访问受保护 ESI 接口的业务逻辑，都先通过这两个 helper 获取角色对象
2. 如果 token 已过期或即将过期，会自动调用 `sso_service.refresh_access_token(...)`
3. 刷新成功后，新的 `access_token`、`refresh_token`、`token_expires` 会自动写回数据库

当前还会一并更新 `characters.scopes`，这样可以记录角色最近一次授权所拥有的 ESI scope，便于排查为什么某些角色能看工业但不能看资产或钱包。

## 当前 SSO Scope

当前登录会申请以下 ESI scope：

- `esi-industry.read_character_jobs.v1`
- `esi-wallet.read_character_wallet.v1`
- `esi-assets.read_assets.v1`

如果数据库里已有旧角色和旧 refresh token，但它们是在本次 scope 扩充前授权的，用户必须重新完成一次 EVE SSO 登录，否则 ESI 上游仍可能拒绝 wallet 或 assets 请求。

这可以避免在每个业务接口里重复手写 token 过期判断逻辑。

## Schema 约定

当前接口层采用两条明确约定：

- Request Schema 负责在入口处校验不合法数据，避免把无效参数带进 Service 或数据库层。
- Response Schema 负责把 ESI 的原始字段翻译为更稳定、更适合前端消费的结构。

目前已经落地的点包括：

- `app/api/v1/schemas/universe.py` 中的 `UniverseNamesRequest`：限制 `ids` 必须是 1 到 1000 个正整数。
- `POST /api/v1/universe/names`：优先命中 L1 内存缓存，再查 `sde.vw_universal_names` 与 `UniverseName`，最后才回退到 ESI。
- `app/api/v1/schemas/industry.py` 中的 `IndustryJobStatus`：把工业任务状态定义为枚举，并补充 `status_label`。
- `app/api/v1/schemas/industry.py` 中的时间字段：例如 `start_date`、`end_date`、`pause_date`、`completed_date` 会在 schema 校验阶段转换为标准时间对象。
- `app/api/v1/endpoints/industry.py` 中的名称扩展字段：`blueprint_name`、`product_name`、`facility_name` 等会在返回前补齐。
- `app/api/v1/schemas/wallet.py`：定义钱包余额、日记、交易记录以及分页/统计字段。
- `app/api/v1/schemas/assets.py`：定义资产列表、资产汇总、位置坐标与资产自定义名字段。

## Universe 名称解析策略

当前通用名称解析入口为 `POST /api/v1/universe/names`，以及各业务接口内部复用的 `esi_service.resolve_ids(...)`。

处理顺序如下：

- 先查进程内 L1 TTL 缓存，减少同一批热点 ID 的重复数据库访问
- 再查 `sde.vw_universal_names`，优先命中静态 SDE 名称
- 若 SDE 未命中，再查本地 `universe_names` 表中的动态缓存名称
- 最后才调用 ESI `/universe/names/` 批量回源

其中 `universe_names` 表不会在命中 SDE 时反向写入，只会在 ESI 回源成功后新增或更新记录。这样可以让这张表始终只承载 SDE 未覆盖的动态名称，例如角色、军团、联盟、结构等实体。

## 资产与钱包入库策略

当前项目对资产和钱包采用“请求 ESI + 同步落库 + 返回前端”的模式：

- 钱包余额：入 `character_wallet_balances`
- 钱包日记：按 `id` 入 `character_wallet_journal_entries`
- 钱包交易：按 `transaction_id` 入 `character_wallet_transactions`
- 角色资产：按 `item_id` 入 `character_assets`

其中钱包链路现在升级为“缓存优先 + 回源刷新”的模式：

- 钱包余额缓存表：`character_wallet_balances`
- 钱包日记缓存表：`character_wallet_journal_entries`
- 钱包交易缓存表：`character_wallet_transactions`

具体返回策略如下：

- 缓存新鲜：直接返回数据库数据，`cache_status=hit_fresh`
- 缓存过期：返回数据库旧数据，并异步刷新，`cache_status=stale_refreshing`
- 缓存缺失：同步拉取 ESI 后写库再返回，`cache_status=miss_refreshed`

这样既保留了本地持久化能力，也把接口响应时间控制在更稳定的范围内。

## Wallet 缓存配置

钱包缓存和预热的主要配置位于 `app/core/config.py`：

- `WALLET_BALANCE_CACHE_TTL_SECONDS`：余额缓存 TTL，默认 60 秒
- `WALLET_JOURNAL_CACHE_TTL_SECONDS`：财务日记缓存 TTL，默认 300 秒
- `WALLET_TRANSACTIONS_CACHE_TTL_SECONDS`：市场交易缓存 TTL，默认 300 秒
- `WALLET_CACHE_WARMUP_ENABLED`：是否启用钱包缓存预热，默认开启
- `WALLET_CACHE_WARMUP_INTERVAL_SECONDS`：预热任务执行间隔，默认 300 秒
- `WALLET_CACHE_WARMUP_BATCH_SIZE`：每轮预热的角色数量，默认 20

预热逻辑挂在 `app/main.py` 的 `lifespan` 中，服务启动后会循环刷新最近活跃、且仍可自动续期 token 的角色钱包缓存。

其中资产除了基础 `/assets/` 列表，还会额外调用：

- `/assets/locations/` 获取坐标
- `/assets/names/` 获取可自定义名称的飞船、货柜等名称

所以 `character_assets` 里除了基础 ESI 字段，还额外持久化了：

- `name`
- `position_x`
- `position_y`
- `position_z`

这也是当前前端可以直接展示深层位置名称和资产自定义名的原因。

## 错误响应约定

当前项目已经统一了 HTTP 异常和参数校验异常的返回结构。

标准错误响应格式：

```json
{
    "error_code": "token_invalid",
    "message": "访问令牌无效，请重新登录"
}
```

参数校验错误格式：

```json
{
    "error_code": "validation_error",
    "message": "请求参数校验失败",
    "details": [
        {
            "field": "query.code",
            "message": "Field required",
            "error_type": "missing"
        }
    ]
}
```

相关代码位置：

- `app/core/errors.py`: 统一创建业务异常
- `app/schemas/common.py`: 统一错误响应模型
- `app/main.py`: 全局 HTTPException / RequestValidationError 异常处理

当前已经使用的常见错误码：

- `token_missing`: 请求没有携带 Bearer Token
- `token_invalid`: Bearer Token 无效或格式错误
- `token_subject_missing`: JWT 中缺少 `sub`
- `user_not_found`: Token 对应的平台用户不存在
- `account_inactive`: 账号已禁用或未激活
- `character_claim_missing`: JWT 中缺少 `character_id`
- `character_not_found`: Token 对应的角色不存在
- `character_token_missing`: 角色缺少可用 ESI access_token
- `validation_error`: 请求参数或请求体校验失败
- `sso_token_invalid`: EVE SSO 授权码或 refresh_token 无效
- `sso_verify_failed`: EVE SSO token 校验失败
- `sso_upstream_failed`: EVE SSO 上游返回异常
- `sso_upstream_unavailable`: EVE SSO 上游暂时不可用
- `esi_upstream_failed`: EVE ESI 上游返回异常或请求失败

推荐约定：

1. 鉴权类错误尽量在 `app/api/deps.py` 统一抛出，不要散落在各个 endpoint 里重复判断。
2. 外部服务错误尽量在 `app/services/` 内转成业务可识别的错误码，不要把原始上游错误文本直接返回给前端。
3. endpoint 层只负责补充当前接口自己的业务错误，例如 `character_token_missing`、`esi_upstream_failed`。

## 开发流程总览

如果你要新增一个功能，建议固定按下面这条链路推进：

1. 先定义“前端最终要什么字段”
2. 再判断这个功能是只查本地数据库，还是需要请求 ESI
3. 如果需要持久化，就先补模型和迁移
4. 再写 CRUD 或 Service
5. 最后写 endpoint 和 schema，把返回格式整理给前端

不要一上来先写 endpoint。这个项目现在已经分层了，最稳的方式是先定数据，再定路由。

## 新功能落地流程

下面以“新增一个业务接口”为例，按从上到下的顺序说明。

### 1. 先确认功能类型

先判断这个功能属于哪一类：

- 只读本地数据库数据
- 需要请求 ESI 但不落库
- 需要请求 ESI 并写入本地数据库
- 需要登录态或角色 token 的受保护接口

这一步决定你后面要动哪些目录。

### 2. 先想清楚前端最终要的响应

你先不要急着写数据库或 endpoint，先写清楚前端最终要拿到什么。

例如：

- 前端到底要原始 ESI 字段，还是要翻译后的业务字段
- 时间字段是原始字符串，还是 `datetime`
- ID 是否要顺手翻译成名称
- 错误时要什么 `error_code`

如果这一步没想清楚，后面很容易在 service、crud、schema 里反复返工。

### 3. 定义 Schema

先写 schema，再写 endpoint。

文件落点：

- 新增接口请求/响应模型：`app/api/v1/schemas/<module>.py`
- 跨版本通用模型：`app/schemas/`

建议：

1. 请求参数写成 Request Schema 或 Query Schema
2. 返回值写成 Response Schema
3. 给字段补 `description`、`examples`
4. GET 查询参数优先用 `Annotated[..., Query()]`

例子：

- `app/api/v1/schemas/universe.py`
- `app/api/v1/schemas/industry.py`
- `app/api/v1/schemas/auth.py`

### 4. 如果要落库，先改 Model

只要这个功能需要新增表、字段、索引、外键，就先改 ORM 模型。

文件落点：

- 新模型文件：`app/models/<module>.py`
- 模型聚合导出：`app/models/__init__.py`

规则：

1. 新模型必须在 `app/models/__init__.py` 里导入，不然 Alembic 扫不到
2. 公共字段命名要和当前项目风格一致
3. 时间字段尽量使用 timezone-aware `DateTime(timezone=True)`

### 5. 生成数据库迁移

改完模型后，马上生成 Alembic 迁移，不要等到后面一起补。

常用命令：

```bash
/Users/wangjianguo/Desktop/EVE/eve_client/eve-server/.venv/bin/alembic revision --autogenerate -m "your_change"
/Users/wangjianguo/Desktop/EVE/eve_client/eve-server/.venv/bin/alembic upgrade head
```

文件落点：

- 迁移文件：`alembic/versions/*.py`

如果涉及建表、加索引、改字段类型，优先先看 `ALEMBIC_CHECKLIST.md`。

### 6. 写 Service 还是写 CRUD

这是现在最容易乱的地方，可以按下面规则区分：

放到 `app/services/` 的逻辑：

- 请求 EVE SSO
- 请求 EVE ESI
- 名称解析
- 外部 API 适配
- token 刷新

放到 `app/crud/` 的逻辑：

- 查数据库
- 写数据库
- Upsert
- 聚合数据库内的业务读写逻辑

简单判断：

- 只要碰外部 HTTP，优先放 `services/`
- 只要碰数据库持久化，优先放 `crud/`
- 如果既要请求外部 API 又要写库，通常是 endpoint 调 service，再调 crud

当前参考文件：

- `app/services/eve_esi.py`
- `app/services/eve_sso.py`
- `app/crud/user.py`

### 7. 写 Endpoint

当前 v1 接口文件统一放在：

- `app/api/v1/endpoints/auth.py`
- `app/api/v1/endpoints/users.py`
- `app/api/v1/endpoints/universe.py`
- `app/api/v1/endpoints/industry.py`

如果你要新增一个新模块，例如 market、assets、characters，建议直接创建：

- `app/api/v1/endpoints/market.py`
- `app/api/v1/schemas/market.py`

然后在以下位置接线：

- `app/api/v1/endpoints/__init__.py`
- `app/api/v1/schemas/__init__.py`
- `app/api/v1/router.py`

endpoint 层建议只做这几件事：

1. 收请求参数
2. 调依赖拿当前用户/当前角色
3. 调 service 或 crud
4. 做少量组装
5. 返回 response schema

不要把大量数据库逻辑和外部 HTTP 逻辑都塞在 endpoint 里。

### 8. 如果需要登录态或角色 Token

当前项目已经有现成依赖，不要重复造轮子。

可直接复用：

- `app/api/deps.py` 中的 `get_current_user`
- `app/api/deps.py` 中的 `get_current_character`

如果接口需要访问受保护 ESI：

1. 优先拿 `current_character`
2. 它内部会走 token 校验和刷新链路
3. 再把 `current_character.access_token` 传给 service

不要在每个 endpoint 里手写 refresh token 逻辑。

### 9. 如果需要把 ESI 数据写回数据库

推荐顺序：

1. endpoint 调 service 请求 ESI
2. service 返回标准化数据
3. endpoint 或上层业务逻辑调用 crud 写库
4. 最后再返回给前端 response schema

如果你直接在 service 里顺手写库，后面会越来越难拆和测试。

### 10. 如何判断该在哪个文件夹新建文件

最简单的速查表：

- 新接口路由：`app/api/v1/endpoints/`
- 新接口请求/响应模型：`app/api/v1/schemas/`
- 通用错误模型、共享 schema：`app/schemas/`
- 外部 HTTP 对接：`app/services/`
- 数据库读写：`app/crud/`
- ORM 表结构：`app/models/`
- 数据库迁移：`alembic/versions/`
- 全局配置：`app/core/`

### 11. 新增一个完整功能时的最小 Checklist

你以后可以直接照这个顺序走：

1. 在 `app/api/v1/schemas/<module>.py` 写请求和响应模型
2. 如果要落库，在 `app/models/<module>.py` 写模型
3. 在 `app/models/__init__.py` 注册模型
4. 生成 Alembic migration 并升级数据库
5. 在 `app/services/<module>.py` 或已有 service 中补外部 API 逻辑
6. 在 `app/crud/<module>.py` 写数据库读写逻辑
7. 在 `app/api/v1/endpoints/<module>.py` 写接口
8. 在 `app/api/v1/endpoints/__init__.py` 和 `app/api/v1/router.py` 注册路由
9. 在 `app/api/v1/schemas/__init__.py` 导出 schema
10. 打开 `/docs` 检查 Swagger
11. 联调请求，确认成功响应和错误响应都符合 schema

### 12. 一个具体例子：新增市场订单接口

假设你要加“当前角色市场订单”接口，可以按下面落地：

1. 先建 `app/api/v1/schemas/market.py`
2. 定义 `MarketOrdersQueryParams` 和 `MarketOrdersResponse`
3. 如果只是读 ESI，不落库，可以不改 model
4. 在 `app/services/eve_esi.py` 新增 `get_character_market_orders(...)`
5. 在 `app/api/v1/endpoints/market.py` 写 `GET /api/v1/market/orders/me`
6. 用 `get_current_character` 拿当前角色和 token
7. 如果订单里有 `type_id`、`location_id`、`system_id` 等可解析 ID，就继续复用 `resolve_ids(...)` 做名称翻译
8. 在 `app/api/v1/endpoints/__init__.py` 和 `app/api/v1/router.py` 注册 `market_router`
9. 打开 `/docs` 检查字段说明

如果这个接口还要把市场订单缓存到本地数据库，再额外补：

1. `app/models/market.py`
2. `app/crud/market.py`
3. Alembic migration

## 开发指南 (Development Guide)

### 0. 开发前置条件

开始前请先确认以下条件满足：

- 已安装 Python 3.12 左右版本
- 本地或远程 PostgreSQL 可连接
- `eve-server/.env.development` 已正确配置
- 如果数据库通过 SSH 隧道暴露到本机，请确认 `localhost:5432` 已监听
- EVE SSO 相关环境变量已正确配置，例如 `ESI_CLIENT_ID`、`CLIENT_SECRET`、`ESI_CALLBACK_URL`

### 1. 创建并激活虚拟环境 (venv)

首次拉起项目时：

```bash
cd eve-server
python3 -m venv .venv
source .venv/bin/activate
```

之后日常开发只需要：

```bash
cd eve-server
source .venv/bin/activate
```

> **提示**：激活成功后，你的终端命令行最前面会出现 `(.venv)` 字样。如果你想退出虚拟环境，可以直接运行命令 `deactivate`。

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 初始化数据库结构

第一次运行项目，或者模型结构刚刚发生变化时，先执行数据库迁移：

```bash
/Users/wangjianguo/Desktop/EVE/eve_client/eve-server/.venv/bin/alembic upgrade head
```

迁移相关的详细规范和排障说明见 `eve-server/ALEMBIC_CHECKLIST.md`。

### 4. 启动前检查

启动 FastAPI 前建议先确认：

1. `eve-server/.env.development` 中的 `DATABASE_URL` 正确
2. 数据库端口可连，例如 `localhost:5432`
3. 虚拟环境 `.venv` 已激活
4. Alembic 迁移已执行到最新版本

可选检查命令：

```bash
lsof -iTCP:5432 -sTCP:LISTEN
/Users/wangjianguo/Desktop/EVE/eve_client/eve-server/.venv/bin/alembic current
```

### 5. 启动本地服务

在已激活虚拟环境的状态下，指定对应的环境变量文件（如 `.env.development`）并启动 FastAPI：

```bash
export PYTHONPATH=.
dotenv -f .env.development run -- uvicorn app.main:app --reload --port 8000
```

启动后，FastAPI 会在 `lifespan` 中自动初始化 `eve_esi.py` 和 `eve_sso.py` 的共享 HTTP session。

如果服务正常启动，你可以进一步验证：

```bash
curl http://127.0.0.1:8000/health
```

如果项目启用了文档页面，也可以直接访问：

```text
http://127.0.0.1:8000/docs
```

### 6. 常用开发命令

```bash
/Users/wangjianguo/Desktop/EVE/eve_client/eve-server/.venv/bin/alembic current
/Users/wangjianguo/Desktop/EVE/eve_client/eve-server/.venv/bin/alembic history
/Users/wangjianguo/Desktop/EVE/eve_client/eve-server/.venv/bin/alembic revision --autogenerate -m "your_change"
/Users/wangjianguo/Desktop/EVE/eve_client/eve-server/.venv/bin/alembic upgrade head
```

### 7. 推荐开发顺序

建议按以下顺序开展本地开发：

1. 激活 `.venv`
2. 安装依赖
3. 检查 `.env.development`
4. 确认数据库连通
5. 执行 `alembic upgrade head`
6. 启动 `uvicorn`
7. 再进行接口调试与联调

### 8. 关键入口文件

如果你第一次接手这个后端，建议按这个顺序阅读：

1. `app/main.py`: 看应用启动方式、统一路由挂载和 lifespan 生命周期
2. `app/core/config.py`: 看环境变量和配置来源
3. `app/database.py`: 看数据库引擎和 Session
4. `app/api/router.py`: 看总路由如何统一聚合 v1 和 v2
5. `app/api/v1/router.py`: 看 v1 路由如何统一聚合
6. `app/api/v1/endpoints/`: 看各业务模块对应的接口实现
7. `app/api/v1/schemas/`: 看接口输入输出的数据结构定义
8. `app/services/eve_sso.py`: 看 SSO 鉴权链路
9. `app/services/eve_esi.py`: 看外部 ESI 请求、缓存和名称解析逻辑
10. `app/crud/user.py`: 看角色 token 持久化和 refresh helper
11. `app/models/__init__.py`: 看 Alembic 扫描依赖的模型聚合入口
12. `alembic/env.py`: 看迁移环境如何加载元数据
