from datetime import datetime, timezone
from typing import Any, Optional, List
from pydantic import BaseModel


class APIResponse(BaseModel):
    status: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    errors: Optional[Any] = None
    timestamp: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


def success_response(
    data: Any = None,
    message: str = "Success",
) -> APIResponse:
    return APIResponse(
        status=True,
        data=data,
        message=message,
        errors=None,
        timestamp=datetime.now(timezone.utc),
    )


def error_response(
    message: str = "An error occurred",
    errors: Any = None,
    data: Any = None,
) -> APIResponse:
    return APIResponse(
        status=False,
        data=data,
        message=message,
        errors=errors,
        timestamp=datetime.now(timezone.utc),
    )
