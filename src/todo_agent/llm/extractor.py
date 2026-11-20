from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from todo_agent.config import settings
from todo_agent.llm.prompts import  TASK_EXTRACTOR_SYSTEM_PROMPT


class Extractor:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_chat_model,
            temperature=0
        )

    async def extract_task(self, task: str):
        response = await self.llm.ainvoke(
            [
                SystemMessage(content=TASK_EXTRACTOR_SYSTEM_PROMPT),
                HumanMessage(content=f"""Task: {task}""")
            ]
        )

        extracted_task = response.content.strip()

        if extracted_task == "UNANSWERABLE":
            return {"result": "ERROR", "message": "That Task cannot be created."}


        return{
            "result":"SUCCESS",
            "task":extracted_task,
        }

