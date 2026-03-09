# API Integration Checklist

## 目标

这份文档用于检查当前仓库的前后端联调主链路是否正常，覆盖以下流程：

- 浏览器登录
- EVE SSO 回调
- JWT 写入前端
- 当前用户读取
- Industry 页面真实数据读取

## 0. 启动前置条件

先确认以下条件满足：

- SSH 隧道已建立
- Docker 或本机开发服务已启动
- 后端健康检查正常
- 前端页面可访问

推荐先验证：

```bash
curl http://127.0.0.1:8000/health
curl -I http://127.0.0.1:5173
```

## 1. 登录链路检查

浏览器访问：

- `http://127.0.0.1:5173/login`

预期行为：

- 页面显示登录入口
- 点击“使用 EVE SSO 登录”后跳到后端 `/api/v1/auth/login`
- 后端再跳转到 EVE 官方 SSO

如果这里失败，优先检查：

- 前端是否已启动
- 代理是否正确把 `/api` 转发到后端
- 后端 `/api/v1/auth/login` 是否能在浏览器打开

## 2. 回调链路检查

完成 EVE SSO 后，预期链路是：

1. EVE 回调后端 `/api/v1/auth/callback`
2. 后端签发本站 JWT
3. 后端重定向到前端 `/login/callback`
4. 前端回调页写入 token 并拉取 `/api/v1/users/me`
5. 浏览器最终跳到 `/dashboard`

如果这里失败，优先检查：

- `FRONTEND_URL` 是否正确
- 浏览器请求 `/api/v1/auth/callback` 时是否带 `Accept: text/html`
- 前端 `/login/callback` 路由是否存在
- 本地存储里是否生成 `eve_access_token`

## 3. 用户状态检查

登录完成后，前端会请求：

- `GET /api/v1/users/me`

预期行为：

- 请求带有 `Authorization: Bearer <token>`
- 返回当前用户信息
- 页面布局右上角显示角色名

如果这里失败，优先检查：

- JWT 是否写入 localStorage
- 请求拦截器是否附加 Bearer Token
- 后端是否返回 401 或 403

## 4. Industry 页面检查

浏览器访问：

- `http://127.0.0.1:5173/industry`

前端会请求：

- `GET /api/v1/industry/jobs/me`

预期行为：

- 返回真实工业工单数据
- 页面能展示蓝图、产出物、设施、执行人、批次、ETA、状态
- 点击“刷新工单”会重新拉取数据

如果这里失败，优先检查：

- 当前角色是否已经完成 SSO 并具备相应权限
- 后端是否能访问 ESI
- 返回 JSON 里是否包含 `jobs`
- 前端字段读取是否和后端返回字段一致

## 5. 常见故障速查

### 登录后跳回登录页

通常原因：

- `/login/callback` 没拿到 `access_token`
- token 写入失败
- `/users/me` 返回 401

### 后端在 Docker 里无法连数据库

通常原因：

- SSH 隧道没开
- `DATABASE_URL` 仍写成 `localhost`
- Docker 场景没有改成 `host.docker.internal`

### 前端页面打开正常，但接口全部 404 或 502

通常原因：

- Vite 代理目标未指向后端
- Docker 网络中的前端没有把 `/api` 代理到 `eve-server`

## 6. 建议排查顺序

如果前后端联调出问题，按下面顺序最省时间：

1. 看浏览器 Network
2. 看后端容器日志或 uvicorn 日志
3. 看 `/health`
4. 看 `/docs`
5. 单独调用 `/users/me` 或 `/industry/jobs/me`

## 7. 当前已验证状态

截至当前仓库状态，以下内容已验证：

- Docker 可启动前后端容器
- 后端 `/health` 正常
- 前端 5173 可访问
- 浏览器登录可完成
- Industry 页面可读取真实接口
