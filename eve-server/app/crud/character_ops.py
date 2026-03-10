from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import case, delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.operations import CharacterAsset, CharacterWalletBalance, CharacterWalletJournalEntry, CharacterWalletTransaction


def _to_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _to_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


async def sync_wallet_balance(db: AsyncSession, character_id: int, balance: float) -> None:
    record = await db.get(CharacterWalletBalance, character_id)
    if record is None:
        db.add(CharacterWalletBalance(character_id=character_id, balance=_to_decimal(balance) or Decimal("0")))
    else:
        record.balance = _to_decimal(balance) or Decimal("0")
        record.updated_at = datetime.now(timezone.utc)
    await db.commit()


async def get_wallet_balance_cache(db: AsyncSession, character_id: int) -> CharacterWalletBalance | None:
    return await db.get(CharacterWalletBalance, character_id)


async def sync_wallet_journal(db: AsyncSession, character_id: int, entries: list[dict[str, Any]]) -> None:
    entry_ids = [int(entry["id"]) for entry in entries if entry.get("id") is not None]
    existing = await db.execute(
        select(CharacterWalletJournalEntry).where(CharacterWalletJournalEntry.id.in_(entry_ids))
    )
    existing_map = {row.id: row for row in existing.scalars().all()}

    for entry in entries:
        entry_id = int(entry["id"])
        record = existing_map.get(entry_id)
        payload = {
            "character_id": character_id,
            "amount": _to_decimal(entry.get("amount")),
            "balance": _to_decimal(entry.get("balance")),
            "context_id": entry.get("context_id"),
            "context_id_type": entry.get("context_id_type"),
            "date": _to_datetime(entry.get("date")) or datetime.now(timezone.utc),
            "description": entry.get("description") or "",
            "first_party_id": entry.get("first_party_id"),
            "reason": entry.get("reason"),
            "ref_type": entry.get("ref_type") or "unknown",
            "second_party_id": entry.get("second_party_id"),
            "tax": _to_decimal(entry.get("tax")),
            "tax_receiver_id": entry.get("tax_receiver_id"),
            "fetched_at": datetime.now(timezone.utc),
        }

        if record is None:
            db.add(CharacterWalletJournalEntry(id=entry_id, **payload))
        else:
            for key, value in payload.items():
                setattr(record, key, value)

    await db.commit()


