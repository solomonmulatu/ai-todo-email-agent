from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from todo_agent.domain.status import TaskStatus


class TaskCreateRequest(BaseModel):
    reminder_text: str = Field(min_length=1, max_length=5000)


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reminder_text: str
    title: str
    recipient_email: str | None
    status: TaskStatus
    due_at: datetime | None
    created_at: datetime