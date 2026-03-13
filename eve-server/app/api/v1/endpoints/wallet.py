import asyncio
import logging
from typing import Any

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_character, get_current_user
from app.api.v1.schemas import WalletBalanceResponse, WalletJournalResponse, WalletTransactionsResponse
from app.core.config import settings
from app.crud.character_ops import (
    get_wallet_balance_cache,
    get_wallet_journal_cache,
    get_wallet_transactions_cache,
    sync_wallet_balance,
    sync_wallet_journal,
    sync_wallet_transactions,
)
from app.crud.user import get_character_with_valid_token
from app.core.errors import api_error
from app.database import AsyncSessionLocal, get_db
from app.models.operations import CharacterWalletJournalEntry, CharacterWalletTransaction
from app.models.user import Character, User
from app.schemas import ErrorResponse
from app.services.eve_esi import esi_service


router = APIRouter(prefix="/api/v1/wallet", tags=["Wallet"])
logger = logging.getLogger(__name__)
_wallet_refresh_inflight: set[tuple[str, int]] = set()
WALLET_CACHE_STATUS_HIT_FRESH = "hit_fresh"
WALLET_CACHE_STATUS_STALE_REFRESHING = "stale_refreshing"
WALLET_CACHE_STATUS_MISS_REFRESHED = "miss_refreshed"


def _collect_wallet_journal_ids(entries: list[dict[str, Any]]) -> list[int]:
    ids_to_resolve: set[int] = set()
    for entry in entries:
        for field in ("first_party_id", "second_party_id", "context_id"):
            value = entry.get(field)
            if isinstance(value, int) and value > 0:
                ids_to_resolve.add(value)
    return list(ids_to_resolve)


def _collect_wallet_transaction_ids(entries: list[dict[str, Any]]) -> list[int]:
    ids_to_resolve: set[int] = set()
    for entry in entries:
        for field in ("type_id", "location_id", "client_id"):
            value = entry.get(field)
            if isinstance(value, int) and value > 0:
                ids_to_resolve.add(value)
    return list(ids_to_resolve)


def _attach_resolved_name(payload: dict[str, Any], names_map: dict[int, str], source_field: str, target_field: str) -> None:
    value = payload.get(source_field)
    if isinstance(value, int):
        payload[target_field] = names_map.get(value, f"ID: {value}")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _is_cache_fresh(updated_at: datetime | None, ttl_seconds: int) -> bool:
    if updated_at is None:
        return False
    return (_utcnow() - updated_at).total_seconds() <= ttl_seconds


def _serialize_wallet_journal_entry(record: CharacterWalletJournalEntry) -> dict[str, Any]:
    return {
        "id": record.id,
        "date": record.date,
        "ref_type": record.ref_type,
        "amount": float(record.amount) if record.amount is not None else None,
        "balance": float(record.balance) if record.balance is not None else None,
        "reason": record.reason,
        "description": record.description,
        "first_party_id": record.first_party_id,
        "second_party_id": record.second_party_id,
        "context_id": record.context_id,
        "context_id_type": record.context_id_type,
        "tax": float(record.tax) if record.tax is not None else None,
        "tax_receiver_id": record.tax_receiver_id,
        "fetched_at": record.fetched_at,
    }


def _serialize_wallet_transaction_entry(record: CharacterWalletTransaction) -> dict[str, Any]:
    return {
        "transaction_id": record.transaction_id,
        "date": record.date,
        "type_id": record.type_id,
        "location_id": record.location_id,
        "client_id": record.client_id,
        "unit_price": float(record.unit_price) if record.unit_price is not None else None,
        "quantity": record.quantity,
        "is_buy": record.is_buy,
        "is_personal": record.is_personal,
        "journal_ref_id": record.journal_ref_id,
        "fetched_at": record.fetched_at,
    }


async def _sync_wallet_balance_from_esi(db: AsyncSession, character_id: int, access_token: str) -> bool:
    balance = await esi_service.get_character_wallet_balance(character_id=character_id, access_token=access_token)
    if balance is None:
        return False

    await sync_wallet_balance(db=db, character_id=character_id, balance=balance)
    return True


