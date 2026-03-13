# EVE Client Web

## 当前状态

当前前端已经从默认 Vite 模板切换为可联调的 Vue 3 单页应用，并完成了以下链路：

- 基于 `Naive UI` 的控制台式布局已经落地
- `Pinia` 已用于登录态管理
- `Axios` 请求层已经统一处理 JWT 注入和 401 跳转
- 登录页已经接入后端 `/api/v1/auth/login`
- 登录回调页已经接住后端浏览器重定向 `/login/callback`
- `Profile` 页面已接入 `/api/v1/users/me`，展示飞行员档案信息
- `Industry` 页面已经接入真实接口 `/api/v1/industry/jobs/me`
- `Wallet` 页面已接入 `/api/v1/wallet/*`，展示余额、财务日记和市场成交
- `Assets` 页面已接入 `/api/v1/assets/me`，展示资产清单、位置翻译和基础筛选
- `Wallet` 页面已接入后端 `cache_status`，可以提示当前是新鲜缓存、后台刷新还是冷启动刷新
- `Market` 页面已接入 `/api/v1/market/history/{type_id}`，展示吉他市场的历史价格与成交量图表
- `MarketBrowser` 页面已接入市场分类树、物品检索、实时盘口、地点名称翻译和全局市场物品自动切换提示
- 市场分类树已抽成公共组件，后续制造业等页面可以直接复用同一套树面板与图标图源逻辑

## 技术栈

- Vue 3
- Vite
- TypeScript
- Naive UI
- Pinia
- Axios
- Sass

## 当前目录结构

```text
eve-client-web/
├── public/
├── src/
│   ├── assets/
│   │   └── styles/
│   │       ├── main.scss
│   │       └── variables.scss
│   ├── components/
│   │   ├── EveImage.vue
│   │   └── common/
│   │       ├── EveTreeIconSource.vue
│   │       └── EveTreePanel.vue
│   ├── layouts/
│   │   └── MainLayout.vue
│   ├── router/
│   │   └── index.ts
│   ├── stores/
│   │   ├── auth.ts
│   │   └── universe.ts
│   ├── utils/
│   │   └── request.ts
│   ├── views/
│   │   ├── Dashboard.vue
│   │   ├── Industry.vue
│   │   ├── Market.vue
│   │   ├── MarketBrowser.vue
│   │   ├── Assets.vue
│   │   ├── Profile.vue
│   │   ├── Wallet.vue
│   │   ├── Login.vue
│   │   └── LoginCallback.vue
│   ├── App.vue
│   └── main.ts
├── Dockerfile
├── package.json
└── vite.config.ts
```

## 路由说明

当前前端主要路由如下：

- `/login`：登录页，点击后跳转到后端 `/api/v1/auth/login`
- `/login/callback`：接收后端回调后的 JWT 和角色信息
- `/profile`：飞行员档案页（**默认登录后进入的页面**）
- `/dashboard`：控制台首页
- `/wallet`：财务中心
- `/assets`：资产清单
- `/market`：市场情报
- `/market-browser`：市场浏览器
- `/industry`：工业监控页

路由守卫定义在 `src/router/index.ts`：

- 未登录用户访问业务页时跳转到 `/login`
- 已登录用户访问 `/login` 或 `/login/callback` 时跳转到 `/profile`

## 登录流程

当前登录流程如下：

1. 用户打开 `/login`
2. 点击“使用 EVE SSO 登录”
3. 浏览器跳转到后端 `/api/v1/auth/login`
4. 后端跳转到 EVE 官方 SSO
5. EVE 回调后端 `/api/v1/auth/callback`
6. 后端签发本站 JWT，并重定向到前端 `/login/callback`
7. 前端回调页把 token 写入本地存储，再请求 `/api/v1/users/me`
8. 登录完成后跳转到 `/profile`（飞行员档案页）

## 请求层说明

请求层位于 `src/utils/request.ts`，当前约定如下：

- 所有请求默认以 `/api/v1` 为基础路径
- 如果本地存在 `eve_access_token`，会自动附加 `Authorization: Bearer <token>`
- 如果后端返回 401，前端会清掉本地 token，并自动跳转到 `/login`

## 主要页面说明

### Profile（飞行员档案）

文件：`src/views/Profile.vue`

