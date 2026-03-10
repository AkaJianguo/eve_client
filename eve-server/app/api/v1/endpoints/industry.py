from typing import Any
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_character, get_current_user
from app.api.v1.schemas import IndustryJobsQueryParams, IndustryJobsResponse
from app.core.errors import api_error
from app.database import get_db
from app.models.user import Character, User
from app.schemas import ErrorResponse, ValidationErrorResponse
from app.services.eve_esi import esi_service


router = APIRouter(prefix="/api/v1/industry", tags=["Industry"])


def _collect_resolvable_ids(jobs: list[dict[str, Any]]) -> list[int]:
    ids_to_resolve: set[int] = set()
    for job in jobs:
        for field in (
            "blueprint_type_id",
            "product_type_id",
            "facility_id",
            "installer_id",
            "station_id",
            "blueprint_location_id",
            "location_id",
            "output_location_id",
            "completed_character_id",
        ):
            value = job.get(field)
            if isinstance(value, int) and value > 0:
                ids_to_resolve.add(value)
    return list(ids_to_resolve)


def _attach_resolved_name(
    job: dict[str, Any],
    names_map: dict[int, str],
    source_field: str,
    target_field: str,
    fallback: str,
) -> None:
    value = job.get(source_field)
    if isinstance(value, int):
        job[target_field] = names_map.get(value, fallback)


@router.get(
    "/jobs/me",
    response_model=IndustryJobsResponse,
    summary="获取当前角色的工业任务",
    description="读取当前 JWT 绑定角色的工业任务列表，必要时自动刷新 ESI access_token，并补齐常见名称翻译字段。",
    responses={
        200: {"description": "成功返回工业任务列表"},
        401: {"description": "当前角色没有可用 ESI access_token，需要重新授权", "model": ErrorResponse},
        422: {"description": "查询参数格式不正确", "model": ValidationErrorResponse},
        502: {"description": "EVE ESI 工业接口调用失败", "model": ErrorResponse},
    },
)
async def read_my_industry_jobs(
    params: Annotated[IndustryJobsQueryParams, Query()],
    current_user: User = Depends(get_current_user),
    current_character: Character = Depends(get_current_character),
    db: AsyncSession = Depends(get_db),
):
    """读取当前登录角色的工业任务，并在请求前自动刷新即将过期的 ESI Token。"""
    user_id = int(current_user.id)
    character_id = int(current_character.id)
    character_name = current_character.name
    access_token = current_character.access_token

    if not access_token:
        raise api_error(401, "character_token_missing", "当前角色缺少可用的 ESI 访问令牌，请重新授权")

    jobs = await esi_service.get_character_industry_jobs(
        character_id=character_id,
        access_token=access_token,
        include_completed=params.include_completed,
    )
    if jobs is None:
        raise api_error(502, "esi_upstream_failed", "EVE ESI 工业接口调用失败，请稍后重试")

    names_map = await esi_service.resolve_ids(db, _collect_resolvable_ids(jobs))
    enriched_jobs: list[dict[str, Any]] = []
    for job in jobs:
        enriched_job = dict(job)

        _attach_resolved_name(enriched_job, names_map, "blueprint_type_id", "blueprint_name", "未知蓝图")
        _attach_resolved_name(enriched_job, names_map, "product_type_id", "product_name", "未知产物")
        _attach_resolved_name(enriched_job, names_map, "facility_id", "facility_name", "未知设施")
        _attach_resolved_name(enriched_job, names_map, "installer_id", "installer_name", "未知角色")
        _attach_resolved_name(enriched_job, names_map, "station_id", "station_name", "未知空间站")
        _attach_resolved_name(enriched_job, names_map, "blueprint_location_id", "blueprint_location_name", "未知蓝图位置")
        _attach_resolved_name(enriched_job, names_map, "location_id", "location_name", "未知作业位置")
        _attach_resolved_name(enriched_job, names_map, "output_location_id", "output_location_name", "未知产出位置")
        _attach_resolved_name(enriched_job, names_map, "completed_character_id", "completed_character_name", "未知交付角色")

        enriched_jobs.append(enriched_job)

    return {
        "user_id": user_id,
        "character_id": character_id,
        "character_name": character_name,
        "job_count": len(enriched_jobs),
        "jobs": enriched_jobs,
    }