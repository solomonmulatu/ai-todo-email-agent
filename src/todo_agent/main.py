from contextlib import asynccontextmanager

from fastapi import FastAPI

from todo_agent.db import create_db_tables
from todo_agent.api.routes_tasks import router as task_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_tables()
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(task_router)