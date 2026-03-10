from __future__ import annotations

import logging
from typing import Any

import aiohttp
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.universe import UniverseName


logger = logging.getLogger(__name__)

ESI_USER_AGENT = "WangJianGuo-EVE-ESI/1.0"
MAX_UNIVERSE_NAME_ID = 2_147_483_647


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
            logger.warning("ESI session was not initialized by app lifespan; creating fallback session")
            self._session = self._build_session()
        return self._session

    async def start(self) -> None:
        if self._session is None or self._session.closed:
            self._session = self._build_session()
            logger.info("ESI service session started")

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()
            logger.info("ESI service session closed")

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
                        "ESI character lookup failed: character_id=%s status=%s body=%s",
                        character_id,
                        response.status,
                        body,
                    )
                    return None
                return await response.json()
        except aiohttp.ClientError as exc:
            logger.warning("ESI character request failed: character_id=%s error=%s", character_id, exc)
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
                        "ESI industry jobs lookup failed: character_id=%s status=%s body=%s",
                        character_id,
                        response.status,
                        body,
                    )
                    return None
                return await response.json()
        except aiohttp.ClientError as exc:
            logger.warning(
                "ESI industry jobs request failed: character_id=%s error=%s",
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
                        "ESI wallet balance lookup failed: character_id=%s status=%s body=%s",
                        character_id,
                        response.status,
                        body,
                    )
                    return None
                payload = await response.json()
                return float(payload)
        except (aiohttp.ClientError, TypeError, ValueError) as exc:
            logger.warning("ESI wallet balance request failed: character_id=%s error=%s", character_id, exc)
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
                        "ESI wallet transactions lookup failed: character_id=%s status=%s body=%s",
                        character_id,
                        response.status,
                        body,
                    )
                    return None
                payload = await response.json()
                return payload if isinstance(payload, list) else None
        except aiohttp.ClientError as exc:
            logger.warning("ESI wallet transactions request failed: character_id=%s error=%s", character_id, exc)
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
                            "ESI %s lookup failed: character_id=%s page=%s status=%s body=%s",
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
                            "ESI %s returned unexpected payload: character_id=%s page=%s payload_type=%s",
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
            logger.warning("ESI %s request failed: character_id=%s error=%s", log_key, character_id, exc)
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
                            "ESI %s lookup failed: character_id=%s chunk_start=%s status=%s body=%s",
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
                            "ESI %s returned unexpected payload: character_id=%s payload_type=%s",
                            log_key,
                            character_id,
                            type(payload).__name__,
                        )
                        return None

                    aggregated.extend(payload)
        except aiohttp.ClientError as exc:
            logger.warning("ESI %s request failed: character_id=%s error=%s", log_key, character_id, exc)
            return None

        return aggregated

    async def resolve_ids(self, db: AsyncSession, ids: list[int]) -> dict[int, str]:
        """Resolve EVE IDs via SDE tables, local cache, then ESI fallback."""
        if not ids:
            return {}

        pending_ids = {item_id for item_id in dict.fromkeys(ids) if 0 < item_id <= MAX_UNIVERSE_NAME_ID}
        resolved: dict[int, str] = {}

        if not pending_ids:
            return resolved

        await self._resolve_from_sde(db, pending_ids, resolved)
        await self._resolve_from_cache(db, pending_ids, resolved)
        await self._resolve_from_esi(db, pending_ids, resolved)

        return resolved

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
            items_query = text(
                f"SELECT type_id AS typeid, COALESCE(zh_name, name, en_name, de_name) AS typename FROM sde.types WHERE type_id IN ({id_list_str})"
            )
            items_result = await db.execute(items_query)
            for row in items_result.mappings():
                item_id = int(row["typeid"])
                resolved[item_id] = str(row["typename"])
                pending_ids.discard(item_id)
        except Exception as exc:
            logger.warning("SDE types lookup failed: %s", exc)
            await db.rollback()  # 👈 回滚中止的事务

        if not pending_ids:
            return

        id_list_str = ",".join(map(str, sorted(pending_ids)))

        try:
            systems_query = text(
                f'SELECT "solarSystemID" AS solarsystemid, COALESCE("solarSystemName_zh", "solarSystemName", "solarSystemName_en") AS solarsystemname FROM sde.solarsystems WHERE "solarSystemID" IN ({id_list_str})'
            )
            systems_result = await db.execute(systems_query)
            for row in systems_result.mappings():
                system_id = int(row["solarsystemid"])
                resolved[system_id] = str(row["solarsystemname"])
                pending_ids.discard(system_id)
        except Exception as exc:
            logger.warning("SDE solarsystems lookup failed: %s", exc)
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
                pending_ids.discard(record.id)
        except Exception as exc:
            logger.warning("Universe names cache lookup failed: %s", exc)
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
                        "ESI universe names lookup failed: status=%s body=%s",
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
                    logger.warning("Database operation failed while caching ESI names: %s", db_exc)
                    await db.rollback()  # 👈 回滚中止的事务
        except aiohttp.ClientError as exc:
            logger.warning("ESI universe names request failed: %s", exc)


esi_service = EveESIService()