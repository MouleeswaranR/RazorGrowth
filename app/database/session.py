from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.config.settings import settings

def _get_async_database_url(raw_url: str) -> str:
    """Ensures database connection URL uses the asyncpg driver."""
    if raw_url.startswith("postgres://"):
        raw_url = raw_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif raw_url.startswith("postgresql://"):
        raw_url = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    # Convert sslmode parameter to ssl for asyncpg compatibility
    if "sslmode=" in raw_url:
        raw_url = raw_url.replace("sslmode=require", "ssl=require").replace("sslmode=prefer", "ssl=prefer")
    if "&channel_binding=require" in raw_url:
        raw_url = raw_url.replace("&channel_binding=require", "")
    return raw_url


from sqlalchemy.pool import NullPool

db_url = _get_async_database_url(settings.database_url)

engine = create_async_engine(
    db_url,
    echo=False,
    future=True,
    poolclass=NullPool,
)


async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

AsyncSessionLocal = async_session_factory


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides an asynchronous database session context for request handlers."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
