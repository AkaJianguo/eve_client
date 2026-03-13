from __future__ import annotations

import logging
from collections.abc import MutableMapping
from typing import Any

import aiohttp
import httpx
from cachetools import TTLCache
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.universe import UniverseName


logger = logging.getLogger(__name__)

ESI_USER_AGENT = "WangJianGuo-EVE-ESI/1.0"
MAX_UNIVERSE_NAME_ID = 2_147_483_647
UNIVERSAL_NAMES_VIEW = "sde.vw_universal_names"
L1_NAME_CACHE_MAXSIZE = 50_000
L1_NAME_CACHE_TTL_SECONDS = 86_400

l1_name_cache: MutableMapping[int, str] = TTLCache(maxsize=L1_NAME_CACHE_MAXSIZE, ttl=L1_NAME_CACHE_TTL_SECONDS)


class EveESIService:
    def __init__(self) -> None:
        self.base_url = "https://esi.evetech.net/latest"
        self._session: aiohttp.ClientSession | None = None

    def _build_session(self) -> aiohttp.ClientSession:
        return aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=20),
            headers={"User-Agent": ESI_USER_AGENT},
        )

    def get_session(self) -> aiohttp.ClientSession:
        """Get a reusable HTTP session, creating a fallback session if needed."""
        if self._session is None or self._session.closed:
            logger.warning("⚠️ [ESI] 服务会话未在应用生命周期中初始化，正在创建兜底会话")
            self._session = self._build_session()
        return self._session

    async def start(self) -> None:
        if self._session is None or self._session.closed:
            self._session = self._build_session()
            logger.info("🛰️ [ESI] 服务会话已启动")

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()
            logger.info("🛑 [ESI] 服务会话已关闭")

    async def get_character_public_info(self, character_id: int) -> dict[str, Any] | None:
        """Fetch public character profile data from ESI."""
        url = f"{self.base_url}/characters/{character_id}/"
        params = {"datasource": "tranquility"}
        session = self.get_session()

        try:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    body = await response.text()
                    logger.warning(
                        "⚠️ [ESI] 角色公开信息查询失败：角色 ID=%s，状态码=%s，响应体=%s",
                        character_id,
                        response.status,
                        body,
                    )
                    return None
                return await response.json()
        except aiohttp.ClientError as exc:
            logger.warning("⚠️ [ESI] 角色公开信息请求失败：角色 ID=%s，错误=%s", character_id, exc)
            return None

    async def get_character_industry_jobs(
        self,
        character_id: int,
        access_token: str,
        include_completed: bool = True,
    ) -> list[dict[str, Any]] | None:
        """Fetch authenticated character industry jobs from ESI."""
        url = f"{self.base_url}/characters/{character_id}/industry/jobs/"
        params = {
            "datasource": "tranquility",
            "include_completed": str(include_completed).lower(),
        }
        headers = {"Authorization": f"Bearer {access_token}"}
        session = self.get_session()

        try:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status != 200:
                    body = await response.text()
                    logger.warning(
                        "⚠️ [ESI] 工业任务查询失败：角色 ID=%s，状态码=%s，响应体=%s",
                        character_id,
                        response.status,
                        body,
                    )
                    return None
                return await response.json()
        except aiohttp.ClientError as exc:
            logger.warning(
                "⚠️ [ESI] 工业任务请求失败：角色 ID=%s，错误=%s",
                character_id,
                exc,
            )
            return None

    async def get_character_wallet_balance(
        self,
        character_id: int,
        access_token: str,
    ) -> float | None:
        url = f"{self.base_url}/characters/{character_id}/wallet/"
        params = {"datasource": "tranquility"}
        headers = {"Authorization": f"Bearer {access_token}"}
        session = self.get_session()

        try:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status != 200:
                    body = await response.text()
                    logger.warning(
                        "⚠️ [ESI] 钱包余额查询失败：角色 ID=%s，状态码=%s，响应体=%s",
                        character_id,
                        response.status,
                        body,
                    )
                    return None
                payload = await response.json()
                return float(payload)
        except (aiohttp.ClientError, TypeError, ValueError) as exc:
            logger.warning("⚠️ [ESI] 钱包余额请求失败：角色 ID=%s，错误=%s", character_id, exc)
            return None

    async def get_character_wallet_journal(
        self,
        character_id: int,
        access_token: str,
    ) -> list[dict[str, Any]] | None:
        return await self._fetch_paginated_character_endpoint(
            character_id=character_id,
            access_token=access_token,
            path="wallet/journal/",
            log_key="wallet journal",
        )

    async def get_character_wallet_transactions(
        self,
        character_id: int,
        access_token: str,
    ) -> list[dict[str, Any]] | None:
        url = f"{self.base_url}/characters/{character_id}/wallet/transactions/"
        params = {"datasource": "tranquility"}
        headers = {"Authorization": f"Bearer {access_token}"}
        session = self.get_session()

        try:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status != 200:
                    body = await response.text()
                    logger.warning(
                        "⚠️ [ESI] 钱包交易查询失败：角色 ID=%s，状态码=%s，响应体=%s",
                        character_id,
                        response.status,
                        body,
                    )
                    return None
                payload = await response.json()
                return payload if isinstance(payload, list) else None
        except aiohttp.ClientError as exc:
            logger.warning("⚠️ [ESI] 钱包交易请求失败：角色 ID=%s，错误=%s", character_id, exc)
            return None

    async def get_character_assets(
        self,
        character_id: int,
        access_token: str,
    ) -> list[dict[str, Any]] | None:
        return await self._fetch_paginated_character_endpoint(
            character_id=character_id,
            access_token=access_token,
            path="assets/",
            log_key="assets",
        )

    async def get_market_history(
        self,
        type_id: int,
        region_id: int = 10000002,
    ) -> list[dict[str, Any]]:
        url = f"{self.base_url}/markets/{region_id}/history/"
        params = {
            "datasource": "tranquility",
            "type_id": type_id,
        }

        try:
            async with httpx.AsyncClient(timeout=20, headers={"User-Agent": ESI_USER_AGENT}) as client:
                response = await client.get(url, params=params)
        except httpx.HTTPError as exc:
            logger.warning(
                "⚠️ [ESI] 市场历史请求失败：物品 ID=%s，星域 ID=%s，错误=%s",
                type_id,
                region_id,
                exc,
            )
            raise

        if response.status_code == 200:
            payload = response.json()
            return payload if isinstance(payload, list) else []

        if response.status_code == 404:
            return []

        logger.warning(
            "⚠️ [ESI] 市场历史查询失败：物品 ID=%s，星域 ID=%s，状态码=%s，响应体=%s",
            type_id,
            region_id,
            response.status_code,
            response.text,
        )
        response.raise_for_status()

    async def get_character_asset_locations(
        self,
        character_id: int,
        access_token: str,
        item_ids: list[int],
    ) -> list[dict[str, Any]] | None:
        return await self._post_character_batch_endpoint(
            character_id=character_id,
            access_token=access_token,
            path="assets/locations/",
            item_ids=item_ids,
            log_key="asset locations",
        )

    async def get_character_asset_names(
        self,
        character_id: int,
        access_token: str,
        item_ids: list[int],
    ) -> list[dict[str, Any]] | None:
        return await self._post_character_batch_endpoint(
            character_id=character_id,
            access_token=access_token,
            path="assets/names/",
            item_ids=item_ids,
            log_key="asset names",
        )

    async def _fetch_paginated_character_endpoint(
        self,
        character_id: int,
        access_token: str,
        path: str,
        log_key: str,
    ) -> list[dict[str, Any]] | None:
        headers = {"Authorization": f"Bearer {access_token}"}
        session = self.get_session()
        page = 1
        total_pages = 1
        aggregated: list[dict[str, Any]] = []

        try:
            while page <= total_pages:
                url = f"{self.base_url}/characters/{character_id}/{path}"
                params = {"datasource": "tranquility", "page": page}

                async with session.get(url, params=params, headers=headers) as response:
                    if response.status != 200:
                        body = await response.text()
                        logger.warning(
                            "⚠️ [ESI] %s 查询失败：角色 ID=%s，页码=%s，状态码=%s，响应体=%s",
                            log_key,
                            character_id,
                            page,
                            response.status,
                            body,
                        )
                        return None

                    payload = await response.json()
                    if not isinstance(payload, list):
                        logger.warning(
                            "⚠️ [ESI] %s 返回了异常数据结构：角色 ID=%s，页码=%s，数据类型=%s",
                            log_key,
                            character_id,
                            page,
                            type(payload).__name__,
                        )
                        return None

                    aggregated.extend(payload)
                    total_pages = int(response.headers.get("X-Pages", total_pages))
                    page += 1
        except (aiohttp.ClientError, ValueError) as exc:
            logger.warning("⚠️ [ESI] %s 请求失败：角色 ID=%s，错误=%s", log_key, character_id, exc)
            return None

        return aggregated

    async def _post_character_batch_endpoint(
        self,
        character_id: int,
        access_token: str,
        path: str,
        item_ids: list[int],
        log_key: str,
    ) -> list[dict[str, Any]] | None:
        if not item_ids:
            return []

        headers = {"Authorization": f"Bearer {access_token}"}
        session = self.get_session()
        aggregated: list[dict[str, Any]] = []

        try:
            for start in range(0, len(item_ids), 1000):
                chunk = item_ids[start:start + 1000]
                url = f"{self.base_url}/characters/{character_id}/{path}"
                params = {"datasource": "tranquility"}

                async with session.post(url, params=params, headers=headers, json=chunk) as response:
                    if response.status != 200:
                        body = await response.text()
                        logger.warning(
                            "⚠️ [ESI] %s 查询失败：角色 ID=%s，分片起点=%s，状态码=%s，响应体=%s",
                            log_key,
                            character_id,
                            start,
                            response.status,
                            body,
                        )
                        return None

                    payload = await response.json()
                    if not isinstance(payload, list):
                        logger.warning(
                            "⚠️ [ESI] %s 返回了异常数据结构：角色 ID=%s，数据类型=%s",
                            log_key,
                            character_id,
                            type(payload).__name__,
                        )
                        return None

                    aggregated.extend(payload)
        except aiohttp.ClientError as exc:
            logger.warning("⚠️ [ESI] %s 请求失败：角色 ID=%s，错误=%s", log_key, character_id, exc)
            return None

        return aggregated

    async def resolve_ids(self, db: AsyncSession, ids: list[int]) -> dict[int, str]:
        """Resolve EVE IDs via universal SDE view, local cache, then ESI fallback."""
        if not ids:
            return {}

        pending_ids = {item_id for item_id in dict.fromkeys(ids) if 0 < item_id <= MAX_UNIVERSE_NAME_ID}
        resolved: dict[int, str] = {}
        total_ids = len(pending_ids)

        if not pending_ids:
            return resolved

        l1_hits = self._resolve_from_l1(pending_ids, resolved)
        if not pending_ids:
            logger.info("🧠 [ESI] 名称解析完成：总数=%s，L1 命中=%s，L2 视图命中=0，L2 缓存命中=0，L3 ESI 命中=0", total_ids, l1_hits)
            return resolved

        before_sde = len(pending_ids)
        await self._resolve_from_sde(db, pending_ids, resolved)
        sde_hits = before_sde - len(pending_ids)

        before_cache = len(pending_ids)
        await self._resolve_from_cache(db, pending_ids, resolved)
        cache_hits = before_cache - len(pending_ids)

        before_esi = len(pending_ids)
        await self._resolve_from_esi(db, pending_ids, resolved)
        esi_hits = before_esi - len(pending_ids)

        logger.info(
            "🧠 [ESI] 名称解析完成：总数=%s，L1 命中=%s，L2 视图命中=%s，L2 缓存命中=%s，L3 ESI 命中=%s，未解析=%s",
            total_ids,
            l1_hits,
            sde_hits,
            cache_hits,
            esi_hits,
            len(pending_ids),
        )

        return resolved

    def _resolve_from_l1(self, pending_ids: set[int], resolved: dict[int, str]) -> int:
        if not pending_ids:
            return 0

        resolved_ids: list[int] = []
        for item_id in pending_ids:
            cached_name = l1_name_cache.get(item_id)
            if cached_name:
                resolved[item_id] = cached_name
                resolved_ids.append(item_id)

        for item_id in resolved_ids:
            pending_ids.discard(item_id)

        if resolved_ids:
            logger.info("⚡ [ESI] L1 内存缓存命中：命中数量=%s", len(resolved_ids))

        return len(resolved_ids)

    async def _resolve_from_sde(
        self,
        db: AsyncSession,
        pending_ids: set[int],
        resolved: dict[int, str],
    ) -> None:
        if not pending_ids:
            return

        id_list_str = ",".join(map(str, sorted(pending_ids)))

        try:
            names_query = text(
                f"SELECT id, name, category FROM {UNIVERSAL_NAMES_VIEW} WHERE id IN ({id_list_str})"
            )
            names_result = await db.execute(names_query)
            for row in names_result.mappings():
                entity_id = int(row["id"])
                entity_name = str(row["name"])
                resolved[entity_id] = entity_name
                l1_name_cache[entity_id] = entity_name
                pending_ids.discard(entity_id)
        except Exception as exc:
            logger.warning("⚠️ [ESI] 通用名称视图查询失败：视图=%s，错误=%s", UNIVERSAL_NAMES_VIEW, exc)
            await db.rollback()  # 👈 回滚中止的事务

    async def _resolve_from_cache(
        self,
        db: AsyncSession,
        pending_ids: set[int],
        resolved: dict[int, str],
    ) -> None:
        if not pending_ids:
            return

        try:
            result = await db.execute(select(UniverseName).where(UniverseName.id.in_(pending_ids)))
            for record in result.scalars().all():
                resolved[record.id] = record.name
                l1_name_cache[record.id] = record.name
                pending_ids.discard(record.id)
        except Exception as exc:
            logger.warning("⚠️ [ESI] 本地宇宙名称缓存查询失败：错误=%s", exc)
            await db.rollback()  # 👈 回滚中止的事务

    async def _resolve_from_esi(
        self,
        db: AsyncSession,
        pending_ids: set[int],
        resolved: dict[int, str],
    ) -> None:
        if not pending_ids:
            return

        url = f"{self.base_url}/universe/names/"
        params = {"datasource": "tranquility"}
        request_ids = sorted(pending_ids)
        session = self.get_session()

        try:
            async with session.post(url, params=params, json=request_ids) as response:
                if response.status != 200:
                    body = await response.text()
                    logger.warning(
                        "⚠️ [ESI] 宇宙名称查询失败：状态码=%s，响应体=%s",
                        response.status,
                        body,
                    )
                    return

                esi_data = await response.json()
                returned_ids = [int(item["id"]) for item in esi_data]
                
                try:
                    existing_result = await db.execute(
                        select(UniverseName).where(UniverseName.id.in_(returned_ids))
                    )
                    existing_map = {
                        record.id: record for record in existing_result.scalars().all()
                    }

                    for item in esi_data:
                        item_id = int(item["id"])
                        item_name = str(item["name"])
                        item_category = str(item.get("category", "unknown"))

                        resolved[item_id] = item_name
                        l1_name_cache[item_id] = item_name

                        existing = existing_map.get(item_id)
                        if existing is None:
                            db.add(
                                UniverseName(
                                    id=item_id,
                                    name=item_name,
                                    category=item_category,
                                )
                            )
                        else:
                            existing.name = item_name
                            existing.category = item_category

                    pending_ids.difference_update(returned_ids)
                    await db.commit()
                except Exception as db_exc:
                    logger.warning("⚠️ [ESI] 缓存名称到数据库失败：错误=%s", db_exc)
                    await db.rollback()  # 👈 回滚中止的事务
        except aiohttp.ClientError as exc:
            logger.warning("⚠️ [ESI] 宇宙名称请求失败：错误=%s", exc)


esi_service = EveESIService()