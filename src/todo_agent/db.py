from collections.abc import AsyncIterator
from sqlalchemy.ext.asyncio import (create_async_engine, AsyncConnection, async_sessionmaker, AsyncSession)

from src.todo_agent.config import settings

if not settings.database_url:
    raise RuntimeError('Please set DATABASE_URL environment variable')
engine = create_async_engine(settings.database_url,pool_pre_ping=True)


SessionFactory= async_sessionmaker(engine,expire_on_commit=False)

async def get_session()->AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:

        yield session