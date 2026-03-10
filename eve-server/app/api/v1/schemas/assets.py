from pydantic import BaseModel, ConfigDict, Field


class AssetEntryResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    item_id: int | None = Field(None, description="资产实例 ID。", examples=[1034567890123])
    type_id: int | None = Field(None, description="物品类型 ID。", examples=[34])
    type_name: str | None = Field(None, description="物品名称。", examples=["Tritanium"])
    is_blueprint_copy: bool | None = Field(None, description="是否为蓝图复制件。", examples=[False])
    is_singleton: bool | None = Field(None, description="是否为唯一实例。", examples=[False])
    location_id: int | None = Field(None, description="位置 ID。", examples=[60003760])
    location_name: str | None = Field(None, description="位置名称。", examples=["Jita IV - Moon 4 - Caldari Navy Assembly Plant"])
    location_flag: str | None = Field(None, description="位置槽位标记。", examples=["Hangar"])
    location_type: str | None = Field(None, description="位置类型。", examples=["station"])
    quantity: int | None = Field(None, description="数量。", examples=[500000])
    name: str | None = Field(None, description="资产自定义名称，例如货柜或飞船名称。", examples=["Jita Hauler"])
    position_x: float | None = Field(None, description="资产空间坐标 X。", examples=[0])
    position_y: float | None = Field(None, description="资产空间坐标 Y。", examples=[0])
    position_z: float | None = Field(None, description="资产空间坐标 Z。", examples=[0])


class AssetsSummaryResponse(BaseModel):
    blueprint_count: int = Field(..., description="蓝图复制件或蓝图相关条目数量。", examples=[18])
    singleton_count: int = Field(..., description="唯一实例资产数量。", examples=[42])
    total_quantity: int = Field(..., description="数量字段的汇总值。", examples=[1250000])


class AssetsResponse(BaseModel):
    user_id: int = Field(..., description="当前平台用户 ID。", examples=[10001])
    character_id: int = Field(..., description="当前请求绑定的 EVE 角色 ID。", examples=[2119999999])
    character_name: str = Field(..., description="当前请求绑定的 EVE 角色名称。", examples=["Wang JianGuo"])
    asset_count: int = Field(..., description="返回的资产总数。", examples=[1523])
    page: int = Field(..., description="当前页码。", examples=[1])
    page_size: int = Field(..., description="当前页大小。", examples=[100])
    total_count: int = Field(..., description="资产总记录数。", examples=[1523])
    summary: AssetsSummaryResponse = Field(..., description="资产汇总信息。")
    assets: list[AssetEntryResponse] = Field(..., description="资产列表。")