async def _sync_wallet_journal_from_esi(db: AsyncSession, character_id: int, access_token: str) -> bool:
    entries = await esi_service.get_character_wallet_journal(character_id=character_id, access_token=access_token)
    if entries is None:
        return False

    await sync_wallet_journal(db=db, character_id=character_id, entries=entries)
    return True


async def _sync_wallet_transactions_from_esi(db: AsyncSession, character_id: int, access_token: str) -> bool:
    entries = await esi_service.get_character_wallet_transactions(character_id=character_id, access_token=access_token)
    if entries is None:
        return False

    await sync_wallet_transactions(db=db, character_id=character_id, entries=entries)
    return True


async def _refresh_wallet_cache_for_character(db: AsyncSession, character_id: int, kind: str) -> bool:
    # 后台刷新和定时预热都走同一个入口，避免请求链路和后台逻辑分叉。
    character = await get_character_with_valid_token(db, character_id)
    if character is None or not character.access_token:
        return False

    if kind == "balance":
        return await _sync_wallet_balance_from_esi(db, character_id, character.access_token)
    if kind == "journal":
        return await _sync_wallet_journal_from_esi(db, character_id, character.access_token)
    if kind == "transactions":
        return await _sync_wallet_transactions_from_esi(db, character_id, character.access_token)

    raise ValueError(f"unsupported wallet refresh kind: {kind}")


def _schedule_wallet_refresh(kind: str, character_id: int) -> None:
    refresh_key = (kind, character_id)
    if refresh_key in _wallet_refresh_inflight:
        return

    async def _runner() -> None:
        try:
            async with AsyncSessionLocal() as session:
                await _refresh_wallet_cache_for_character(session, character_id, kind)
        except Exception:
            logger.exception("💥 [Wallet] 钱包后台刷新失败：类型=%s，角色 ID=%s", kind, character_id)
        finally:
            _wallet_refresh_inflight.discard(refresh_key)

    # 这里做去重是为了避免用户快速连点时重复打 ESI。
    _wallet_refresh_inflight.add(refresh_key)
    asyncio.create_task(_runner())


async def warm_wallet_cache_for_active_characters(batch_size: int | None = None) -> int:
    limit = batch_size or settings.WALLET_CACHE_WARMUP_BATCH_SIZE

    async with AsyncSessionLocal() as session:
        # 预热优先挑最近活跃、且用户仍处于激活状态的角色。
        result = await session.execute(
            select(Character.id)
            .join(User, Character.owner_id == User.id)
            .where(User.is_active.is_(True), Character.refresh_token.is_not(None))
            .order_by(User.last_login_at.desc().nullslast(), User.id.desc())
            .limit(limit)
        )
        character_ids = [int(character_id) for character_id in result.scalars().all()]

        refreshed_count = 0
        for character_id in character_ids:
            refreshed_any = False
            for kind in ("balance", "journal", "transactions"):
                try:
                    refreshed_any = await _refresh_wallet_cache_for_character(session, character_id, kind) or refreshed_any
                except Exception:
                    logger.exception("💥 [Wallet] 钱包缓存预热失败：角色 ID=%s，类型=%s", character_id, kind)

            if refreshed_any:
                refreshed_count += 1

        return refreshed_count


