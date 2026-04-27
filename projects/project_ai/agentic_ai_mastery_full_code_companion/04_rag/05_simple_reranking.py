from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

class Score(BaseModel):
    relevance: int = Field(ge=0, le=10)

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
scorer = llm.with_structured_output(Score)

question = "What is FX volatility skew?"
docs = [
    "FX skew compares implied volatility across calls and puts.",
    "Docker packages applications in containers.",
    "LangSmith traces LLM applications.",
]

scored = []
for d in docs:
    s = scorer.invoke(f"Question: {question}\nDocument: {d}\nScore relevance from 0 to 10.")
    scored.append((s.relevance, d))

for score, doc in sorted(scored, reverse=True):
    print(score, doc)
