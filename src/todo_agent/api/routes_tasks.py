from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from todo_agent.db import get_session, create_db_tables
from todo_agent.domain.dto import TaskResponse, TaskCreateRequest
from todo_agent.domain.service import DBServices

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_tables()
    yield

app = FastAPI(lifespan=lifespan)

db_services=DBServices()



@app.post("/tasks", response_model=TaskResponse)
async def create_task(
    payload: TaskCreateRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    print(payload)

    return await db_services.create_task(session, payload)