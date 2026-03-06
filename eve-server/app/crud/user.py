from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User, Character
from datetime import datetime, timedelta, timezone

from app.services.eve_sso import sso_service


def _build_token_expire_time(token_data: dict) -> datetime:
    expires_in = token_data.get("expires_in", 1199)
    return datetime.now(timezone.utc) + timedelta(seconds=expires_in)

async def process_sso_login(db: AsyncSession, char_info: dict, token_data: dict, current_user_id: int = None) -> User:
    """处理 SSO 登录的数据库 Upsert 逻辑 (全异步版本)"""
    character_id = char_info["CharacterID"]
    character_name = char_info["CharacterName"]
    
    expire_time = _build_token_expire_time(token_data)

    # 1. 异步查询现有角色
    result = await db.execute(select(Character).filter(Character.id == character_id))
    db_char = result.scalar_one_or_none()

    if db_char:
        # 【老角色登录】更新现有角色的 Token
        db_char.access_token = token_data["access_token"]
        db_char.refresh_token = token_data.get("refresh_token")
        db_char.token_expires = expire_time
        await db.commit()
        
        # 获取对应的 User
        user_result = await db.execute(select(User).filter(User.id == db_char.owner_id))
        user = user_result.scalar_one_or_none()
    else:
        # 【新角色接入】
        if not current_user_id:
            # 创建全新底层账户
            new_user = User(sub_level=2)
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            owner_id = new_user.id
        else:
            # 绑定到现有账户
            owner_id = current_user_id

        # 写入角色表
        new_char = Character(
            id=character_id,
            name=character_name,
            owner_id=owner_id,
            corporation_id=0, 
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_expires=expire_time
        )
        db.add(new_char)
        await db.commit()
        
        # 获取对应的 User
        user_result = await db.execute(select(User).filter(User.id == owner_id))
        user = user_result.scalar_one_or_none()

    # 👇 【新增打卡逻辑】统一更新最后登录时间
    if user:
        # 使用 UTC 时间打卡
        user.last_login_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(user)

    return user


async def ensure_character_access_token(
    db: AsyncSession,
    character: Character,
    refresh_window_seconds: int = 300,
) -> Character:
    """Refresh the stored ESI token when it is missing, expired, or close to expiry."""
    now = datetime.now(timezone.utc)
    refresh_deadline = now + timedelta(seconds=refresh_window_seconds)

    if not character.refresh_token:
        return character

    if character.token_expires and character.token_expires > refresh_deadline and character.access_token:
        return character

    token_data = await sso_service.refresh_access_token(character.refresh_token)
    character.access_token = token_data["access_token"]
    character.refresh_token = token_data.get("refresh_token", character.refresh_token)
    character.token_expires = _build_token_expire_time(token_data)

    await db.commit()
    await db.refresh(character)
    return character


async def get_character_with_valid_token(db: AsyncSession, character_id: int) -> Character | None:
    """Load a character record and ensure its ESI access token is still usable."""
    result = await db.execute(select(Character).filter(Character.id == character_id))
    character = result.scalar_one_or_none()
    if character is None:
        return None

    return await ensure_character_access_token(db, character)


async def update_character_esi_info(db: AsyncSession, character_id: int, esi_data: dict):
    """把 ESI 爬回来的档案更新到数据库"""
    result = await db.execute(select(Character).filter(Character.id == character_id))
    db_char = result.scalar_one_or_none()

    if db_char and esi_data:
        # 开始填坑
        db_char.corporation_id = esi_data.get("corporation_id", 0)
        db_char.alliance_id = esi_data.get("alliance_id")
        db_char.faction_id = esi_data.get("faction_id")
        db_char.security_status = esi_data.get("security_status")
        db_char.gender = esi_data.get("gender")
        db_char.bloodline_id = esi_data.get("bloodline_id")
        db_char.race_id = esi_data.get("race_id")
        db_char.ancestry_id = esi_data.get("ancestry_id")
        db_char.title = esi_data.get("title")
        db_char.description = esi_data.get("description")

        # 处理 EVE 的特殊时间格式 (例如 "2010-05-14T12:34:56Z")
        birthday_str = esi_data.get("birthday")
        if birthday_str:
            try:
                db_char.birthday = datetime.strptime(birthday_str, "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                pass

        await db.commit()
        await db.refresh(db_char)