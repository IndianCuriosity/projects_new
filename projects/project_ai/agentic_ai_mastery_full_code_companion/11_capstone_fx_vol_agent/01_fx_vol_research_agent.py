import math
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool

@tool
def realized_vol(returns_csv: str) -> float:
    """Calculate annualized realized volatility from comma-separated daily returns."""
    rs = [float(x.strip()) for x in returns_csv.split(",")]
    mean = sum(rs) / len(rs)
    var = sum((x - mean) ** 2 for x in rs) / (len(rs) - 1)
    return math.sqrt(var) * math.sqrt(252)

docs = [
    Document(page_content="Long gamma benefits from realized volatility exceeding implied volatility plus hedging costs."),
    Document(page_content="FX risk reversals indicate skew demand. Rich call skew can reflect upside hedging demand."),
    Document(page_content="Before central bank events, implied vol often rises; post-event theta and vol crush are major risks."),
]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

vectorstore = Chroma.from_documents(docs, embedding=embeddings, collection_name="fx_vol_capstone", persist_directory="./chroma_fx_vol_capstone")
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an FX volatility research agent.\nContext:\n{context}\nTool results:\n{tool_results}"),
    ("human", "{question}"),
])

def research(question: str, tool_results: str = ""):
    docs = retriever.invoke(question)
    context = "\n".join(d.page_content for d in docs)
    return (prompt | llm).invoke({"question": question, "context": context, "tool_results": tool_results}).content

if __name__ == "__main__":
    rv = realized_vol.invoke({"returns_csv": "0.005,-0.004,0.006,-0.003,0.004"})
    print(research("Should I buy EURUSD gamma before an ECB event?", tool_results=f"Recent annualized RV estimate: {rv:.2%}"))
