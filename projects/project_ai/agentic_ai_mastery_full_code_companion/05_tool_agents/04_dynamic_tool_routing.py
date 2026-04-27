from typing import Literal
from pydantic import BaseModel
from langchain_openai import ChatOpenAI

class ToolRoute(BaseModel):
    tool: Literal["calculator", "retriever", "database", "none"]
    reason: str

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
router = llm.with_structured_output(ToolRoute)

for q in ["Calculate annualized vol from returns.", "Find my notes about LangGraph.", "Query EURUSD surface history from DB.", "Explain what an agent is."]:
    print(q, "=>", router.invoke(q))
