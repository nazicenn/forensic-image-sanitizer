from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from app.core.config import settings
from datetime import datetime, timezone
from sqlalchemy import func

# Convert postgresql:// to postgresql+asyncpg://
database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Engine with proper pool settings
def create_engine_for_env():
    """Create engine based on environment."""
    if settings.DEBUG:
        # Test ortamı için NullPool
        return create_async_engine(
            database_url,
            echo=settings.DEBUG,
            poolclass=NullPool,
            pool_pre_ping=True,
        )
    else:
        # Production ortamı için normal pool
        return create_async_engine(
            database_url,
            echo=settings.DEBUG,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,
        )

engine = create_engine_for_env()

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Get database session."""
    async with AsyncSessionLocal() as session:
        yield session


async def close_db():
    """Close database connection."""
    await engine.dispose()