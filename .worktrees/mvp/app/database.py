from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import get_settings

settings = get_settings()

async_database_url = settings.database_url.replace(
    "postgresql://", "postgresql+asyncpg://"
)
async_engine = create_async_engine(async_database_url, echo=settings.debug)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Verify DB connectivity on startup. Schema is managed by Alembic migrations."""
    async with async_engine.begin() as conn:
        from sqlalchemy import text

        await conn.execute(text("SELECT 1"))
