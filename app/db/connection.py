from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.logging import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

engine_options = {
    "echo": settings.DEBUG,
    "pool_pre_ping": True,
}

if not settings.DATABASE_URL.startswith("sqlite"):
    engine_options.update({"pool_size": 10, "max_overflow": 20})

engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_options,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            logger.error("[DB] Session rollback triggered: %s", e)
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    logger.info("[DB] Creating/verifying database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if settings.DATABASE_URL.startswith("sqlite"):
            columns = await conn.execute(text("PRAGMA table_info(users)"))
            if any(row[1] == "email" for row in columns):
                logger.info("[DB] Removing legacy users.email column from SQLite database...")
                await conn.execute(text("ALTER TABLE users RENAME TO users_old"))
                await conn.run_sync(Base.metadata.tables["users"].create)
                await conn.execute(text(
                    "INSERT INTO users (id, username, hashed_password, created_at, updated_at) "
                    "SELECT id, username, hashed_password, created_at, updated_at FROM users_old"
                ))
                await conn.execute(text("DROP TABLE users_old"))
    logger.info("[DB] Database tables ready")
