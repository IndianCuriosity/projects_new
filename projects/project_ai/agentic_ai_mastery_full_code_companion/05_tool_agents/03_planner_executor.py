from pydantic import BaseModel
from typing import List
from langchain_openai import ChatOpenAI

class Plan(BaseModel):
    steps: List[str]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
planner = llm.with_structured_output(Plan)

plan = planner.invoke("Plan how to research an FX vol trade idea using data, RAG, and risk checks.")
for i, step in enumerate(plan.steps, 1):
    print(i, step)
