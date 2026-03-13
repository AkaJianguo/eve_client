import logging
from datetime import datetime, timedelta
from decimal import Decimal
from time import perf_counter
from typing import Any

import httpx
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from asyncache import cached
    from cachetools import TTLCache
except ImportError:
    cached = None
    TTLCache = None

from app.api.v1.schemas import MarketHistoryItem, MarketOrder
from app.core.config import settings
from app.core.errors import api_error
from app.database import get_db
from app.models.market import MarketHistory
from app.schemas import ErrorResponse
from app.services.eve_esi import esi_service
from app.services.eve_esi import ESI_USER_AGENT


router = APIRouter(prefix="/api/v1/market", tags=["Market"])
logger = logging.getLogger(__name__)

LIVE_MARKET_ORDERS_CACHE_TTL_SECONDS = 300
LIVE_MARKET_ORDERS_CACHE_MAXSIZE = 1000
LIVE_MARKET_ORDER_TIMEOUT_SECONDS = 20
GLOBAL_MARKET_REGION_ID = 19000001
GLOBAL_MARKET_ITEMS = {44992}

if cached is not None and TTLCache is not None:
    live_market_orders_cache = TTLCache(maxsize=LIVE_MARKET_ORDERS_CACHE_MAXSIZE, ttl=LIVE_MARKET_ORDERS_CACHE_TTL_SECONDS)

    @cached(cache=live_market_orders_cache)
    async def fetch_live_orders_from_esi(region_id: int, type_id: int) -> list[dict[str, Any]]:
        url = f"{esi_service.base_url}/markets/{region_id}/orders/"
        params = {
            "datasource": "tranquility",
            "order_type": "all",
            "type_id": type_id,
        }
        async with httpx.AsyncClient(timeout=LIVE_MARKET_ORDER_TIMEOUT_SECONDS, headers={"User-Agent": ESI_USER_AGENT}) as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            if response.status_code == 404:
                return []
            response.raise_for_status()
else:
    live_market_orders_cache = None

    async def fetch_live_orders_from_esi(region_id: int, type_id: int) -> list[dict[str, Any]]:
        raise RuntimeError("缺少 cachetools/asyncache 依赖，请先执行 pip install cachetools asyncache")


def _coerce_decimal(value: float | int | str | Decimal) -> Decimal:
    return Decimal(str(value))


@router.get(
    "/history/{type_id}",
    response_model=list[MarketHistoryItem],
    summary="获取吉他市场历史数据",
    description="按需读取指定物品在指定区域的市场历史。优先读取本地缓存，缓存缺失或过期时再回源 ESI 并批量入库。",
    responses={
        200: {"description": "成功返回市场历史数据"},
        502: {"description": "ESI 市场历史接口调用失败且本地无可用缓存", "model": ErrorResponse},
    },
)
async def get_market_history(
    type_id: int,
    region_id: int = Query(settings.MARKET_HISTORY_DEFAULT_REGION_ID, ge=1),
    db: AsyncSession = Depends(get_db),
):
    latest_stmt = select(func.max(MarketHistory.date)).where(
        MarketHistory.type_id == type_id,
        MarketHistory.region_id == region_id,
    )
    latest_result = await db.execute(latest_stmt)
    latest_date = latest_result.scalar_one_or_none()

    today = datetime.utcnow().date()
    has_local_cache = latest_date is not None
    needs_update = latest_date is None or latest_date < (today - timedelta(days=settings.MARKET_HISTORY_STALE_AFTER_DAYS))

    if needs_update:
        try:
            esi_data = await esi_service.get_market_history(type_id=type_id, region_id=region_id)
            if esi_data:
                insert_values = [
                    {
                        "type_id": type_id,
                        "region_id": region_id,
                        "date": datetime.strptime(item["date"], "%Y-%m-%d").date(),
                        "average": _coerce_decimal(item["average"]),
                        "highest": _coerce_decimal(item["highest"]),
                        "lowest": _coerce_decimal(item["lowest"]),
                        "volume": int(item["volume"]),
                        "order_count": int(item["order_count"]),
                    }
                    for item in esi_data
                ]

                insert_stmt = insert(MarketHistory).values(insert_values)
                on_conflict_stmt = insert_stmt.on_conflict_do_nothing(
                    index_elements=["type_id", "region_id", "date"],
                )
                await db.execute(on_conflict_stmt)
                await db.commit()
        except httpx.HTTPError as exc:
            logger.warning(
                "⚠️ [Market] ESI 市场历史拉取失败：物品 ID=%s，星域 ID=%s，错误=%s",
                type_id,
                region_id,
                exc,
            )
            await db.rollback()
            if not has_local_cache:
                raise api_error(502, "esi_upstream_failed", "市场历史数据拉取失败，且本地暂无可用缓存")
        except Exception:
            logger.exception(
                "💥 [Market] 市场历史同步发生未预期异常：物品 ID=%s，星域 ID=%s",
                type_id,
                region_id,
            )
            await db.rollback()
            if not has_local_cache:
                raise api_error(502, "market_history_sync_failed", "市场历史数据同步失败，且本地暂无可用缓存")

    query_stmt = select(MarketHistory).where(
        MarketHistory.type_id == type_id,
        MarketHistory.region_id == region_id,
    ).order_by(MarketHistory.date.asc())
    records = await db.execute(query_stmt)
    return records.scalars().all()