async def get_wallet_journal_cache(
    db: AsyncSession,
    character_id: int,
    page: int,
    page_size: int,
) -> tuple[list[CharacterWalletJournalEntry], int, float, float, datetime | None]:
    summary_result = await db.execute(
        select(
            func.count(CharacterWalletJournalEntry.id),
            func.coalesce(
                func.sum(
                    case(
                        (CharacterWalletJournalEntry.amount > 0, CharacterWalletJournalEntry.amount),
                        else_=0,
                    )
                ),
                0,
            ),
            func.coalesce(
                func.sum(
                    case(
                        (CharacterWalletJournalEntry.amount < 0, -CharacterWalletJournalEntry.amount),
                        else_=0,
                    )
                ),
                0,
            ),
            func.max(CharacterWalletJournalEntry.fetched_at),
        ).where(CharacterWalletJournalEntry.character_id == character_id)
    )
    total_count, income_total, expense_total, latest_fetched_at = summary_result.one()

    entries_result = await db.execute(
        select(CharacterWalletJournalEntry)
        .where(CharacterWalletJournalEntry.character_id == character_id)
        .order_by(desc(CharacterWalletJournalEntry.date), desc(CharacterWalletJournalEntry.id))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    return (
        entries_result.scalars().all(),
        int(total_count or 0),
        float(income_total or 0),
        float(expense_total or 0),
        latest_fetched_at,
    )


async def sync_wallet_transactions(db: AsyncSession, character_id: int, entries: list[dict[str, Any]]) -> None:
    transaction_ids = [int(entry["transaction_id"]) for entry in entries if entry.get("transaction_id") is not None]
    existing = await db.execute(
        select(CharacterWalletTransaction).where(CharacterWalletTransaction.transaction_id.in_(transaction_ids))
    )
    existing_map = {row.transaction_id: row for row in existing.scalars().all()}

    for entry in entries:
        transaction_id = int(entry["transaction_id"])
        payload = {
            "character_id": character_id,
            "client_id": int(entry.get("client_id") or 0),
            "date": _to_datetime(entry.get("date")) or datetime.now(timezone.utc),
            "is_buy": bool(entry.get("is_buy")),
            "is_personal": bool(entry.get("is_personal")),
            "journal_ref_id": int(entry.get("journal_ref_id") or 0),
            "location_id": int(entry.get("location_id") or 0),
            "quantity": int(entry.get("quantity") or 0),
            "type_id": int(entry.get("type_id") or 0),
            "unit_price": _to_decimal(entry.get("unit_price")) or Decimal("0"),
            "fetched_at": datetime.now(timezone.utc),
        }

        record = existing_map.get(transaction_id)
        if record is None:
            db.add(CharacterWalletTransaction(transaction_id=transaction_id, **payload))
        else:
            for key, value in payload.items():
                setattr(record, key, value)

    await db.commit()


async def get_wallet_transactions_cache(
    db: AsyncSession,
    character_id: int,
    page: int,
    page_size: int,
) -> tuple[list[CharacterWalletTransaction], int, int, int, datetime | None]:
    summary_result = await db.execute(
        select(
            func.count(CharacterWalletTransaction.transaction_id),
            func.coalesce(
                func.sum(case((CharacterWalletTransaction.is_buy.is_(True), 1), else_=0)),
                0,
            ),
            func.coalesce(
                func.sum(case((CharacterWalletTransaction.is_buy.is_(False), 1), else_=0)),
                0,
            ),
            func.max(CharacterWalletTransaction.fetched_at),
        ).where(CharacterWalletTransaction.character_id == character_id)
    )
    total_count, buy_count, sell_count, latest_fetched_at = summary_result.one()

    entries_result = await db.execute(
        select(CharacterWalletTransaction)
        .where(CharacterWalletTransaction.character_id == character_id)
        .order_by(desc(CharacterWalletTransaction.date), desc(CharacterWalletTransaction.transaction_id))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    return (
        entries_result.scalars().all(),
        int(total_count or 0),
        int(buy_count or 0),
        int(sell_count or 0),
        latest_fetched_at,
    )


async def sync_character_assets(
    db: AsyncSession,
    character_id: int,
    assets: list[dict[str, Any]],
    asset_names: dict[int, str],
    asset_positions: dict[int, dict[str, float]],
) -> None:
    item_ids = [int(asset["item_id"]) for asset in assets if asset.get("item_id") is not None]
    existing = await db.execute(select(CharacterAsset).where(CharacterAsset.item_id.in_(item_ids)))
    existing_map = {row.item_id: row for row in existing.scalars().all()}
    now = datetime.now(timezone.utc)

    for asset in assets:
        item_id = int(asset["item_id"])
        position = asset_positions.get(item_id, {})
        payload = {
            "character_id": character_id,
            "type_id": int(asset.get("type_id") or 0),
            "is_blueprint_copy": asset.get("is_blueprint_copy"),
            "is_singleton": bool(asset.get("is_singleton")),
            "location_flag": asset.get("location_flag") or "Unknown",
            "location_id": int(asset.get("location_id") or 0),
            "location_type": asset.get("location_type") or "other",
            "quantity": int(asset.get("quantity") or 0),
            "name": asset_names.get(item_id),
            "position_x": position.get("x"),
            "position_y": position.get("y"),
            "position_z": position.get("z"),
            "fetched_at": now,
            "updated_at": now,
        }

        record = existing_map.get(item_id)
        if record is None:
            db.add(CharacterAsset(item_id=item_id, **payload))
        else:
            for key, value in payload.items():
                setattr(record, key, value)

    if item_ids:
        await db.execute(
            delete(CharacterAsset).where(
                CharacterAsset.character_id == character_id,
                CharacterAsset.item_id.not_in(item_ids),
            )
        )
    else:
        await db.execute(delete(CharacterAsset).where(CharacterAsset.character_id == character_id))

    await db.commit()