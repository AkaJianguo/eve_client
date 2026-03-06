from typing import Any

from fastapi import HTTPException


def api_error(status_code: int, error_code: str, message: str, *, headers: dict[str, str] | None = None, **extra: Any) -> HTTPException:
    detail = {"error_code": error_code, "message": message}
    if extra:
        detail.update(extra)
    return HTTPException(status_code=status_code, detail=detail, headers=headers)