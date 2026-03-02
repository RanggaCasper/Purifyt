import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import get_settings
from app.db.connection import create_tables
from app.api.router import api_router
from app.utils.response_formatter import error_response

logger = logging.getLogger(__name__)
settings = get_settings()


def _preload_ml_model():
    """Load ML model di background thread saat startup."""
    try:
        from app.core.services.model_service import _load_model
        _load_model()
        logger.info("ML model berhasil dimuat di background.")
    except Exception as e:
        logger.warning(f"Gagal preload ML model (akan dimuat saat pertama kali dipakai): {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables + preload ML model in background
    await create_tables()
    asyncio.get_event_loop().run_in_executor(None, _preload_ml_model)
    yield
    # Shutdown: nothing to clean up


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "FastAPI backend for collecting and managing YouTube comment datasets. "
        "Supports importing data from YouTube API v3 and Kaggle."
    ),
    lifespan=lifespan,
)

# CORS – allow_credentials requires explicit origins (not "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)


# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    resp = error_response(message=str(exc.detail), errors=None)
    return JSONResponse(status_code=exc.status_code, content=resp.model_dump(mode="json"))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    resp = error_response(
        message="Validation error",
        errors=exc.errors(),
    )
    return JSONResponse(status_code=422, content=resp.model_dump(mode="json"))

# Routes
app.include_router(api_router)


@app.get("/", tags=["Health"])
async def root():
    from app.utils.response_formatter import success_response
    return success_response(
        data={
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
        },
        message="Service is running",
    )


@app.get("/health", tags=["Health"])
async def health():
    from app.utils.response_formatter import success_response
    return success_response(data={"status": "ok"}, message="Healthy")
