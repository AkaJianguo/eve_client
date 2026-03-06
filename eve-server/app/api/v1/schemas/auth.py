from pydantic import BaseModel, Field


class AuthCallbackParams(BaseModel):
    code: str = Field(
        ...,
        min_length=1,
        description="EVE SSO 回调返回的授权码，用于向 SSO 服务器换取 access_token。",
        examples=["zY1vR9-example-code"],
    )
    state: str = Field(
        ...,
        min_length=1,
        description="登录发起时生成的状态校验值，用于防止 CSRF 和串号回调。",
        examples=["3e4f5f7e-d0de-4caa-9f45-123456789abc"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "code": "zY1vR9-example-code",
                "state": "3e4f5f7e-d0de-4caa-9f45-123456789abc",
            }
        }
    }


class AuthCallbackResponse(BaseModel):
    access_token: str = Field(
        ...,
        description="本站签发给前端使用的 JWT，不是 EVE 官方 access_token。",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )
    token_type: str = Field(
        ...,
        description="令牌类型，前端通常固定按 Bearer 使用。",
        examples=["bearer"],
    )
    user_id: int = Field(
        ...,
        description="本站内部平台用户 ID。",
        examples=[10001],
    )
    character_name: str = Field(
        ...,
        description="本次完成授权的 EVE 角色名称。",
        examples=["Wang JianGuo"],
    )
    msg: str = Field(
        ...,
        description="面向前端或调试页面的简短结果说明。",
        examples=["登录成功！请将 access_token 保存至前端 localStorage"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user_id": 10001,
                "character_name": "Wang JianGuo",
                "msg": "登录成功！请将 access_token 保存至前端 localStorage",
            }
        }
    }