@router.get(
    "/orders/{type_id}",
    response_model=list[MarketOrder],
    summary="获取指定物品的实时市场订单",
    description="透传 ESI 市场订单接口，并使用 5 分钟 TTL 的 Python 内存缓存减轻上游请求压力。",
    responses={
        200: {"description": "成功返回指定星域的市场订单"},
        500: {"description": "服务端缺少依赖或内部处理失败", "model": ErrorResponse},
        502: {"description": "ESI 上游接口调用失败", "model": ErrorResponse},
    },
)
async def get_live_market_orders(
    type_id: int,
    region_id: int = Query(10000002, ge=1, description="星域 ID，默认吉他。"),
    db: AsyncSession = Depends(get_db),
):
    start_time = perf_counter()
    order_count = 0

    try:
        if type_id in GLOBAL_MARKET_ITEMS and region_id != GLOBAL_MARKET_REGION_ID:
            logger.info(
                "💎 [Market] 检测到全局市场物品：物品 ID=%s，请求星域=%s，已自动切换到星域=%s",
                type_id,
                region_id,
                GLOBAL_MARKET_REGION_ID,
            )
            region_id = GLOBAL_MARKET_REGION_ID

        logger.info("🚀 [Market] 开始查询市场订单：物品 ID=%s，星域 ID=%s", type_id, region_id)
        raw_orders = await fetch_live_orders_from_esi(region_id=region_id, type_id=type_id)
        logger.info("📡 [Market] ESI 市场订单返回完成：物品 ID=%s，星域 ID=%s，原始订单数=%s", type_id, region_id, len(raw_orders))
        if not raw_orders:
            logger.info(
            "📭 [Market] 市场订单查询完成：物品 ID=%s，星域 ID=%s，结果为空，耗时=%.2fms",
                type_id,
                region_id,
                (perf_counter() - start_time) * 1000,
            )
            return []

        unique_ids: set[int] = set()
        for order in raw_orders:
            location_id = order.get("location_id")
            system_id = order.get("system_id")
            if isinstance(location_id, int):
                unique_ids.add(location_id)
            if isinstance(system_id, int):
                unique_ids.add(system_id)

        logger.info("🧭 [Market] 开始通过通用名称解析服务翻译订单 ID：待解析数量=%s", len(unique_ids))
        names_mapping = await esi_service.resolve_ids(db, list(unique_ids))
        logger.info("🧭 [Market] 通用名称解析完成：成功解析数量=%s", len(names_mapping))

        processed_orders: list[dict[str, Any]] = []
        for order in raw_orders:
            location_id = int(order["location_id"])
            system_id = int(order["system_id"])
            default_location_name = "玩家星堡 (Citadel)" if location_id > 1_000_000_000_000 else f"未知空间站 ({location_id})"

            enriched_order = dict(order)
            enriched_order["location_name"] = names_mapping.get(location_id, default_location_name)
            enriched_order["system_name"] = names_mapping.get(system_id, f"未知星系 ({system_id})")
            processed_orders.append(enriched_order)

        buy_orders = sorted((order for order in processed_orders if order.get("is_buy_order")), key=lambda order: order["price"], reverse=True)
        sell_orders = sorted((order for order in processed_orders if not order.get("is_buy_order")), key=lambda order: order["price"])

        sorted_orders = sell_orders + buy_orders
        order_count = len(sorted_orders)

        logger.info(
            "✅ [Market] 市场订单查询完成：物品 ID=%s，星域 ID=%s，订单数=%s，耗时=%.2fms",
            type_id,
            region_id,
            order_count,
            (perf_counter() - start_time) * 1000,
        )

        return [
            {
                "order_id": int(order["order_id"]),
                "is_buy_order": bool(order["is_buy_order"]),
                "price": float(order["price"]),
                "volume_remain": int(order["volume_remain"]),
                "location_id": int(order["location_id"]),
                "system_id": int(order["system_id"]),
                "location_name": str(order.get("location_name") or "未知建筑"),
                "system_name": str(order.get("system_name") or "未知星系"),
            }
            for order in sorted_orders
        ]
    except RuntimeError as exc:
        logger.warning(
            "⚠️ [Market] 市场订单查询失败：物品 ID=%s，星域 ID=%s，订单数=%s，耗时=%.2fms，错误=%s",
            type_id,
            region_id,
            order_count,
            (perf_counter() - start_time) * 1000,
            exc,
        )
        raise api_error(500, "market_orders_dependency_missing", str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "⚠️ [Market] ESI 市场订单请求失败：物品 ID=%s，星域 ID=%s，订单数=%s，耗时=%.2fms，状态码=%s",
            type_id,
            region_id,
            order_count,
            (perf_counter() - start_time) * 1000,
            exc.response.status_code,
        )
        raise api_error(502, "esi_upstream_failed", f"ESI 节点通讯异常: {exc}") from exc
    except httpx.HTTPError as exc:
        logger.warning(
            "⚠️ [Market] ESI 市场订单通信失败：物品 ID=%s，星域 ID=%s，订单数=%s，耗时=%.2fms，错误=%s",
            type_id,
            region_id,
            order_count,
            (perf_counter() - start_time) * 1000,
            exc,
        )
        raise api_error(502, "esi_transport_failed", "ESI 市场订单接口通讯失败") from exc
    except Exception as exc:
        logger.exception(
            "💥 [Market] 市场订单查询发生未预期异常：物品 ID=%s，星域 ID=%s，订单数=%s，耗时=%.2fms",
            type_id,
            region_id,
            order_count,
            (perf_counter() - start_time) * 1000,
        )
        raise api_error(500, "market_orders_internal_error", "服务器内部处理错误") from exc