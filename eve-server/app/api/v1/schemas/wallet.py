from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


WalletCacheStatus = Literal["hit_fresh", "stale_refreshing", "miss_refreshed"]


class WalletBalanceResponse(BaseModel):
    user_id: int = Field(..., description="当前平台用户 ID。", examples=[10001])
    character_id: int = Field(..., description="当前请求绑定的 EVE 角色 ID。", examples=[2119999999])
    character_name: str = Field(..., description="当前请求绑定的 EVE 角色名称。", examples=["Wang JianGuo"])
    balance: float = Field(..., description="当前角色钱包余额，单位 ISK。", examples=[123456789.12])
    updated_at: datetime | None = Field(None, description="本次余额同步时间。", examples=["2026-03-09T16:00:00Z"])
    cache_status: WalletCacheStatus = Field(..., description="缓存命中状态。fresh=新鲜缓存，stale_refreshing=返回旧缓存并后台刷新，miss_refreshed=缓存未命中并已同步刷新。")


class WalletJournalEntryResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int | None = Field(None, description="财务日记条目 ID。", examples=[987654321])
    date: datetime | None = Field(None, description="流水发生时间。", examples=["2026-03-09T12:34:56Z"])
    ref_type: str | None = Field(None, description="ESI 返回的财务引用类型。", examples=["player_trading"])
    amount: float | None = Field(None, description="本次变动金额。", examples=[-12500000.0])
    balance: float | None = Field(None, description="变动后的钱包余额。", examples=[856000000.0])
    reason: str | None = Field(None, description="备注或原因。", examples=["Jita trade"])
    first_party_id: int | None = Field(None, description="交易对手一方 ID。", examples=[2119999999])
    first_party_name: str | None = Field(None, description="交易对手一方名称。", examples=["Wang JianGuo"])
    second_party_id: int | None = Field(None, description="交易对手另一方 ID。", examples=[1000125])
    second_party_name: str | None = Field(None, description="交易对手另一方名称。", examples=["Caldari Navy"])


class WalletJournalResponse(BaseModel):
    user_id: int = Field(..., description="当前平台用户 ID。", examples=[10001])
    character_id: int = Field(..., description="当前请求绑定的 EVE 角色 ID。", examples=[2119999999])
    character_name: str = Field(..., description="当前请求绑定的 EVE 角色名称。", examples=["Wang JianGuo"])
    entry_count: int = Field(..., description="返回的财务日记条目数量。", examples=[25])
    page: int = Field(..., description="当前页码。", examples=[1])
    page_size: int = Field(..., description="当前页大小。", examples=[100])
    total_count: int = Field(..., description="总条目数。", examples=[250])
    income_total: float = Field(..., description="当前数据集收入总额。", examples=[125000000.0])
    expense_total: float = Field(..., description="当前数据集支出总额。", examples=[68000000.0])
    cache_status: WalletCacheStatus = Field(..., description="缓存命中状态。fresh=新鲜缓存，stale_refreshing=返回旧缓存并后台刷新，miss_refreshed=缓存未命中并已同步刷新。")
    entries: list[WalletJournalEntryResponse] = Field(..., description="财务日记条目列表。")


class WalletTransactionEntryResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    transaction_id: int | None = Field(None, description="市场交易记录 ID。", examples=[123456789])
    date: datetime | None = Field(None, description="交易时间。", examples=["2026-03-09T10:00:00Z"])
    type_id: int | None = Field(None, description="物品类型 ID。", examples=[34])
    type_name: str | None = Field(None, description="物品名称。", examples=["Tritanium"])
    location_id: int | None = Field(None, description="交易地点 ID。", examples=[60003760])
    location_name: str | None = Field(None, description="交易地点名称。", examples=["Jita IV - Moon 4 - Caldari Navy Assembly Plant"])
    unit_price: float | None = Field(None, description="成交单价。", examples=[4.52])
    quantity: int | None = Field(None, description="成交数量。", examples=[500000])
    is_buy: bool | None = Field(None, description="是否为买入记录。", examples=[True])
    is_personal: bool | None = Field(None, description="是否为个人交易。", examples=[True])


class WalletTransactionsResponse(BaseModel):
    user_id: int = Field(..., description="当前平台用户 ID。", examples=[10001])
    character_id: int = Field(..., description="当前请求绑定的 EVE 角色 ID。", examples=[2119999999])
    character_name: str = Field(..., description="当前请求绑定的 EVE 角色名称。", examples=["Wang JianGuo"])
    transaction_count: int = Field(..., description="返回的交易记录数量。", examples=[100])
    page: int = Field(..., description="当前页码。", examples=[1])
    page_size: int = Field(..., description="当前页大小。", examples=[100])
    total_count: int = Field(..., description="总交易数。", examples=[300])
    buy_count: int = Field(..., description="买入记录数。", examples=[40])
    sell_count: int = Field(..., description="卖出记录数。", examples=[60])
    cache_status: WalletCacheStatus = Field(..., description="缓存命中状态。fresh=新鲜缓存，stale_refreshing=返回旧缓存并后台刷新，miss_refreshed=缓存未命中并已同步刷新。")
    transactions: list[WalletTransactionEntryResponse] = Field(..., description="市场交易记录列表。")