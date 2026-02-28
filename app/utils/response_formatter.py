from datetime import datetime, timezone
from typing import Any, Optional, List, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class PaginatedData(BaseModel):
    items: List[Any]
    total: int
    page: int
    per_page: int
    total_pages: int


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


def paginated_response(
    items: List[Any],
    total: int,
    page: int,
    per_page: int,
    message: str = "Success",
) -> APIResponse:
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 1
    return APIResponse(
        status=True,
        data=PaginatedData(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
        ),
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
