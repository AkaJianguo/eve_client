# API Integration Checklist

这份文档按开发者视角组织，用于验证当前仓库的前后端联调链路，并在出现问题时快速定位故障点。

它不重复解释项目介绍、页面能力和启动背景信息；这些内容放在 [readme.md](readme.md)。

## 适用范围

当前清单覆盖以下链路：

- 浏览器登录
- EVE SSO 回调
- JWT 写入前端
- 当前用户读取
- Industry 页面真实数据读取
- Wallet 页面真实数据读取
- Assets 页面真实数据读取
- Market 页面历史数据读取
- MarketBrowser 页面分类树、物品检索和实时盘口读取

## 1. 联调前检查

先确认以下条件满足：

- SSH 隧道已建立，或 `DATABASE_URL` 已直接指向可访问的云端数据库
- Docker 或本机开发服务已启动
- 后端健康检查正常
- 前端页面可访问
- 数据库迁移已执行到最新版本

推荐先执行：

```bash
curl http://127.0.0.1:8000/health
curl -I http://127.0.0.1:5173
```

如果后端运行在 Docker 中，同时数据库走宿主机 SSH 隧道，还要额外确认：

- `DATABASE_URL` 使用的不是 `localhost`
- 连接地址已改成 `host.docker.internal`

## 2. 登录链路

浏览器访问：

- `http://127.0.0.1:5173/login`

预期行为：

1. 页面显示登录入口。
2. 点击“使用 EVE SSO 登录”后跳到后端 `/api/v1/auth/login`。
3. 后端继续跳转到 EVE 官方 SSO。

如果失败，优先检查：

- 前端是否已启动
- Vite 或 Docker 代理是否把 `/api` 正确转发到后端
- 后端 `/api/v1/auth/login` 是否能在浏览器直接打开

## 3. 回调链路

完成 EVE SSO 后，预期链路如下：

1. EVE 回调后端 `/api/v1/auth/callback`
2. 后端签发本站 JWT
3. 后端重定向到前端 `/login/callback`
4. 前端回调页写入 token 并拉取 `/api/v1/users/me`
5. 浏览器最终跳到 `/profile`

当前登录已包含钱包和资产所需 scope。如果你在较早版本已经登录过，需要重新授权，否则 Wallet 和 Assets 页面会因为 scope 不足而失败。

如果失败，优先检查：

- `FRONTEND_URL` 是否正确
- 浏览器请求 `/api/v1/auth/callback` 时是否带 `Accept: text/html`
- 前端 `/login/callback` 路由是否存在
- 本地存储里是否生成 `eve_access_token`

## 4. 当前用户读取

登录完成后，前端会请求：

- `GET /api/v1/users/me`

预期行为：

- 请求带有 `Authorization: Bearer <token>`
- 返回当前用户信息
- 页面右上角显示角色名

如果失败，优先检查：

- JWT 是否写入 localStorage
- 请求拦截器是否附加 Bearer Token
- 后端是否返回 401 或 403

## 5. Industry 页面

浏览器访问：

- `http://127.0.0.1:5173/industry`

前端会请求：

- `GET /api/v1/industry/jobs/me`

预期行为：

- 返回真实工业工单数据
- 页面展示蓝图、产出物、设施、执行人、批次、ETA、状态
- 点击“刷新工单”会重新拉取数据

如果失败，优先检查：

- 当前角色是否已经完成 SSO 并具备相应权限
- 后端是否能访问 ESI
- 返回 JSON 是否包含 `jobs`
- 前端字段读取是否和后端返回字段一致

## 6. Wallet 页面

浏览器访问：

- `http://127.0.0.1:5173/wallet`

前端会请求：

- `GET /api/v1/wallet/balance`
- `GET /api/v1/wallet/journal?page=1&page_size=...`
- `GET /api/v1/wallet/transactions?page=1&page_size=...`

预期行为：

- 余额卡片显示 ISK 数值
- 财务日记和市场交易表格正常加载
- 分页切换时会重新请求后端
- 页面会根据 `cache_status` 展示缓存命中状态
- 请求失败时页面展示 warning，而不是白屏

如果失败，优先检查：

- 当前角色是否重新授权并具备 `esi-wallet.read_character_wallet.v1`
- 后端是否能访问 ESI 钱包接口
- 数据库迁移是否已经执行到最新版本
- 返回的 `cache_status` 是否符合前端约定

## 7. Assets 页面

浏览器访问：

- `http://127.0.0.1:5173/assets`

前端会请求：

- `GET /api/v1/assets/me?page=1&page_size=...`

后端还会向 ESI 请求：

- `GET /characters/{character_id}/assets`
- `POST /characters/{character_id}/assets/locations`
- `POST /characters/{character_id}/assets/names`

