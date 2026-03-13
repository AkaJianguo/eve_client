import datetime as dt

from pydantic import BaseModel, Field


class MarketHistoryItem(BaseModel):
    date: "dt.date" = Field(..., description="历史数据对应的日期。", examples=["2026-03-10"])
    average: float = Field(..., description="当日平均成交价。", examples=[4.52])
    highest: float = Field(..., description="当日最高成交价。", examples=[4.87])
    lowest: float = Field(..., description="当日最低成交价。", examples=[4.13])
    volume: int = Field(..., description="当日成交量。", examples=[125000000])
    order_count: int = Field(..., description="当日订单数量。", examples=[18234])

    model_config = {"from_attributes": True}


class MarketOrder(BaseModel):
    order_id: int = Field(..., description="订单 ID。", examples=[123456789])
    is_buy_order: bool = Field(..., description="是否为买单。", examples=[False])
    price: float = Field(..., description="订单价格，单位 ISK。", examples=[15200.50])
    volume_remain: int = Field(..., description="剩余数量。", examples=[50000])
    location_id: int = Field(..., description="挂单位置 ID。", examples=[60003760])
    system_id: int = Field(..., description="所在太阳系 ID。", examples=[30000142])
    location_name: str | None = Field("未知建筑", description="挂单位置名称。", examples=["Jita IV - Moon 4 - Caldari Navy Assembly Plant"])
    system_name: str | None = Field("未知星系", description="所在太阳系名称。", examples=["Jita"])

    model_config = {"from_attributes": True}