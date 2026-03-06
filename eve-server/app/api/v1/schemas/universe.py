from pydantic import BaseModel, Field, field_validator


class UniverseNamesRequest(BaseModel):
    ids: list[int] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="传入需要翻译的正整数 ID 数组，例如 [30000142, 2123937997]",
        examples=[[30000142, 2123937997, 60003760]],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "ids": [30000142, 2123937997, 60003760]
            }
        }
    }

    @field_validator("ids")
    @classmethod
    def validate_ids(cls, values: list[int]) -> list[int]:
        if any(value <= 0 for value in values):
            raise ValueError("ids 里的每个值都必须是正整数")
        return values


class UniverseNamesResponse(BaseModel):
    status: str = Field(
        ...,
        description="请求处理结果标记。当前成功返回固定为 success。",
        examples=["success"],
    )
    resolved_count: int = Field(
        ...,
        description="本次成功翻译出的 ID 数量。",
        examples=[3],
    )
    data: dict[int, str] = Field(
        ...,
        description="ID 到名称的映射结果。键为原始 ID，值为翻译后的名称。",
        examples=[{30000142: "Jita", 2123937997: "Wang JianGuo", 60003760: "Jita IV - Moon 4 - Caldari Navy Assembly Plant"}],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "resolved_count": 3,
                "data": {
                    "30000142": "Jita",
                    "2123937997": "Wang JianGuo",
                    "60003760": "Jita IV - Moon 4 - Caldari Navy Assembly Plant"
                }
            }
        }
    }