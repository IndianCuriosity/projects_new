from pydantic import BaseModel
from langchain_openai import ChatOpenAI

class Concept(BaseModel):
    name: str
    definition: str
    when_to_use: str

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured = llm.with_structured_output(Concept)
print(structured.invoke("Define LangGraph."))
