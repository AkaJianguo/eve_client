from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_character, get_current_user
from app.api.v1.schemas import AssetsResponse
from app.crud.character_ops import sync_character_assets
from app.core.errors import api_error
from app.database import get_db
from app.models.user import Character, User
from app.schemas import ErrorResponse
from app.services.eve_esi import esi_service


router = APIRouter(prefix="/api/v1/assets", tags=["Assets"])


def _collect_asset_ids(entries: list[dict[str, Any]]) -> list[int]:
    ids_to_resolve: set[int] = set()
    asset_item_ids = {entry.get("item_id") for entry in entries if isinstance(entry.get("item_id"), int)}
    for entry in entries:
        type_id = entry.get("type_id")
        if isinstance(type_id, int) and type_id > 0:
            ids_to_resolve.add(type_id)

        location_id = entry.get("location_id")
        if isinstance(location_id, int) and location_id > 0 and location_id not in asset_item_ids:
            ids_to_resolve.add(location_id)
    return list(ids_to_resolve)


def _attach_resolved_name(payload: dict[str, Any], names_map: dict[int, str], source_field: str, target_field: str) -> None:
    value = payload.get(source_field)
    if isinstance(value, int):
        payload[target_field] = names_map.get(value, f"ID: {value}")


def _slice_page[T](items: list[T], page: int, page_size: int) -> list[T]:
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end]


def _build_asset_summary(entries: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "blueprint_count": sum(1 for entry in entries if entry.get("is_blueprint_copy")),
        "singleton_count": sum(1 for entry in entries if entry.get("is_singleton")),
        "total_quantity": sum(int(entry.get("quantity") or 0) for entry in entries),
    }


@router.get(
    "/me",
    response_model=AssetsResponse,
    summary="获取当前角色资产列表",
    description="读取当前 JWT 绑定角色的完整资产列表，并补齐物品与位置名称。",
    responses={
        401: {"description": "当前角色没有可用 ESI access_token，需要重新授权", "model": ErrorResponse},
        502: {"description": "EVE ESI 资产接口调用失败", "model": ErrorResponse},
    },
)
async def read_my_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    current_character: Character = Depends(get_current_character),
    db: AsyncSession = Depends(get_db),
):
    user_id = int(current_user.id)
    character_id = int(current_character.id)
    character_name = current_character.name
    access_token = current_character.access_token

    if not access_token:
        raise api_error(401, "character_token_missing", "当前角色缺少可用的 ESI 访问令牌，请重新授权")

    entries = await esi_service.get_character_assets(
        character_id=character_id,
        access_token=access_token,
    )
    if entries is None:
        raise api_error(502, "esi_upstream_failed", "EVE ESI 资产接口调用失败，请稍后重试")

    item_ids = [int(entry["item_id"]) for entry in entries if entry.get("item_id") is not None]
    asset_locations = await esi_service.get_character_asset_locations(
        character_id=character_id,
        access_token=access_token,
        item_ids=item_ids,
    )
    asset_names = await esi_service.get_character_asset_names(
        character_id=character_id,
        access_token=access_token,
        item_ids=item_ids,
    )
    if asset_locations is None:
        asset_locations = []
    if asset_names is None:
        asset_names = []

    asset_name_map = {
        int(item["item_id"]): str(item["name"])
        for item in asset_names
        if item.get("item_id") is not None and item.get("name") is not None
    }
    asset_position_map = {
        int(item["item_id"]): {
            "x": float(item.get("position", {}).get("x", 0)),
            "y": float(item.get("position", {}).get("y", 0)),
            "z": float(item.get("position", {}).get("z", 0)),
        }
        for item in asset_locations
        if item.get("item_id") is not None and isinstance(item.get("position"), dict)
    }

    await sync_character_assets(
        db=db,
        character_id=character_id,
        assets=entries,
        asset_names=asset_name_map,
        asset_positions=asset_position_map,
    )

    asset_by_item_id = {int(entry["item_id"]): entry for entry in entries if entry.get("item_id") is not None}
    paged_source_entries = _slice_page(entries, page, page_size)
    names_map = await esi_service.resolve_ids(db, _collect_asset_ids(paged_source_entries))
    enriched_entries: list[dict[str, Any]] = []
    for entry in paged_source_entries:
        enriched_entry = dict(entry)
        _attach_resolved_name(enriched_entry, names_map, "type_id", "type_name")
        location_id = enriched_entry.get("location_id")
        if isinstance(location_id, int):
            if location_id in asset_name_map:
                enriched_entry["location_name"] = asset_name_map[location_id]
            elif location_id in asset_by_item_id:
                parent = asset_by_item_id[location_id]
                enriched_entry["location_name"] = asset_name_map.get(location_id) or names_map.get(parent.get("type_id"), f"ID: {location_id}")
            else:
                _attach_resolved_name(enriched_entry, names_map, "location_id", "location_name")
        enriched_entry["name"] = asset_name_map.get(enriched_entry.get("item_id"))
        position = asset_position_map.get(enriched_entry.get("item_id"), {})
        enriched_entry["position_x"] = position.get("x")
        enriched_entry["position_y"] = position.get("y")
        enriched_entry["position_z"] = position.get("z")
        enriched_entries.append(enriched_entry)

    return {
        "user_id": user_id,
        "character_id": character_id,
        "character_name": character_name,
        "page": page,
        "page_size": page_size,
        "asset_count": len(entries),
        "total_count": len(entries),
        "summary": _build_asset_summary(entries),
        "assets": enriched_entries,
    }