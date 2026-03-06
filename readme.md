EVE_CLIENT/ (根目录)
├── docker-compose.yml           # 基础配置：定义服务名称、镜像和网络
├── docker-compose.override.yml  # 开发配置：代码挂载(Hot Reload)、端口映射
├── docker-compose.prod.yml      # 生产配置：重启策略、环境变量加密、移除端口暴露
├── eve-client-web/              # 前端目录
└── eve-server/                  # 后端目录
