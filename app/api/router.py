from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.datasets import router as datasets_router
from app.api.v1.youtube import router as youtube_router
from app.api.v1.kaggle import router as kaggle_router
from app.api.v1.labeling import router as labeling_router
from app.api.v1.explorer import router as explorer_router
from app.api.v1.channel_explorer import router as channel_explorer_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(datasets_router)
api_router.include_router(youtube_router)
api_router.include_router(kaggle_router)
api_router.include_router(labeling_router)
api_router.include_router(explorer_router)
api_router.include_router(channel_explorer_router)
