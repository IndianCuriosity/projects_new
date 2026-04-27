from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
emb = OpenAIEmbeddings(model="text-embedding-3-small")

vs = Chroma(collection_name="semantic_memory_demo", embedding_function=emb, persist_directory="./chroma_semantic_memory_demo")

def save_memory(text):
    vs.add_texts([text])

def recall(query, k=3):
    docs = vs.similarity_search(query, k=k)
    return "\n".join(d.page_content for d in docs)

prompt = ChatPromptTemplate.from_messages([
    ("system", "Relevant memories:\n{memory}"),
    ("human", "{input}"),
])

def chat(user_input):
    memory = recall(user_input)
    response = (prompt | llm).invoke({"memory": memory, "input": user_input})
    save_memory(f"User: {user_input}\nAssistant: {response.content}")
    return response.content

save_memory("User specializes in FX volatility and wants quant-focused examples.")
print(chat("Teach me memory in LangChain."))
