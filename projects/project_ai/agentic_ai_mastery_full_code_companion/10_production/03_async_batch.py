import asyncio
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

async def ask(q):
    msg = await llm.ainvoke(q)
    return msg.content

async def main():
    questions = [
        "Explain RAG briefly.",
        "Explain LangGraph briefly.",
        "Explain LangSmith briefly.",
    ]
    results = await asyncio.gather(*(ask(q) for q in questions))
    for r in results:
        print("---")
        print(r)

asyncio.run(main())
