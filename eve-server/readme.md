eve-backend/
├── app/
│   ├── api/            # 路由（login, character, market）
│   ├── core/           # 配置文件（ESI_CLIENT_ID, DB_URL）
│   ├── models/         # SQLAlchemy 数据库模型
│   ├── schemas/        # Pydantic 数据验证模型
│   ├── services/       # 业务逻辑（ESI 请求封装）
│   ├── database.py     # 数据库连接
│   └── main.py         # 入口文件
├── .env                # 环境变量（敏感信息）
└── requirements.txt