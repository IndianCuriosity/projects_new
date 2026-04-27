from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

docs = [
    Document(page_content="Long gamma profits when realized vol exceeds implied vol plus costs.", metadata={"source": "note_1"}),
    Document(page_content="Event vol can collapse after the catalyst passes.", metadata={"source": "note_2"}),
]

vs = Chroma.from_documents(docs, embedding=OpenAIEmbeddings(model="text-embedding-3-small"), collection_name="rag_citations", persist_directory="./chroma_rag_citations")
retrieved = vs.similarity_search("Should I buy gamma before an event?", k=2)

context = "\n".join(f"[{i}] source={d.metadata['source']}: {d.page_content}" for i, d in enumerate(retrieved, 1))

prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer with source numbers like [1], [2]. Context:\n{context}"),
    ("human", "{question}"),
])

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
print((prompt | llm).invoke({"context": context, "question": "Should I buy gamma before an event?"}).content)
