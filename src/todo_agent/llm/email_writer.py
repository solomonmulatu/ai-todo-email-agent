from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from todo_agent.config import settings
from todo_agent.llm.prompts import TASK_EXTRACTOR_SYSTEM_PROMPT, EMAIL_SYSTEM_PROMPT


class EmailDraft(BaseModel):
    subject: str = Field(description="Email subject")
    body: str = Field(description="Email body")

class EmailWriter:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_chat_model,
            temperature=0
        )

    async def generate_email(self, task: dict):
        response = await self.llm.with_structured_output(
            EmailDraft
        ).ainvoke(
            [
                SystemMessage(content=EMAIL_SYSTEM_PROMPT),
                HumanMessage(content=f"""Task: {task}""")
            ]
        )

        generated_email = response



        return generated_email

