# EVE_CLIENT

```text
EVE_CLIENT/ (根目录)
├── docker-compose.yml           # 基础配置：定义服务名称、镜像和网络
├── docker-compose.override.yml  # 开发配置：代码挂载(Hot Reload)、端口映射
├── docker-compose.prod.yml      # 生产配置：重启策略、环境变量加密、移除端口暴露
├── eve-client-web/              # 前端目录
└── eve-server/                  # 后端目录
```

## Docker 当前用途

当前 Compose 的定位是：

- `eve-server`：后端 FastAPI 容器
- `eve-client`：前端 Vite 容器
- `db`：仅保留为可选本地 Postgres，默认不启动

当前项目数据库以云端为主，因此默认开发链路并不依赖 `db` 服务。

## 当前联调状态

当前仓库已经打通了以下主链路：

- 前端登录页通过 `/api/v1/auth/login` 跳转到 EVE SSO
- 后端在浏览器完成 SSO 回调后，会重定向回前端 `/login/callback`
- 前端回调页会写入本站 JWT，并拉取当前用户信息
- 前端 `Industry` 页面已经接入真实接口 `/api/v1/industry/jobs/me`
- 前端 `Wallet` 页面已经接入 `/api/v1/wallet/balance`、`/api/v1/wallet/journal`、`/api/v1/wallet/transactions`
- 前端 `Assets` 页面已经接入 `/api/v1/assets/me`
- 后端已新增资产与钱包持久化表，并完成 Alembic 迁移
- 后端 `Wallet` 接口已切换为“数据库缓存优先，过期后台刷新，冷启动时再回源 ESI”的模式
- 前端 `Wallet` 页面已接入 `cache_status` 提示，可区分新鲜缓存、后台刷新和冷启动刷新
- Docker 开发模式已经验证可启动前后端容器

当前主要页面：

- `/login`：登录页
- `/profile`：飞行员档案页（**首页**）
- `/dashboard`：控制台概览页
- `/wallet`：财务中心
- `/assets`：资产清单
- `/industry`：工业监控页

当前登录会申请以下 ESI scope：

- `esi-industry.read_character_jobs.v1`
- `esi-wallet.read_character_wallet.v1`
- `esi-assets.read_assets.v1`

如果你是在本次更新前就登录过，必须重新走一次 SSO 授权，否则旧 token 不具备钱包和资产权限。

联调顺序与排查步骤见：`API_INTEGRATION_CHECKLIST.md`

## Wallet 缓存策略

当前钱包接口不再默认阻塞等待 ESI 在线返回，而是优先读取数据库中的已持久化数据：

- 如果本地缓存仍在 TTL 内，接口直接返回缓存数据
- 如果本地缓存已过期，接口先返回旧缓存，再在后台异步刷新
- 如果本地没有任何缓存，接口才会同步请求一次 ESI 并把结果写入数据库

当前接口响应会附带 `cache_status` 字段，前端可据此展示状态提示：

- `hit_fresh`：命中新鲜缓存
- `stale_refreshing`：返回旧缓存，后台正在刷新
- `miss_refreshed`：本次请求发生冷启动刷新，并已写入缓存

服务启动后，后端还会按固定周期预热最近活跃角色的钱包缓存，尽量减少用户首次打开页面时的等待。

## 开发模式

开发环境会自动叠加 `docker-compose.override.yml`，用于：

- 挂载前后端源码目录，便于热更新
- 暴露 `8000` 和 `5173` 端口
- 为后端加载 `eve-server/.env.development`
- 为前端注入 `VITE_PROXY_TARGET=http://eve-server:8000`

启动方式：

```bash
docker compose up --build
```

如果后端在 Docker 中要连接云端数据库，推荐单独准备一份环境文件：

```bash
cp eve-server/.env.docker.example eve-server/.env.docker
```

然后把其中的 `DATABASE_URL` 改成云端数据库地址，再用下面的命令启动：

```bash
EVE_SERVER_ENV_FILE=./eve-server/.env.docker docker compose up --build
```

启动后访问：

- 前端：<http://127.0.0.1:5173>
- 后端：<http://127.0.0.1:8000>
- Swagger：<http://127.0.0.1:8000/docs>

数据库说明：

- 当前默认开发链路使用云端数据库，不依赖 `db` 容器
- 如果后端跑在 Docker 容器里，`eve-server/.env.development` 中的 `DATABASE_URL` 必须写成容器可访问的地址
- 不要在容器场景里继续使用 `localhost` 指向云端数据库或宿主机隧道
- 如果是直连云端数据库，直接填写云端主机名
- 如果是宿主机上的 SSH 隧道，再改成 `host.docker.internal`

## 常用命令

本机直跑前后端：

```bash
# 终端 1
cd eve-server
source .venv/bin/activate
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 终端 2
cd eve-client-web
npm run dev
```

本机直跑后的访问入口：

- 前端：<http://127.0.0.1:5173>
- 后端：<http://127.0.0.1:8000>
- Swagger：<http://127.0.0.1:8000/docs>

Docker 开发模式：

```bash
cp eve-server/.env.docker.example eve-server/.env.docker
# 先在宿主机建立 SSH 隧道
ssh -p 22222 -N -L 5432:127.0.0.1:5432 ubuntu@43.163.228.205 -i ~/.ssh/NEW_Key.pem

# eve-server/.env.docker 已按 host.docker.internal:5432 准备好
EVE_SERVER_ENV_FILE=./eve-server/.env.docker docker compose up --build
```

如果你已经启动过旧版本后端，在拿到最新代码后建议补跑一次迁移：

```bash
cd eve-server
source .venv/bin/activate
alembic upgrade head
```

如果使用 Docker：

```bash
docker exec eve-server alembic upgrade head
```

如果 SSH 隧道断开，Docker 内的后端也会失去数据库连接。

建议把 SSH 隧道单独保留在一个终端窗口中，不要和 docker compose 共用同一个会话。

停止并清理容器：

```bash
docker compose down
```

如果只是检查 Compose 是否能正确读取 Docker 环境文件，可以先执行：

```bash
EVE_SERVER_ENV_FILE=./eve-server/.env.docker docker compose config
```

## 可选本地数据库

如果未来想临时启用本地 Postgres，而不是云端数据库，可以显式启用 `local-db` profile：

```bash
docker compose --profile local-db up --build
```

此时还需要把后端数据库连接串改为容器内可访问的地址，例如 `db:5432`。

## 当前限制

这套 Compose 现在的重点是本地开发联调，不是完整生产部署：

- `docker-compose.prod.yml` 仅保留了基础运行骨架
- 生产环境通常还需要反向代理、域名、证书和更明确的镜像发布流程
