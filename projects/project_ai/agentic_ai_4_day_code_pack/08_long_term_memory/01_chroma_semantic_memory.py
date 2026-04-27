"""
Semantic long-term memory with Chroma:
Save durable memories and retrieve relevant ones later.
"""

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

memory_store = Chroma(
    collection_name="semantic_memory",
    embedding_function=embeddings,
    persist_directory="./chroma_semantic_memory",
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "Use relevant memories if helpful:\n{memories}"),
    ("human", "{input}")
])

def save_memory(text: str, metadata=None):
    memory_store.add_texts([text], metadatas=[metadata or {}])

def retrieve_memories(query: str, k: int = 3):
    docs = memory_store.similarity_search(query, k=k)
    return "\n".join(d.page_content for d in docs)

def chat(user_input: str):
    memories = retrieve_memories(user_input)
    response = (prompt | llm).invoke({"input": user_input, "memories": memories})
    save_memory(f"User: {user_input}\nAssistant: {response.content}", {"type": "conversation"})
    return response.content

save_memory("User prefers quant finance and FX volatility examples.", {"type": "preference"})
print(chat("Teach me LangGraph with an example relevant to my background."))
