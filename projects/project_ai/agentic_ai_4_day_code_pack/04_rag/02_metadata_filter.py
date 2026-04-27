"""
Metadata filtering:
Useful when docs have asset class, date, source, region, strategy, etc.
"""

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

docs = [
    Document(page_content="EURUSD 1M skew richened after ECB event.", metadata={"asset": "EURUSD", "type": "market"}),
    Document(page_content="USDJPY gamma rose before BOJ meeting.", metadata={"asset": "USDJPY", "type": "market"}),
    Document(page_content="LangSmith traces help debug agents.", metadata={"asset": "AI", "type": "engineering"}),
]

vectorstore = Chroma.from_documents(
    docs,
    embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
    collection_name="metadata_demo",
    persist_directory="./chroma_metadata_demo",
)

retriever = vectorstore.as_retriever(
    search_kwargs={
        "k": 2,
        "filter": {"asset": "EURUSD"}
    }
)

for doc in retriever.invoke("What happened to skew?"):
    print(doc.page_content, doc.metadata)
