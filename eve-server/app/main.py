from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

# 配置跨域 (为你的 Vue3 前端开启)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 生产环境请限制为前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "running", "version": "1.0.0"}

# 之后在这里注册路由
# app.include_router(auth.router, prefix="/api/v1")