async def _build_wallet_journal_response(
    db: AsyncSession,
    *,
    user_id: int,
    character_id: int,
    character_name: str,
    page: int,
    page_size: int,
    cache_status: str,
) -> dict[str, Any]:
    cached_entries, total_count, income_total, expense_total, _ = await get_wallet_journal_cache(
        db=db,
        character_id=character_id,
        page=page,
        page_size=page_size,
    )
    serialized_entries = [_serialize_wallet_journal_entry(entry) for entry in cached_entries]
    names_map = await esi_service.resolve_ids(db, _collect_wallet_journal_ids(serialized_entries))

    enriched_entries: list[dict[str, Any]] = []
    for entry in serialized_entries:
        enriched_entry = dict(entry)
        _attach_resolved_name(enriched_entry, names_map, "first_party_id", "first_party_name")
        _attach_resolved_name(enriched_entry, names_map, "second_party_id", "second_party_name")
        _attach_resolved_name(enriched_entry, names_map, "context_id", "context_name")
        enriched_entries.append(enriched_entry)

    return {
        "user_id": user_id,
        "character_id": character_id,
        "character_name": character_name,
        "entry_count": len(enriched_entries),
        "page": page,
        "page_size": page_size,
        "total_count": total_count,
        "income_total": income_total,
        "expense_total": expense_total,
        "cache_status": cache_status,
        "entries": enriched_entries,
    }


async def _build_wallet_transactions_response(
    db: AsyncSession,
    *,
    user_id: int,
    character_id: int,
    character_name: str,
    page: int,
    page_size: int,
    cache_status: str,
) -> dict[str, Any]:
    cached_entries, total_count, buy_count, sell_count, _ = await get_wallet_transactions_cache(
        db=db,
        character_id=character_id,
        page=page,
        page_size=page_size,
    )
    serialized_entries = [_serialize_wallet_transaction_entry(entry) for entry in cached_entries]
    names_map = await esi_service.resolve_ids(db, _collect_wallet_transaction_ids(serialized_entries))

    enriched_entries: list[dict[str, Any]] = []
    for entry in serialized_entries:
        enriched_entry = dict(entry)
        _attach_resolved_name(enriched_entry, names_map, "type_id", "type_name")
        _attach_resolved_name(enriched_entry, names_map, "location_id", "location_name")
        enriched_entries.append(enriched_entry)

    return {
        "user_id": user_id,
        "character_id": character_id,
        "character_name": character_name,
        "transaction_count": len(enriched_entries),
        "page": page,
        "page_size": page_size,
        "total_count": total_count,
        "buy_count": buy_count,
        "sell_count": sell_count,
        "cache_status": cache_status,
        "transactions": enriched_entries,
    }


@router.get(
    "/balance",
    response_model=WalletBalanceResponse,
    summary="获取当前角色钱包余额",
    description="读取当前 JWT 绑定角色的钱包余额。",
    responses={
        401: {"description": "当前角色没有可用 ESI access_token，需要重新授权", "model": ErrorResponse},
        502: {"description": "EVE ESI 钱包接口调用失败", "model": ErrorResponse},
    },
)
async def read_wallet_balance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_character: Character = Depends(get_current_character),
):
    user_id = int(current_user.id)
    character_id = int(current_character.id)
    character_name = current_character.name
    access_token = current_character.access_token

    if not access_token:
        raise api_error(401, "character_token_missing", "当前角色缺少可用的 ESI 访问令牌，请重新授权")

    cached_balance = await get_wallet_balance_cache(db=db, character_id=character_id)
    if cached_balance is not None:
        # 命中新鲜缓存时直接返回；命中过期缓存时先返回旧值并异步刷新。
        cache_status = WALLET_CACHE_STATUS_HIT_FRESH
        if not _is_cache_fresh(cached_balance.updated_at, settings.WALLET_BALANCE_CACHE_TTL_SECONDS):
            cache_status = WALLET_CACHE_STATUS_STALE_REFRESHING
            _schedule_wallet_refresh("balance", character_id)

        return {
            "user_id": user_id,
            "character_id": character_id,
            "character_name": character_name,
            "balance": float(cached_balance.balance),
            "updated_at": cached_balance.updated_at,
            "cache_status": cache_status,
        }

    # 冷启动时没有任何缓存，只能同步拉一次 ESI 并落库。
    if not await _sync_wallet_balance_from_esi(db=db, character_id=character_id, access_token=access_token):
        raise api_error(502, "esi_upstream_failed", "EVE ESI 钱包余额接口调用失败，请稍后重试")

    cached_balance = await get_wallet_balance_cache(db=db, character_id=character_id)
    if cached_balance is None:
        raise api_error(502, "wallet_cache_missing", "钱包余额刷新成功，但缓存未写入，请稍后重试")

    return {
        "user_id": user_id,
        "character_id": character_id,
        "character_name": character_name,
        "balance": float(cached_balance.balance),
        "updated_at": cached_balance.updated_at,
        "cache_status": WALLET_CACHE_STATUS_MISS_REFRESHED,
    }