- 显示当前飞行员头像、名称、军团和联盟信息
- 展示安全等级、出舱日期、系统权限等级
- 调用 `/api/v1/users/me` 获取飞行员信息
- 调用 `/api/v1/universe/names` 翻译军团/联盟 ID
- 使用 EVE 官方 CDN 渲染头像和军团 Logo

### Login

文件：`src/views/Login.vue`

- 展示登录入口和授权说明
- 点击按钮后直接跳到后端登录接口

### LoginCallback

文件：`src/views/LoginCallback.vue`

- 接收后端 query 中的 `access_token`
- 写入 `Pinia` 和 `localStorage`
- 再请求 `/users/me` 补齐用户状态

### Dashboard

文件：`src/views/Dashboard.vue`

- 当前是控制台风格的总览页
- 以运营面板和示意数据为主，适合作为后续资产、市场、订单模块的入口页

### Industry

文件：`src/views/Industry.vue`

- 当前已接入真实接口 `/api/v1/industry/jobs/me`
- 支持前端关键字筛选、状态筛选和手动刷新
- 当前展示字段包括蓝图、产出物、设施、执行人、批次、ETA、状态

### Wallet

文件：`src/views/Wallet.vue`

- 已接入 `/api/v1/wallet/balance`、`/api/v1/wallet/journal`、`/api/v1/wallet/transactions`
- 已展示收入/支出、买卖统计卡片
- 支持关键字筛选、买卖方向筛选和空状态展示
- 对交易中的物品和地点做名称翻译
- 已根据后端 `cache_status` 展示缓存状态提示，区分新鲜缓存、后台刷新和冷启动刷新

当前 `Wallet` 页面对后端缓存状态的约定如下：

- `hit_fresh`：当前数据来自新鲜缓存
- `stale_refreshing`：当前先展示旧缓存，服务端正在后台刷新
- `miss_refreshed`：本次请求已完成冷启动刷新，并回填到数据库缓存

### Assets

文件：`src/views/Assets.vue`

- 已接入 `/api/v1/assets/me`
- 已切换为服务端分页，并展示蓝图、唯一实例和数量汇总卡片
- 支持关键字筛选、蓝图/普通物资筛选和空状态展示
- 复用 `EveImage.vue` 和 `/api/v1/universe/names` 做图标与名称展示
- `/api/v1/universe/names` 在后端会优先命中 L1 内存缓存，再查 `sde.vw_universal_names`、`UniverseName` 和 ESI
- 当后端返回资产自定义名和深层位置时，页面会优先展示这些解析结果

### 公共组件

- `src/components/EveImage.vue`
  - 用于渲染 EVE 官方 `images.evetech.net` 的物品类型图
  - 当前已被 Assets、Industry、MarketBrowser 等页面复用
- `src/components/common/EveTreePanel.vue`
  - 用于渲染带标题、加载态和统一风格的树状面板
  - 当前已接入 MarketBrowser，后续制造业页面可以直接复用
- `src/components/common/EveTreeIconSource.vue`
  - 专门负责树节点的图源拼接
  - 通过 `iconName` 输出 `/eve-icons/...` 本地静态图标地址

### Market

文件：`src/views/Market.vue`

- 已接入 `/api/v1/market/history/{type_id}`
- 当前默认查询吉他区域的三钛合金历史数据
- 顶部提供常见硬通货快捷选择器，例如 Tritanium、PLEX、Ishtar
- 使用 `ECharts` 绘制平均价格折线、MA5 均线和成交量柱状图
- 支持窗口缩放自适应和空状态提示

### MarketBrowser

文件：`src/views/MarketBrowser.vue`

- 采用左侧分类树、右侧星域切换与实时盘口的经典市场浏览器布局
- 左侧通过 `/api/v1/sde/market-groups/tree` 读取市场分类树
- 左侧树展示由 `src/components/common/EveTreePanel.vue` 承担
- 树节点图标由 `src/components/common/EveTreeIconSource.vue` 承担
- 右侧订单表通过 `/api/v1/market/orders/{type_id}?region_id=...` 读取实时盘口
- 后端会把订单中的 `location_id` 和 `system_id` 翻译成可读名称，前端直接展示星系和空间站/星堡位置
- 对全局市场物品，页面会显示“该物品已自动切换到全局市场”提示
- 当前前端本地白名单已包含 `44992`（PLEX），与后端重定向规则保持一致

