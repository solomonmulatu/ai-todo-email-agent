from sqlalchemy.ext.asyncio import AsyncSession

from todo_agent.domain.dto import TaskCreateRequest
from todo_agent.domain.models import Task


class DBServices:
    def __init__(self):
        pass

    async def create_task(self,session: AsyncSession, payload: TaskCreateRequest) -> Task:
        task = Task(reminder_text=payload.reminder_text,title="Test Title")
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task

