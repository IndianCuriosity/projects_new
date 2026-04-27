"""
Planner-executor pattern:
Planner creates steps. Executor executes them.
"""

from typing import List
from pydantic import BaseModel
from langchain_openai import ChatOpenAI

class Plan(BaseModel):
    steps: List[str]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
planner = llm.with_structured_output(Plan)

task = "Build a small FX vol research assistant using RAG and memory."

plan = planner.invoke(f"Create a 5-step implementation plan for: {task}")
print("PLAN")
for i, step in enumerate(plan.steps, 1):
    print(i, step)
