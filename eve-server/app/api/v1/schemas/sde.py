from pydantic import BaseModel, Field


class SdeTypeItem(BaseModel):
    type_id: int = Field(..., description="物品类型 ID。", examples=[34])
    name: str = Field(..., description="展示给前端的物品名称，优先中文名称。", examples=["三钛合金"])
    volume: float | None = Field(0.0, description="物品基础体积，单位为立方米。", examples=[0.01])
    market_group_id: int | None = Field(None, description="所属市场分类 ID。", examples=[18])

    model_config = {"from_attributes": True}


class UnifiedTreeNode(BaseModel):
    key: str = Field(..., description="树节点唯一键。", examples=["group:4", "type:34"])
    parent_key: str | None = Field(None, description="父节点键。", examples=["group:11"])
    name: str = Field(..., description="树节点名称。", examples=["舰船", "三钛合金"])
    iconname: str | None = Field(None, description="节点图标文件名。", examples=["market_icon_1443.png"])
    is_group: bool = Field(..., description="是否为分类节点。", examples=[True])
    type_id: int | None = Field(None, description="当节点对应具体物品时的 type_id。", examples=[34])
    children: list["UnifiedTreeNode"] = Field(default_factory=list, description="子节点数组。")


UnifiedTreeNode.model_rebuild()