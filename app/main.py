import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config.logging_config import setup_logging, get_logger
from app.config.settings import get_settings
from app.db.connection import create_tables
from app.api.router import api_router
from app.utils.response_formatter import error_response

# Initialize logging FIRST — before any logger is used
setup_logging()

logger = get_logger(__name__)
settings = get_settings()


def _preload_ml_model():
    """Load ML model di background thread saat startup."""
    try:
        from app.core.services.model_service import _load_model
        _load_model()
        logger.info("[STARTUP] ML model berhasil dimuat di background")
    except Exception as e:
        logger.warning("[STARTUP] Gagal preload ML model (akan dimuat saat pertama kali dipakai): %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("[STARTUP] Purifyt %s starting up...", settings.APP_VERSION)
    await create_tables()
    logger.info("[STARTUP] Database tables verified")
    asyncio.get_event_loop().run_in_executor(None, _preload_ml_model)
    yield
    # Shutdown
    logger.info("[SHUTDOWN] Purifyt shutting down...")


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
    logger.warning(
        "[HTTP %d] %s %s — %s",
        exc.status_code, request.method, request.url.path, exc.detail,
    )
    resp = error_response(message=str(exc.detail), errors=None)
    return JSONResponse(status_code=exc.status_code, content=resp.model_dump(mode="json"))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(
        "[VALIDATION] %s %s — %s",
        request.method, request.url.path, exc.errors(),
    )
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
