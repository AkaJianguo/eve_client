from pydantic import BaseModel, Field


class CurrentUserResponse(BaseModel):
    msg: str = Field(..., description="接口返回的简短说明。", examples=["欢迎来到个人中心！这是你的底层账户信息"])
    user_id: int = Field(..., description="当前平台用户 ID。", examples=[10001])
    sub_level: int = Field(..., description="当前用户的订阅或权限等级。", examples=[2])
    is_active: bool = Field(..., description="当前账号是否处于激活状态。", examples=[True])

    model_config = {
        "json_schema_extra": {
            "example": {
                "msg": "欢迎来到个人中心！这是你的底层账户信息",
                "user_id": 10001,
                "sub_level": 2,
                "is_active": True,
            }
        }
    }