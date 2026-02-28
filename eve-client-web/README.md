eve-client-web/
├── public/                 # 静态资源（如 EVE 物品图标、Logo）
├── src/
│   ├── api/                # 后端接口封装
│   │   ├── request.ts      # Axios 实例与拦截器（处理 402 订阅过期）
│   │   ├── market.ts       # 市场相关接口
│   │   ├── industry.ts     # 工业计算接口
│   │   └── subscription.ts # ISK 订单与支付接口
│   ├── assets/
│   │   ├── styles/
│   │   │   ├── main.scss      # 全局样式入口
│   │   │   ├── variables.scss # EVE 调色板与 CSS 变量
│   │   │   └── mixins.scss    # 常用混合（如科幻发光效果）
│   │   └── images/
│   ├── components/         # 公共 UI 组件
│   │   ├── common/         # 基础组件（Button, Modal, Input）
│   │   ├── layout/         # 布局组件（Dock, Header, Sidebar）
│   │   └── business/       # 业务组件（CharCard, PriceTag, OrderItem）
│   ├── hooks/              # 组合式函数（如 useEsiAuth, useSubscription）
│   ├── layout/             # 页面整体框架布局
│   │   ├── DefaultLayout.vue
│   │   └── BlankLayout.vue
│   ├── store/              # Pinia 状态管理
│   │   ├── user.ts         # 用户信息与订阅等级
│   │   ├── character.ts    # 多角色列表与当前选中角色
│   │   └── market.ts       # 市场搜索历史缓存
│   ├── views/              # 页面级组件
│   │   ├── dashboard/      # 角色概览
│   │   ├── market/         # 市场查询
│   │   ├── industry/       # 工业制造计算
│   │   ├── corporation/    # 军团授权中心
│   │   └── billing/        # ISK 订阅/充值页面
│   ├── router/             # 路由配置（含付费权限守卫）
│   ├── utils/              # 工具函数（ISK 格式化、时间计算）
│   ├── App.vue             # 根组件
│   └── main.ts             # 入口文件
├── .env.development        # 开发环境配置
├── .env.production         # 生产环境配置
├── vite.config.ts          # Vite 配置文件
└── package.json
