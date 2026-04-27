from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

docs = [
    Document(page_content="EURUSD skew richened after ECB.", metadata={"asset": "EURUSD", "source": "market_note"}),
    Document(page_content="USDJPY gamma rose before BOJ.", metadata={"asset": "USDJPY", "source": "market_note"}),
]

vs = Chroma.from_documents(docs, embedding=OpenAIEmbeddings(model="text-embedding-3-small"), collection_name="metadata_filter", persist_directory="./chroma_metadata_filter")

docs = vs.similarity_search("What happened to skew?", k=2, filter={"asset": "EURUSD"})
for d in docs:
    print(d.page_content, d.metadata)
