from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

docs = [
    Document(page_content="FX risk reversal is a measure of skew."),
    Document(page_content="Skew reflects demand imbalance between upside and downside options."),
    Document(page_content="Gamma scalping monetizes realized volatility through delta hedging."),
]

vs = Chroma.from_documents(docs, embedding=OpenAIEmbeddings(model="text-embedding-3-small"), collection_name="multi_query", persist_directory="./chroma_multi_query")

question = "Explain FX skew"
queries = llm.invoke(f"Generate 3 search queries for this question: {question}. Return one per line.").content.splitlines()

seen = set()
results = []
for q in queries:
    for d in vs.similarity_search(q, k=2):
        if d.page_content not in seen:
            seen.add(d.page_content)
            results.append(d)

print("Queries:", queries)
print("\nRetrieved:")
for d in results:
    print("-", d.page_content)
