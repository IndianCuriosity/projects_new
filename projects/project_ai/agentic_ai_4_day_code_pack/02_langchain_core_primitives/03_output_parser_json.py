from pydantic import BaseModel
from langchain_openai import ChatOpenAI

class Concept(BaseModel):
    name: str
    definition: str
    when_to_use: str

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured = llm.with_structured_output(Concept)
print(structured.invoke("Define LangGraph."))


"""
>>> print(structured.invoke("Define LangGraph."))
name='LangGraph' definition='LangGraph is a framework designed for building and managing language models and their interactions in a graph-based structure,
 allowing for efficient querying, reasoning, and manipulation of language data.' when_to_use='Use LangGraph when you need to integrate multiple language models, 
 manage complex relationships between language data, or require advanced querying capabilities for natural language processing tasks.'
"""