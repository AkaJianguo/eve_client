import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api import api_router
from app.api.v1.endpoints.wallet import warm_wallet_cache_for_active_characters
from app.schemas import ErrorResponse, HealthResponse, ValidationErrorItem, ValidationErrorResponse
from .core.config import settings
from app.services.eve_esi import esi_service
from app.services.eve_sso import sso_service


logger = logging.getLogger(__name__)


async def _wallet_cache_warmup_loop() -> None:
    while True:
        try:
            refreshed_count = await warm_wallet_cache_for_active_characters(settings.WALLET_CACHE_WARMUP_BATCH_SIZE)
            logger.info("wallet cache warmup finished: refreshed_characters=%s", refreshed_count)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("wallet cache warmup loop failed")

        await asyncio.sleep(settings.WALLET_CACHE_WARMUP_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(_: FastAPI):
    wallet_warmup_task: asyncio.Task[None] | None = None
    await esi_service.start()
    await sso_service.start()

    # 预热任务在服务启动后立即跑一轮，此后按固定间隔刷新活跃角色的钱包缓存。
    if settings.WALLET_CACHE_WARMUP_ENABLED:
        wallet_warmup_task = asyncio.create_task(_wallet_cache_warmup_loop())

    try:
        yield
    finally:
        if wallet_warmup_task is not None:
            wallet_warmup_task.cancel()
            with suppress(asyncio.CancelledError):
                await wallet_warmup_task
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