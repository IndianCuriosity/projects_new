from typing import Literal
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

class Route(BaseModel):
    route: Literal["code", "finance", "general"]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
router = llm.with_structured_output(Route)

prompts = {
    "code": ChatPromptTemplate.from_messages([("system", "You are a Python tutor."), ("human", "{input}")]),
    "finance": ChatPromptTemplate.from_messages([("system", "You are a macro quant assistant."), ("human", "{input}")]),
    "general": ChatPromptTemplate.from_messages([("system", "You are a general assistant."), ("human", "{input}")]),
}

def route_query(input_data):
    selector = input_data["destination"].route
    original_input = input_data["original_input"]
    chain = prompts.get(selector, prompts["general"]) | llm
    return chain.invoke({"input": original_input})

full_chain = {"destination": router, "original_input": RunnablePassthrough()} | RunnableLambda(route_query)

result = full_chain.invoke("Write Python code for rolling FX volatility.")
print(result.content)
