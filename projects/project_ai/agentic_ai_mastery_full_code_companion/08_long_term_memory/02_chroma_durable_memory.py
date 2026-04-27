from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

vs = Chroma(collection_name="durable_memory", embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"), persist_directory="./chroma_durable_memory")

vs.add_texts(
    ["User wants Agentic AI mastery in 4 days.", "User prefers FX vol examples."],
    metadatas=[{"type": "goal"}, {"type": "preference"}],
)

for d in vs.similarity_search("What does the user want to learn?", k=2):
    print(d.page_content, d.metadata)
