# app/api/deps.py
from collections.abc import Mapping

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import os

from app.core.errors import api_error
from app.database import get_db
from app.crud.user import get_character_with_valid_token
from app.models.user import User, Character

# 👇 换成 HTTPBearer，专门用于纯 Token 验证
security = HTTPBearer(auto_error=False)

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "WangJianGuo_Super_Secret_Key_88888888")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


def _build_credentials_exception() -> HTTPException:
    return api_error(
        status.HTTP_401_UNAUTHORIZED,
        "token_invalid",
        "访问令牌无效，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _build_missing_token_exception() -> HTTPException:
    return api_error(
        status.HTTP_401_UNAUTHORIZED,
        "token_missing",
        "缺少 Bearer 访问令牌，请先登录",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _extract_bearer_token(credentials: HTTPAuthorizationCredentials | None) -> str:
    if credentials is None:
        raise _build_missing_token_exception()

    if credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise api_error(
            status.HTTP_401_UNAUTHORIZED,
            "token_invalid",
            "Bearer 访问令牌格式无效，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return credentials.credentials


def _decode_access_token(token: str) -> Mapping[str, object]:
    credentials_exception = _build_credentials_exception()

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise credentials_exception from exc

    if payload.get("sub") is None:
        raise api_error(
            status.HTTP_401_UNAUTHORIZED,
            "token_subject_missing",
            "访问令牌缺少用户主体信息，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security), 
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    核心检票机：解析 Token，验证身份，并返回当前数据库里的真实 User 对象
    """
    # 提取出 Bearer 后面的那串真正的 Token 字符
    token = _extract_bearer_token(credentials)
    payload = _decode_access_token(token)
    user_id = payload.get("sub")

    # 去数据库里确认这个用户是不是真的存在，并加载其关联的角色数据
    result = await db.execute(
        select(User)
        .filter(User.id == int(user_id))
        .options(selectinload(User.characters))  # 👈 eager load 所有关联角色
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise api_error(
            status.HTTP_401_UNAUTHORIZED,
            "user_not_found",
            "当前访问令牌对应的用户不存在，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 👇 【新增逻辑】: 小黑屋拦截器
    if not user.is_active:
        raise api_error(
            status.HTTP_403_FORBIDDEN,
            "account_inactive",
            "该账号已被封禁或未激活",
        )
    return user


async def get_current_character(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Character:
    """Resolve the current JWT-bound character and refresh its ESI token when needed."""
    payload = _decode_access_token(_extract_bearer_token(credentials))
    character_id = payload.get("character_id")

    if character_id is None:
        raise api_error(
            status.HTTP_401_UNAUTHORIZED,
            "character_claim_missing",
            "访问令牌缺少角色信息，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )

    character = await get_character_with_valid_token(db, int(character_id))
    if character is None:
        raise api_error(
            status.HTTP_401_UNAUTHORIZED,
            "character_not_found",
            "当前访问令牌对应的角色不存在，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return character