当前如果要启用树节点图标，只需要把对应图片放到前端 `public/eve-icons/` 目录。

这个页面的左侧树依赖后端数据库已经导入 `sde.marketGroups`（或兼容的 `sde.market_groups`）和 `sde.types`，右侧实时盘口则依赖后端透传 ESI 市场订单接口。

如果后端当前库没有导入 SDE，页面会收到后端返回的明确错误信息，而不是静默空白。

## 状态管理

### auth store

文件：`src/stores/auth.ts`

当前负责：

- 保存 JWT
- 保存当前用户简要信息
- 保存当前角色名
- 提供 `logout()` 清理登录态

## 开发启动

### 本机开发

```bash
cd eve-client-web
pnpm install
pnpm dev
```

默认访问地址：<http://127.0.0.1:5173>

当前前端依赖管理已统一为 `pnpm`。如果本机更新了依赖，Docker 前端容器也需要重新执行一次安装流程，最直接的做法是重启 `eve-client` 容器或重新 `docker compose up`。

## 授权说明

当前前端依赖以下 ESI 授权范围：

- `esi-industry.read_character_jobs.v1`
- `esi-wallet.read_character_wallet.v1`
- `esi-assets.read_assets.v1`

如果你在本次更新之前已经登录过，需要先退出并重新完成一次 EVE SSO 授权，否则 Wallet 和 Assets 页面会因为旧 token 缺少 scope 而无法读取数据。

### Docker 开发

当前 Compose 会为前端注入：

- `VITE_PROXY_TARGET=http://eve-server:8000`

这样前端容器中的 `/api` 请求会自动代理到后端容器。

前端容器现在也统一使用 `pnpm install --frozen-lockfile` 和 `pnpm dev`，因此宿主机与容器会基于同一份 `pnpm-lock.yaml` 安装依赖。

## 构建命令

```bash
pnpm build
```

当前项目已经验证过可成功构建。

当前前端市场页已引入 `echarts`。如果在宿主机新增了图表相关依赖，而 Docker 前端容器尚未更新，请重新拉起 `eve-client` 容器，让容器内重新执行一次 `pnpm install --frozen-lockfile`。

## 下一步建议

当前前端已完成第一轮可用链路，但仍然是“框架已成形，业务模块继续扩展”的阶段。后续优先级建议：

1. 继续扩充 Dashboard 真实数据来源
2. 为 Industry 页增加分页、排序和更多过滤参数
3. 为 Wallet 和 Assets 增加时间范围筛选、位置树还原和价值估算

## 页面开发路线图

下面这份路线图按“已经有基础骨架”到“适合继续接真实接口”的顺序整理。

### P0

- Dashboard
  - 接入 `/api/v1/users/me` 的更多用户字段
  - 接入工业概览统计接口，例如工单总数、进行中工单、即将完成工单
  - 把当前示意数据卡片替换成真实统计数据
- Industry
  - 增加服务端分页参数
  - 增加开始时间、结束时间、状态排序
  - 增加更多业务字段，例如安装地点、活动类型、角色 ID

### P1

- Market
  - 增加更多预设物资与搜索能力
  - 扩展价格摘要、涨跌幅和更完整的市场情报卡片
  - 补充区域切换与更多均线指标
- Characters
  - 展示当前登录角色、订阅状态、权限范围、Token 健康度

### 已落地模块待增强

- Wallet
  - 增加时间范围筛选
  - 增加按 ref_type、物品类型、地点的组合过滤
- Assets
  - 增加价值估算、位置树还原和更完整的深层容器解析

### P2

- Corporation
  - 接入军团授权、军团工业、军团资产相关接口
- Billing
  - 如果未来存在订阅或增值服务，再把支付、订阅状态单独抽为页面

## 推荐文件落点

如果继续扩前端，建议按下面方式落文件：

- 新页面：`src/views/<Page>.vue`
- 通用展示组件：`src/components/common/`
- 新业务组件：`src/components/` 下按业务拆分
- 新状态管理：`src/stores/<module>.ts`
- 新请求封装：`src/utils/request.ts` 基础上再按业务拆 helper

## 联调手册

前后端联调顺序和检查清单见根目录新增文档：`API_INTEGRATION_CHECKLIST.md`
