from collections.abc import AsyncIterator
from sqlalchemy.ext.asyncio import (create_async_engine, AsyncConnection, async_sessionmaker, AsyncSession)

from src.todo_agent.config import settings
from todo_agent.domain.models import Base

if not settings.database_url:
    raise RuntimeError('Please set DATABASE_URL environment variable')
engine = create_async_engine(settings.database_url,pool_pre_ping=True)


SessionFactory= async_sessionmaker(engine,expire_on_commit=False)

async def get_session()->AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:

        yield session

async def create_db_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)