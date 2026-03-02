from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.logging_config import get_logger
from app.db.connection import get_db
from app.db.repositories.user_repository import UserRepository
from app.core.schemas import UserResponse
from app.core.services.auth_service import get_current_user
from app.utils.response_formatter import APIResponse, paginated_response

logger = get_logger(__name__)
router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=APIResponse)
async def list_users(
    page: int = 1,
    per_page: int = 20,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    logger.debug("[USERS] List users page=%d per_page=%d", page, per_page)
    repo = UserRepository(db)
    skip = (page - 1) * per_page
    users = await repo.get_all(skip=skip, limit=per_page)
    total = await repo.count()
    logger.info("[USERS] Listed %d/%d users", len(users), total)
    return paginated_response(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{user_id}", response_model=APIResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    logger.debug("[USERS] Get user_id=%d", user_id)
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        logger.warning("[USERS] User not found id=%d", user_id)
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")
    return success_response(data=UserResponse.model_validate(user))
