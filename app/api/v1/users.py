from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db
from app.db.repositories.user_repository import UserRepository
from app.core.schemas import UserResponse
from app.core.services.auth_service import get_current_user
from app.utils.response_formatter import APIResponse, success_response

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=APIResponse)
async def list_users(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    repo = UserRepository(db)
    users = await repo.get_all(skip=skip, limit=limit)
    return success_response(data=[UserResponse.model_validate(u) for u in users])


@router.get("/{user_id}", response_model=APIResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")
    return success_response(data=UserResponse.model_validate(user))
