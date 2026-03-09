import logging
import urllib.parse
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import AuthCallbackParams, AuthCallbackResponse
from app.core.config import settings
from app.core.security import create_access_token
from app.crud.user import process_sso_login, update_character_esi_info
from app.database import get_db
from app.schemas import ErrorResponse, ValidationErrorResponse
from app.services.eve_esi import esi_service
from app.services.eve_sso import sso_service


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.get(
    "/login",
    summary="跳转至 EVE SSO 登录页",
    description="生成 EVE 官方 SSO 授权地址，并将用户重定向到 CCP 登录页面。",
    responses={302: {"description": "重定向到 EVE SSO 授权页面"}},
)
async def sso_login_redirect():
    """生成跳转链接并重定向至 EVE 官网"""
    client_id = settings.ESI_CLIENT_ID
    redirect_uri = settings.ESI_CALLBACK_URL

    logger.info(
        "Preparing EVE SSO redirect: client_id_configured=%s redirect_uri=%s",
        bool(client_id),
        redirect_uri,
    )

    scopes = "esi-industry.read_character_jobs.v1"
    state = str(uuid.uuid4())

    params = {
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "scope": scopes,
        "state": state,
    }

    auth_url = f"https://login.eveonline.com/v2/oauth/authorize?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get(
    "/callback",
    response_model=AuthCallbackResponse,
    summary="处理 EVE SSO 回调",
    description="接收 EVE SSO 回调参数，换取官方 token，完成本站用户登录，并返回本站 JWT。",
    responses={
        200: {"description": "登录成功并返回本站 JWT"},
        422: {"description": "回调参数缺失或格式不正确", "model": ValidationErrorResponse},
        502: {"description": "EVE SSO 或 ESI 上游请求失败", "model": ErrorResponse},
    },
)
async def sso_callback(
    request: Request,
    params: Annotated[AuthCallbackParams, Query()],
    db: AsyncSession = Depends(get_db),
):
    """处理 EVE 官网回调，完成 Token 交换与用户注册"""
    token_data = await sso_service.get_access_token(params.code)
    char_info = await sso_service.verify_character(token_data["access_token"])

    user = await process_sso_login(db=db, char_info=char_info, token_data=token_data)
    char_id = char_info["CharacterID"]
    esi_data = await esi_service.get_character_public_info(char_id)
    if esi_data:
        await update_character_esi_info(db=db, character_id=char_id, esi_data=esi_data)

    jwt_payload = {
        "sub": str(user.id),
        "character_id": char_info["CharacterID"],
        "character_name": char_info["CharacterName"],
    }

    access_token = create_access_token(data=jwt_payload)

    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header:
        query = urllib.parse.urlencode(
            {
                "access_token": access_token,
                "character_name": char_info["CharacterName"],
                "user_id": user.id,
            }
        )
        return RedirectResponse(url=f"{settings.FRONTEND_URL.rstrip('/')}/login/callback?{query}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "character_name": char_info["CharacterName"],
        "msg": "登录成功！请将 access_token 保存至前端 localStorage",
    }