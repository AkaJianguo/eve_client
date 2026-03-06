from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import UniverseNamesRequest, UniverseNamesResponse
from app.database import get_db
from app.schemas import ValidationErrorResponse
from app.services.eve_esi import esi_service


router = APIRouter(prefix="/api/v1/universe", tags=["Universe"])


@router.post(
    "/names",
    response_model=UniverseNamesResponse,
    summary="批量翻译 EVE ID",
    description="接收一组 EVE 相关 ID，优先走 SDE、本地缓存，再回退到 ESI 批量解析名称。适合前端做角色、地点、物品和设施名称展示。",
    responses={
        200: {"description": "成功返回 ID 到名称的映射结果"},
        422: {"description": "请求体缺失、ID 数组为空、数量超限或包含非法值", "model": ValidationErrorResponse},
    },
)
async def resolve_eve_names(
    payload: UniverseNamesRequest,
    db: AsyncSession = Depends(get_db),
):
    """批量翻译 EVE ID 为名称。"""
    result = await esi_service.resolve_ids(db, payload.ids)
    return {
        "status": "success",
        "resolved_count": len(result),
        "data": result,
    }