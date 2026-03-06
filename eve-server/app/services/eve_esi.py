from __future__ import annotations

import logging
from typing import Any

import aiohttp
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.universe import UniverseName


logger = logging.getLogger(__name__)

ESI_USER_AGENT = "WangJianGuo-EVE-ESI/1.0"


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

    async def resolve_ids(self, db: AsyncSession, ids: list[int]) -> dict[int, str]:
        """Resolve EVE IDs via SDE tables, local cache, then ESI fallback."""
        if not ids:
            return {}

        pending_ids = set(dict.fromkeys(ids))
        resolved: dict[int, str] = {}

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
                f"SELECT typeid, typename FROM sde.types WHERE typeid IN ({id_list_str})"
            )
            items_result = await db.execute(items_query)
            for row in items_result.mappings():
                item_id = int(row["typeid"])
                resolved[item_id] = str(row["typename"])
                pending_ids.discard(item_id)
        except Exception as exc:
            logger.warning("SDE types lookup failed: %s", exc)

        if not pending_ids:
            return

        id_list_str = ",".join(map(str, sorted(pending_ids)))

        try:
            systems_query = text(
                f"SELECT solarsystemid, solarsystemname FROM sde.solarsystems WHERE solarsystemid IN ({id_list_str})"
            )
            systems_result = await db.execute(systems_query)
            for row in systems_result.mappings():
                system_id = int(row["solarsystemid"])
                resolved[system_id] = str(row["solarsystemname"])
                pending_ids.discard(system_id)
        except Exception as exc:
            logger.warning("SDE solarsystems lookup failed: %s", exc)

    async def _resolve_from_cache(
        self,
        db: AsyncSession,
        pending_ids: set[int],
        resolved: dict[int, str],
    ) -> None:
        if not pending_ids:
            return

        result = await db.execute(select(UniverseName).where(UniverseName.id.in_(pending_ids)))
        for record in result.scalars().all():
            resolved[record.id] = record.name
            pending_ids.discard(record.id)

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
        except aiohttp.ClientError as exc:
            logger.warning("ESI universe names request failed: %s", exc)


esi_service = EveESIService()