"""
FastAPI service wrapper.

Run from the project root:
uvicorn 10_production.01_fastapi_agent_service:app --reload

Then POST to:
http://127.0.0.1:8000/chat
"""

from fastapi import FastAPI
from pydantic import BaseModel
from langchain_openai import ChatOpenAI

app = FastAPI()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat(req: ChatRequest):
    response = llm.invoke(req.message)
    return {"response": response.content}