@router.get(
    "/journal",
    response_model=WalletJournalResponse,
    summary="获取当前角色钱包日记",
    description="读取当前 JWT 绑定角色的钱包日记列表，并补齐常见名称翻译字段。",
    responses={
        401: {"description": "当前角色没有可用 ESI access_token，需要重新授权", "model": ErrorResponse},
        502: {"description": "EVE ESI 钱包日记接口调用失败", "model": ErrorResponse},
    },
)
async def read_wallet_journal(
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

    cached_entries, total_count, _, _, latest_fetched_at = await get_wallet_journal_cache(
        db=db,
        character_id=character_id,
        page=page,
        page_size=page_size,
    )
    if total_count > 0:
        cache_status = WALLET_CACHE_STATUS_HIT_FRESH
        if not _is_cache_fresh(latest_fetched_at, settings.WALLET_JOURNAL_CACHE_TTL_SECONDS):
            cache_status = WALLET_CACHE_STATUS_STALE_REFRESHING
            _schedule_wallet_refresh("journal", character_id)

        return await _build_wallet_journal_response(
            db=db,
            user_id=user_id,
            character_id=character_id,
            character_name=character_name,
            page=page,
            page_size=page_size,
            cache_status=cache_status,
        )

    if not await _sync_wallet_journal_from_esi(db=db, character_id=character_id, access_token=access_token):
        raise api_error(502, "esi_upstream_failed", "EVE ESI 钱包日记接口调用失败，请稍后重试")

    return await _build_wallet_journal_response(
        db=db,
        user_id=user_id,
        character_id=character_id,
        character_name=character_name,
        page=page,
        page_size=page_size,
        cache_status=WALLET_CACHE_STATUS_MISS_REFRESHED,
    )


@router.get(
    "/transactions",
    response_model=WalletTransactionsResponse,
    summary="获取当前角色市场交易记录",
    description="读取当前 JWT 绑定角色的市场交易记录，并补齐物品与地点名称。",
    responses={
        401: {"description": "当前角色没有可用 ESI access_token，需要重新授权", "model": ErrorResponse},
        502: {"description": "EVE ESI 市场交易接口调用失败", "model": ErrorResponse},
    },
)
async def read_wallet_transactions(
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

    _, total_count, _, _, latest_fetched_at = await get_wallet_transactions_cache(
        db=db,
        character_id=character_id,
        page=page,
        page_size=page_size,
    )
    if total_count > 0:
        cache_status = WALLET_CACHE_STATUS_HIT_FRESH
        if not _is_cache_fresh(latest_fetched_at, settings.WALLET_TRANSACTIONS_CACHE_TTL_SECONDS):
            cache_status = WALLET_CACHE_STATUS_STALE_REFRESHING
            _schedule_wallet_refresh("transactions", character_id)

        return await _build_wallet_transactions_response(
            db=db,
            user_id=user_id,
            character_id=character_id,
            character_name=character_name,
            page=page,
            page_size=page_size,
            cache_status=cache_status,
        )

    if not await _sync_wallet_transactions_from_esi(db=db, character_id=character_id, access_token=access_token):
        raise api_error(502, "esi_upstream_failed", "EVE ESI 市场交易接口调用失败，请稍后重试")

    return await _build_wallet_transactions_response(
        db=db,
        user_id=user_id,
        character_id=character_id,
        character_name=character_name,
        page=page,
        page_size=page_size,
        cache_status=WALLET_CACHE_STATUS_MISS_REFRESHED,
    )