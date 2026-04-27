from fastapi import FastAPI
from pydantic import BaseModel
from langchain_openai import ChatOpenAI

# Run:
# uvicorn 10_production.01_fastapi_service:app --reload

app = FastAPI()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat(req: ChatRequest):
    response = llm.invoke(req.message)
    return {"response": response.content}
