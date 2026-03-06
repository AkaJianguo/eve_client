from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api import api_router
from app.schemas import ErrorResponse, HealthResponse, ValidationErrorItem, ValidationErrorResponse
from .core.config import settings
from app.services.eve_esi import esi_service
from app.services.eve_sso import sso_service


@asynccontextmanager
async def lifespan(_: FastAPI):
    await esi_service.start()
    await sso_service.start()
    try:
        yield
    finally:
        await esi_service.close()
        await sso_service.close()


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# 配置跨域 (为你的 Vue3 前端开启)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 生产环境请限制为前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _http_error_code(status_code: int) -> str:
    return {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        422: "validation_error",
        502: "bad_gateway",
        503: "service_unavailable",
    }.get(status_code, "http_error")


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        content = exc.detail
    else:
        content = ErrorResponse(
            error_code=_http_error_code(exc.status_code),
            message=str(exc.detail),
        ).model_dump()
    return JSONResponse(status_code=exc.status_code, content=content, headers=exc.headers)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        ValidationErrorItem(
            field=".".join(str(part) for part in error["loc"]),
            message=error["msg"],
            error_type=error["type"],
        )
        for error in exc.errors()
    ]
    content = ValidationErrorResponse(
        error_code="validation_error",
        message="请求参数校验失败",
        details=details,
    ).model_dump()
    return JSONResponse(status_code=422, content=content)


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="健康检查",
    description="返回服务运行状态和版本号，通常用于容器探针、反向代理探活或本地联调确认服务是否启动成功。",
    responses={200: {"description": "服务正常运行"}},
)
async def health_check():
    return {"status": "running", "version": "1.0.0"}

app.include_router(api_router)