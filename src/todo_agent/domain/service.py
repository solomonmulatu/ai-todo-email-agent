from sqlalchemy.ext.asyncio import AsyncSession

from todo_agent.domain.dto import TaskCreateRequest
from todo_agent.domain.models import Task

async def create_task(session: AsyncSession,payload:TaskCreateRequest) -> Task:
    task= Task(reminder_text=payload.reminder_text)
    session.add(task)
    await session.flush()
    return task