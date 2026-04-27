from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

docs = [
    Document(page_content="A risk reversal compares implied vol of calls and puts at similar delta."),
    Document(page_content="LangGraph uses stateful nodes and edges to build robust agent workflows."),
]

vs = Chroma.from_documents(docs, embedding=OpenAIEmbeddings(model="text-embedding-3-small"), collection_name="basic_rag", persist_directory="./chroma_basic_rag")
retriever = vs.as_retriever(search_kwargs={"k": 2})
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system", "Use context only where relevant:\n{context}"),
    ("human", "{question}"),
])

q = "What is a risk reversal?"
context = "\n".join(d.page_content for d in retriever.invoke(q))
print((prompt | llm).invoke({"context": context, "question": q}).content)
