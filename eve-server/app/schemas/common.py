from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error_code: str = Field(..., description="机器可读的错误代码。", examples=["unauthorized"])
    message: str = Field(..., description="面向调用方的错误说明。", examples=["无效的凭证，请重新登录"])

    model_config = {
        "json_schema_extra": {
            "example": {
                "error_code": "unauthorized",
                "message": "无效的凭证，请重新登录",
            }
        }
    }


class ValidationErrorItem(BaseModel):
    field: str = Field(..., description="校验失败的字段路径。", examples=["query.code"])
    message: str = Field(..., description="该字段对应的校验错误消息。", examples=["Field required"])
    error_type: str = Field(..., description="Pydantic/FastAPI 返回的错误类型。", examples=["missing"])


class ValidationErrorResponse(ErrorResponse):
    details: list[ValidationErrorItem] = Field(..., description="字段级校验错误明细。")

    model_config = {
        "json_schema_extra": {
            "example": {
                "error_code": "validation_error",
                "message": "请求参数校验失败",
                "details": [
                    {
                        "field": "query.code",
                        "message": "Field required",
                        "error_type": "missing",
                    }
                ],
            }
        }
    }


class HealthResponse(BaseModel):
    status: str = Field(..., description="服务当前状态。", examples=["running"])
    version: str = Field(..., description="当前后端版本号。", examples=["1.0.0"])

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "running",
                "version": "1.0.0",
            }
        }
    }