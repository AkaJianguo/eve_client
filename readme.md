# EVE_CLIENT

EVE_CLIENT 是一个面向 EVE Online 的前后端联调项目，当前已经打通登录、角色资料、工业、钱包、资产、市场历史和市场浏览器等主链路。

这份文档按用户视角组织，重点回答三件事：

- 这个仓库现在能用什么
- 最快怎么把前后端跑起来
- 使用时依赖哪些外部条件

如果你要做接口联调、排查问题或逐步验收页面，请直接看 [API_INTEGRATION_CHECKLIST.md](API_INTEGRATION_CHECKLIST.md)。

如果你要看服务端实现、SDE 依赖和接口设计细节，请看 [eve-server/readme.md](eve-server/readme.md)。

## 当前可用能力

当前仓库已经打通以下主链路：

- 浏览器通过 `/api/v1/auth/login` 跳转到 EVE SSO
- 后端完成 SSO 回调后，重定向回前端 `/login/callback`
- 前端写入本站 JWT，并拉取当前用户信息
- `Industry` 页面已接入真实接口 `/api/v1/industry/jobs/me`
- `Wallet` 页面已接入余额、财务日记和交易记录接口
- `Assets` 页面已接入资产分页、位置翻译和自定义名称展示
- `Market` 页面已接入市场历史缓存接口，可查看吉他区域价格与成交量走势
- `MarketBrowser` 页面已接入市场分类树、物品检索、实时盘口、地点名称翻译和全局市场自动切换提示

当前主要页面：

- `/login`：登录页
- `/profile`：飞行员档案页
- `/dashboard`：控制台概览页
- `/industry`：工业监控页
- `/wallet`：财务中心
- `/assets`：资产清单
- `/market`：市场情报
- `/market-browser`：市场浏览器

## 快速上手

### 推荐方式：Docker 开发模式

当前 Compose 的定位如下：

- `eve-server`：后端 FastAPI 容器
- `eve-client`：前端 Vite 容器
- `db`：可选本地 Postgres，默认不启用

项目默认联调线上数据库或宿主机上的 SSH 隧道，不依赖本地 `db` 容器。

启动步骤：

```bash
cp eve-server/.env.docker.example eve-server/.env.docker
ssh -p 22222 -N -L 5432:127.0.0.1:5432 ubuntu@43.163.228.205 -i ~/.ssh/NEW_Key.pem
EVE_SERVER_ENV_FILE=./eve-server/.env.docker docker compose up --build
```

启动后访问：

- 前端：<http://127.0.0.1:5173>
- 后端：<http://127.0.0.1:8000>
- Swagger：<http://127.0.0.1:8000/docs>

### 可选方式：本机直跑前后端

```bash
# 终端 1
cd eve-server
source .venv/bin/activate
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 终端 2
cd eve-client-web
pnpm install
pnpm dev
```

## 使用前需要知道的事

### 登录权限

当前登录会申请以下 ESI scope：

- `esi-industry.read_character_jobs.v1`
- `esi-wallet.read_character_wallet.v1`
- `esi-assets.read_assets.v1`

如果你是在较早版本登录过，必须重新完成一次 EVE SSO 授权，否则旧 token 不具备钱包和资产权限。

### 数据库连接

当前默认开发链路使用云端数据库，不依赖本地 `db` 容器。

- 宿主机直跑后端时，数据库通常走 `localhost` 上的 SSH 隧道
- Docker 内运行后端时，不能继续使用 `localhost`
- Docker 场景下如果依赖宿主机隧道，应改用 `host.docker.internal`

### SDE 依赖

市场浏览器依赖数据库中的 SDE 数据。

- 左侧分类树依赖 `sde.vw_unified_market_tree`
- 物品静态信息依赖 `sde.types`
- 如果当前数据库未导入 SDE，`/api/v1/sde/*` 接口会返回明确的 `503`

### 前端依赖管理

前端依赖管理已经统一为 `pnpm`：

- Dockerfile 使用 `corepack + pnpm install --frozen-lockfile`
- 开发环境 Compose 使用 `pnpm dev`
- 生产构建使用 `pnpm build`

## 功能说明

### Wallet

钱包接口当前采用“缓存优先，过期后台刷新，冷启动再回源”的模式：

- 命中新鲜缓存时直接返回
- 命中过期缓存时先返回旧数据，再后台刷新
- 本地没有缓存时才同步回源 ESI

接口响应会附带 `cache_status`，前端据此展示状态提示：

- `hit_fresh`
- `stale_refreshing`
- `miss_refreshed`

### Market

市场历史接口采用“按需加载 + 本地缓存”的模式：

- 前端调用 `/api/v1/market/history/{type_id}`
- 后端优先读取本地 `market_history`
- 本地无数据或数据过期时再回源 ESI
- ESI 不可用但本地已有缓存时，优先返回本地历史数据

### MarketBrowser

市场浏览器当前由两部分数据源组成：

- SDE 静态数据：分类树、按组物品列表、搜索结果
- ESI 实时数据：指定物品在指定星域的市场订单

当前页面行为包括：

- 左侧分类树读取 `/api/v1/sde/market-groups/tree`
- 右侧物品列表读取 `/api/v1/sde/types`
- 右上角搜索读取 `/api/v1/sde/types/search`
- 实时盘口读取 `/api/v1/market/orders/{type_id}?region_id=...`
- 订单中的 `location_id`、`system_id` 由后端统一翻译成可读名称
- 对 PLEX 这类全局市场物品，后端会自动切换到全局市场星域，前端显示提示

统一名称解析链路当前为：

- L1 内存缓存
- `sde.vw_universal_names`
- `UniverseName`
- ESI

## 常用命令

重新启动前端容器：

```bash
docker compose up -d eve-client
```

执行后端迁移：

```bash
cd eve-server
source .venv/bin/activate
alembic upgrade head
```

Docker 场景执行迁移：

```bash
docker exec eve-server alembic upgrade head
```

停止并清理容器：

```bash
docker compose down
```

检查 Compose 是否正确读取 Docker 环境文件：

```bash
EVE_SERVER_ENV_FILE=./eve-server/.env.docker docker compose config
```

## 文档分工

- [readme.md](readme.md)：用户视角总览、启动方式、页面能力、外部依赖
- [API_INTEGRATION_CHECKLIST.md](API_INTEGRATION_CHECKLIST.md)：开发者视角联调步骤、接口验证、故障排查
- [eve-server/readme.md](eve-server/readme.md)：后端结构、服务设计、SDE 依赖、接口策略
