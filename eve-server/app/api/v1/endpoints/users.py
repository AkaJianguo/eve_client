from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.api.v1.schemas import CurrentUserResponse
from app.models.user import User
from app.schemas import ErrorResponse


router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    summary="获取当前登录用户信息",
    description="读取当前 Bearer Token 对应的平台用户基本信息。通常用于前端启动时恢复登录态和权限信息。",
    responses={
        200: {"description": "成功返回当前用户信息"},
        401: {"description": "JWT 无效、缺失或已过期", "model": ErrorResponse},
        403: {"description": "当前账号已被禁用或未激活", "model": ErrorResponse},
    },
)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """获取当前登录玩家的个人底层信息。"""
    return {
        "msg": "欢迎来到个人中心！这是你的底层账户信息",
        "user_id": current_user.id,
        "sub_level": current_user.sub_level,
        "is_active": current_user.is_active,
    }