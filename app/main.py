from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import get_settings
from app.db.connection import create_tables
from app.api.router import api_router
from app.utils.response_formatter import error_response

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    await create_tables()
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

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
