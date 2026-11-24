from typing import Annotated

from fastapi import APIRouter, Depends
import json
from sqlalchemy.ext.asyncio import AsyncSession

from todo_agent.db import get_session
from todo_agent.domain.dto import TaskCreateRequest
from todo_agent.domain.service import DBServices
from todo_agent.llm.email_writer import EmailWriter
from todo_agent.llm.extractor import Extractor

router = APIRouter(prefix="/tasks", tags=["Tasks"])

db_services = DBServices()
extractor = Extractor()
email_writer=EmailWriter()


@router.post("/")
async def create_task(
    payload: str,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    extracted_task = await extractor.extract_task(payload)
    print(type(extracted_task))
    print(extracted_task)
    print(extracted_task["task"]["data"]["reminder_text"])

    task_data = extracted_task["task"]["data"]

    payload = TaskCreateRequest(
        reminder_text=task_data["reminder_text"],
        title=task_data["title"],
        due_at=task_data["due_date"],
    )
    task_created=await db_services.create_task(session, payload)

    email=await  email_writer.generate_email(extracted_task)


    print(email)
    return extracted_task