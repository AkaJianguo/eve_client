from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CharacterInfo(BaseModel):
    """角色基本信息"""
    id: int = Field(..., description="EVE 角色 ID", examples=[2123937997])
    name: str = Field(..., description="角色名称", examples=["Char Aznable"])
    corporation_id: int = Field(..., description="军团 ID", examples=[98765432])
    alliance_id: Optional[int] = Field(None, description="联盟 ID", examples=[99999999])
    security_status: Optional[float] = Field(None, description="安全等级", examples=[1.5])
    birthday: Optional[datetime] = Field(None, description="角色创建时间 (UTC)")
    
    class Config:
        from_attributes = True


class CurrentUserResponse(BaseModel):
    msg: str = Field(..., description="接口返回的简短说明。", examples=["欢迎来到个人中心！这是你的底层账户信息"])
    user_id: int = Field(..., description="当前平台用户 ID。", examples=[10001])
    sub_level: int = Field(..., description="当前用户的订阅或权限等级。", examples=[2])
    is_active: bool = Field(..., description="当前账号是否处于激活状态。", examples=[True])
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间", examples=["2024-01-15T10:30:00"])
    character: Optional[CharacterInfo] = Field(None, description="当前玩家的主要角色信息")

    model_config = {
        "json_schema_extra": {
            "example": {
                "msg": "欢迎来到个人中心！这是你的底层账户信息",
                "user_id": 10001,
                "sub_level": 2,
                "is_active": True,
                "last_login_at": "2024-01-15T10:30:00",
                "character": {
                    "id": 2123937997,
                    "name": "Char Aznable",
                    "corporation_id": 98765432,
                    "alliance_id": 99999999,
                    "security_status": 1.5,
                    "birthday": "2023-06-01T00:00:00"
                }
            }
        },
        "from_attributes": True
    }