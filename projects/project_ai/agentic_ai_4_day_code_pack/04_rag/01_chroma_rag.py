"""
RAG with Chroma:
Load documents -> embed -> retrieve -> inject into prompt.
"""

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

docs = [
    Document(page_content="FX vol skew measures demand for calls versus puts across strikes.", metadata={"topic": "fx_vol"}),
    Document(page_content="A risk reversal is long one option and short another option with different strikes.", metadata={"topic": "fx_options"}),
    Document(page_content="LangGraph represents agent workflows as stateful graphs with nodes and edges.", metadata={"topic": "agentic_ai"}),
]

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

vectorstore = Chroma.from_documents(
    docs,
    embedding=embeddings,
    collection_name="rag_demo",
    persist_directory="./chroma_rag_demo",
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer using the context below.\n\nContext:\n{context}"),
    ("human", "{question}")
])

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def rag_answer(question: str):
    retrieved = retriever.invoke(question)
    context = "\n".join(d.page_content for d in retrieved)
    return (prompt | llm).invoke({"question": question, "context": context}).content

print(rag_answer("What is FX vol skew?"))
