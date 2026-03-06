from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator


class IndustryJobsQueryParams(BaseModel):
    include_completed: bool = Field(
        True,
        description="是否同时返回已完成、已交付或已取消的工业任务。为 false 时通常更适合只看当前进行中的作业。",
        examples=[True],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "include_completed": True,
            }
        }
    }


class IndustryJobStatus(StrEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    DELIVERED = "delivered"
    PAUSED = "paused"
    READY = "ready"
    REVERTED = "reverted"
    UNKNOWN = "unknown"


class IndustryJobResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    job_id: int | None = Field(None, description="工业任务唯一 ID。", examples=[453829102])
    activity_id: int | None = Field(None, description="工业活动类型 ID，例如制造、发明、复制。", examples=[1])
    completed_character_id: int | None = Field(None, description="完成或交付该工业任务的角色 ID。", examples=[2119999999])
    completed_character_name: str | None = Field(None, description="完成或交付该工业任务的角色名称。", examples=["Wang JianGuo"]) 
    blueprint_id: int | None = Field(None, description="蓝图实例 ID。对于某些活动可能为空。", examples=[1034567890123])
    blueprint_location_id: int | None = Field(None, description="蓝图所在位置 ID。", examples=[60003760])
    blueprint_location_name: str | None = Field(None, description="蓝图所在位置名称。", examples=["Jita IV - Moon 4 - Caldari Navy Assembly Plant"])
    blueprint_type_id: int | None = Field(None, description="蓝图类型 ID。", examples=[2047])
    blueprint_name: str | None = Field(None, description="蓝图名称，已做 ESI/SDE 翻译。", examples=["Scourge Heavy Missile Blueprint"])
    cost: float | None = Field(None, description="工业任务花费。", examples=[1250000.5])
    duration: int | None = Field(None, description="任务总时长，单位为秒。", examples=[86400])
    end_date: datetime | None = Field(None, description="任务预计结束时间。", examples=["2026-03-06T12:34:56Z"])
    product_type_id: int | None = Field(None, description="产出物类型 ID。", examples=[30744])
    product_name: str | None = Field(None, description="产出物名称，已做 ESI/SDE 翻译。", examples=["Scourge Fury Heavy Missile"])
    facility_id: int | None = Field(None, description="执行该工业任务的设施 ID。", examples=[1038457641673])
    facility_name: str | None = Field(None, description="设施名称，已做 ESI/SDE 翻译。", examples=["Tatara - Moon Drill"])
    installer_id: int | None = Field(None, description="发起该工业任务的角色 ID。", examples=[2119999999])
    installer_name: str | None = Field(None, description="发起该工业任务的角色名称。", examples=["Wang JianGuo"])
    licensed_runs: int | None = Field(None, description="蓝图许可次数，通常用于复制或发明。", examples=[10])
    location_id: int | None = Field(None, description="作业输入材料位置 ID。", examples=[60003760])
    location_name: str | None = Field(None, description="作业输入材料位置名称。", examples=["Jita IV - Moon 4 - Caldari Navy Assembly Plant"])
    output_location_id: int | None = Field(None, description="产出物输出位置 ID。", examples=[60003760])
    output_location_name: str | None = Field(None, description="产出物输出位置名称。", examples=["Jita IV - Moon 4 - Caldari Navy Assembly Plant"])
    pause_date: datetime | None = Field(None, description="任务暂停时间。未暂停时为空。", examples=["2026-03-06T08:00:00Z"])
    probability: float | None = Field(None, description="发明等概率型工业任务的成功率。", examples=[0.42])
    runs: int | None = Field(None, description="计划执行次数。", examples=[20])
    start_date: datetime | None = Field(None, description="任务开始时间。", examples=["2026-03-05T12:34:56Z"])
    station_id: int | None = Field(None, description="兼容部分 ESI 返回的空间站 ID。", examples=[60003760])
    station_name: str | None = Field(None, description="空间站名称。", examples=["Jita IV - Moon 4 - Caldari Navy Assembly Plant"])
    successful_runs: int | None = Field(None, description="已经成功完成的次数。", examples=[5])
    completed_date: datetime | None = Field(None, description="任务实际完成或交付时间。", examples=["2026-03-06T13:00:00Z"])
    status: IndustryJobStatus | None = Field(None, description="工业任务状态枚举。", examples=["active"])

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value: str | IndustryJobStatus | None) -> str | IndustryJobStatus | None:
        if value is None or isinstance(value, IndustryJobStatus):
            return value

        normalized = value.lower()
        if normalized in IndustryJobStatus._value2member_map_:
            return normalized
        return IndustryJobStatus.UNKNOWN

    @computed_field
    @property
    def status_label(self) -> str | None:
        if self.status is None:
            return None

        return {
            IndustryJobStatus.ACTIVE: "进行中",
            IndustryJobStatus.CANCELLED: "已取消",
            IndustryJobStatus.DELIVERED: "已交付",
            IndustryJobStatus.PAUSED: "已暂停",
            IndustryJobStatus.READY: "可交付",
            IndustryJobStatus.REVERTED: "已回退",
            IndustryJobStatus.UNKNOWN: "未知状态",
        }[self.status]


class IndustryJobsResponse(BaseModel):
    user_id: int = Field(..., description="当前平台用户 ID。", examples=[10001])
    character_id: int = Field(..., description="当前请求绑定的 EVE 角色 ID。", examples=[2119999999])
    character_name: str = Field(..., description="当前请求绑定的 EVE 角色名称。", examples=["Wang JianGuo"])
    job_count: int = Field(..., description="本次返回的工业任务数量。", examples=[12])
    jobs: list[IndustryJobResponse] = Field(..., description="工业任务列表，已包含常见名称翻译字段。")

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": 10001,
                "character_id": 2119999999,
                "character_name": "Wang JianGuo",
                "job_count": 1,
                "jobs": [
                    {
                        "job_id": 453829102,
                        "activity_id": 1,
                        "blueprint_type_id": 2047,
                        "blueprint_name": "Scourge Heavy Missile Blueprint",
                        "product_type_id": 30744,
                        "product_name": "Scourge Fury Heavy Missile",
                        "facility_id": 1038457641673,
                        "facility_name": "Tatara - Moon Drill",
                        "installer_id": 2119999999,
                        "installer_name": "Wang JianGuo",
                        "runs": 20,
                        "successful_runs": 5,
                        "start_date": "2026-03-05T12:34:56Z",
                        "end_date": "2026-03-06T12:34:56Z",
                        "status": "active",
                        "status_label": "进行中"
                    }
                ]
            }
        }
    }