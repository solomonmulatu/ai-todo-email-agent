from collections.abc import AsyncIterator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import ( create_async_engine, AsyncConnection)

from src.todo_agent.config import settings

if not settings.database_url:
    raise RuntimeError('Please set DATABASE_URL environment variable')
engine = create_async_engine(settings.database_url,pool_pre_ping=True)

async def get_connection()->AsyncIterator[AsyncConnection]:
    async with engine.connect() as conn:
        await conn.execute(
            text("SET default_transaction_read_only = on")
        )
        await conn.execute(
            text("SET statement_timeout = '5s'")
        )
        yield conn