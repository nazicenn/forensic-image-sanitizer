from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker 
from sqlalchemy.orm import declarative_base 
 
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@postgres:5432/forensic_sanitizer" 
 
engine = create_async_engine(DATABASE_URL, echo=True) 
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False) 
Base = declarative_base() 
