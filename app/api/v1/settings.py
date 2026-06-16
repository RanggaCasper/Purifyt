from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.settings.schemas import AppCredentialsRequest, AppCredentialsResponse
from app.db.connection import get_db
from app.modules.settings.repository import AppSettingRepository
from app.shared.utils.response_formatter import APIResponse, success_response


router = APIRouter(prefix="/settings", tags=["Settings"])

YOUTUBE_API_KEY = "YOUTUBE_API_KEY"
KAGGLE_USERNAME = "KAGGLE_USERNAME"
KAGGLE_KEY = "KAGGLE_KEY"
SETTING_KEYS = [YOUTUBE_API_KEY, KAGGLE_USERNAME, KAGGLE_KEY]


def _credentials_response(values: dict[str, str | None]) -> AppCredentialsResponse:
    youtube_api_key = values.get(YOUTUBE_API_KEY) or ""
    kaggle_username = values.get(KAGGLE_USERNAME) or ""
    kaggle_key = values.get(KAGGLE_KEY) or ""
    return AppCredentialsResponse(
        youtube_api_key=youtube_api_key,
        kaggle_username=kaggle_username,
        kaggle_key=kaggle_key,
        youtube_api_key_set=bool(youtube_api_key.strip()),
        kaggle_username_set=bool(kaggle_username.strip()),
        kaggle_key_set=bool(kaggle_key.strip()),
    )


@router.get("/credentials", response_model=APIResponse)
async def get_credentials(db: AsyncSession = Depends(get_db)):
    repo = AppSettingRepository(db)
    values = await repo.get_many(SETTING_KEYS)
    return success_response(data=_credentials_response(values))


@router.put("/credentials", response_model=APIResponse)
async def update_credentials(
    payload: AppCredentialsRequest,
    db: AsyncSession = Depends(get_db),
):
    values = await AppSettingRepository(db).set_many({
        YOUTUBE_API_KEY: (payload.youtube_api_key or "").strip(),
        KAGGLE_USERNAME: (payload.kaggle_username or "").strip(),
        KAGGLE_KEY: (payload.kaggle_key or "").strip(),
    })
    return success_response(
        data=_credentials_response(values),
        message="Settings saved successfully",
    )