预期行为：

- 资产表格正常加载
- 蓝图数、唯一实例数、数量总和统计卡片正常显示
- 部分飞船或货柜会显示自定义名称
- 翻页会触发新的后端分页请求

如果失败，优先检查：

- 当前角色是否重新授权并具备 `esi-assets.read_assets.v1`
- 数据库是否已经完成新增资产和钱包表的迁移
- 某些 `location_id` 是否属于容器内部实例；这种情况下前端允许回退显示 `ID: xxxxx`

## 8. Market 页面

浏览器访问：

- `http://127.0.0.1:5173/market`

前端会请求：

- `GET /api/v1/market/history/{type_id}`

预期行为：

- 图表能够正常渲染价格和成交量
- 首次查询可能稍慢，后续同一物品应优先命中本地缓存
- 如果 ESI 短暂失败但本地已有缓存，页面仍能显示历史数据

如果失败，优先检查：

- `market_history` 表是否存在
- 后端是否能访问 ESI `/markets/{region_id}/history/`
- 前端传入的 `type_id` 和区域参数是否正确

## 9. MarketBrowser 页面

浏览器访问：

- `http://127.0.0.1:5173/market-browser`

前端会请求：

- `GET /api/v1/sde/market-groups/tree`
- `GET /api/v1/sde/types?group_id=...`
- `GET /api/v1/sde/types/search?name=...`
- `GET /api/v1/market/orders/{type_id}?region_id=...`

预期行为：

- 左侧分类树正常加载
- 选择分类后能看到物品列表
- 搜索物品时能返回匹配结果
- 选择物品后右侧实时盘口正常展示
- 订单中的 `location_name`、`system_name` 已被后端补齐
- PLEX 等全局市场物品会显示“自动切换到全局市场”提示

如果失败，优先检查：

- 数据库是否已导入 `sde.vw_unified_market_tree` 和 `sde.types`
- `/api/v1/sde/*` 是否返回 `503` 明确提示当前数据库未导入 SDE
- 后端是否能访问 ESI 市场订单接口
- 名称解析链路是否正常工作：L1 内存缓存 -> `sde.vw_universal_names` -> `UniverseName` -> ESI

## 10. 观测点

联调时建议同时看三类信息：

1. 浏览器 Network，确认请求路径、状态码和响应结构。
2. 后端日志，确认是否访问 ESI、是否触发缓存命中、是否有数据库错误。
3. Swagger `/docs`，确认接口参数和返回结构是否与前端读取字段一致。

如果优先想判断是前端问题还是后端问题，通常先直接调用以下接口最省时间：

- `/api/v1/users/me`
- `/api/v1/industry/jobs/me`
- `/api/v1/wallet/balance`
- `/api/v1/assets/me`
- `/api/v1/market/history/{type_id}`
- `/api/v1/market/orders/{type_id}?region_id=...`

## 11. 常见故障速查

### 登录后跳回登录页

通常原因：

- `/login/callback` 没拿到 `access_token`
- token 写入失败
- `/users/me` 返回 401

### Wallet 或 Assets 一直 403 / 502

通常原因：

- 角色是在扩充 scope 之前登录的，旧 token 没有钱包或资产权限
- 没有重新走 EVE SSO 授权
- 后端已经更新，但数据库迁移没跑

### 后端在 Docker 里无法连数据库

通常原因：

- SSH 隧道没开
- `DATABASE_URL` 仍写成 `localhost`
- Docker 场景没有改成 `host.docker.internal`

### MarketBrowser 左侧树空白或返回 503

通常原因：

- 当前数据库没有导入 `sde.vw_unified_market_tree`
- `sde.types` 不存在或字段不兼容
- 当前后端连接到的不是预期数据库

### MarketBrowser 有订单数但位置名称为空

通常原因：

- 订单接口上游正常，但名称解析链路未命中
- `sde.vw_universal_names` 不存在
- ESI `/universe/names/` 暂时失败，且本地缓存里也没有对应名称

## 12. 建议排查顺序

如果联调出问题，按下面顺序排查最省时间：

1. 看浏览器 Network。
2. 看后端日志或容器日志。
3. 看 `/health`。
4. 看 `/docs`。
5. 单独调用问题页面对应的接口。

## 13. 当前已验证状态

截至当前仓库状态，以下内容已验证：

- Docker 可启动前后端容器
- 后端 `/health` 正常
- 前端 5173 可访问
- 浏览器登录可完成
- Industry 页面可读取真实接口
- Wallet 和 Assets 页面已接入真实数据链路
- 市场历史和市场浏览器接口已接入前端页面
- 数据库迁移已升级到包含资产、钱包和市场历史相关表的最新版本
