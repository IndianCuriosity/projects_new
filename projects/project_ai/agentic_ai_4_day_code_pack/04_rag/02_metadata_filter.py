"""
Metadata filtering:
Useful when docs have asset class, date, source, region, strategy, etc.
"""

##################################################################################################################################################
# This code demonstrates Self-Querying or Metadata Filtering in a vector database. While standard RAG searches through the text of documents, this approach allows you 
# to "narrow the search" using specific attributes (like asset type or department) before the AI even begins looking at the meanings of the words.

##################################################################################################################################################
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
# 1. The Power of Metadata
    # In your docs list, each Document has two parts:
        # page_content: The actual sentence the AI reads.
        # metadata: A dictionary of hidden labels (asset, type).
    # These labels are not used by the embedding model to create the vector, but they are stored alongside the vector in ChromaDB as indexable fields.

docs = [
    Document(page_content="EURUSD 1M skew richened after ECB event.", metadata={"asset": "EURUSD", "type": "market"}),
    Document(page_content="USDJPY gamma rose before BOJ meeting.", metadata={"asset": "USDJPY", "type": "market"}),
    Document(page_content="LangSmith traces help debug agents.", metadata={"asset": "AI", "type": "engineering"}),
]

vectorstore = Chroma.from_documents(
    docs,
    embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
    collection_name="metadata_demo",
    persist_directory="./db_others/chroma_metadata_demo",
)
# 2. The Filtered Retriever
    # The "magic" is in the search_kwargs: When you call retriever.invoke(), ChromaDB does not search all three documents. Instead, it performs a Boolean Filter first:
        # Filter Step: "Show me only documents where asset == 'EURUSD'." (This immediately discards the USDJPY and LangSmith documents).
        # Search Step: "Of the remaining documents, which 2 are most similar to 'What happened to skew?'"

retriever = vectorstore.as_retriever(
    search_kwargs={
        "k": 2,
        "filter": {"asset": "EURUSD"}
    }
)

# 4. Code Breakdown: Manual vs. Retriever
    # You have a commented-out line:
        # # docs_retrieved = vectorstore.similarity_search(...)
    # vectorstore.similarity_search: This is a direct call to the database. It's useful for one-off debugging.
    # retriever.invoke: This is the "LangChain Way." By turning the vectorstore into a retriever object, you can plug it into a 
    # larger chain (prompt | llm) later without changing your code structure.

docs_retrieved = retriever.invoke("What happened to skew?")
#docs_retrieved = vectorstore.similarity_search("What happened to skew?", k=2, filter={"asset": "EURUSD"})


for doc in docs_retrieved:
    print(doc.page_content, doc.metadata)

"""
>>> for doc in docs_retrieved:
...     print(doc.page_content, doc.metadata)
... 
EURUSD 1M skew richened after ECB event. {'asset': 'EURUSD', 'type': 'market'}
>>> 

"""
# Summary: The Retrieval Flow
    # Query arrives: "What happened to skew?"
    # Filter applied: Index narrowed down to EURUSD documents only.
    # Similarity Search: The query is compared against the filtered subset.
    # Result: Only the "EURUSD 1M skew richened..." document is returned.




# 3. Why use Metadata Filtering?
    # Without the filter, if you asked about "volatility," the AI might return the USDJPY document as the top result. 
    # By applying the filter, you ensure that the AI only looks at EURUSD data, even if the USDJPY document was "mathematically" more similar to your query.
    # Common Use Cases:
        # Multi-tenancy: Ensuring a user only searches their own files ("filter": {"user_id": "123"}).
        # Time-boxing: Searching only for reports from a specific year ("filter": {"year": 2024}).
        # Domain Specificity: In your case, isolating FX market types from AI engineering notes.

# Why metadata filtering matters in Agentic AI systems
    # Without filtering:
        # skew query → returns EURUSD + USDJPY + AI engineering docs
    # With filtering:
        # skew query + asset=EURUSD → returns only EURUSD docs
    # This dramatically improves relevance.


# Real trading-agent applications
    # Example filters in production:
        # Asset filtering
            # filter={"asset": "EURUSD"}
        # Strategy filtering
            # filter={"strategy": "long_gamma"}
        # Regime filtering
            # filter={"regime": "pre_event"}
        # Data source filtering
            # filter={"source": "research_notes"}


# How this fits inside a real FX-vol research agent
# Pipeline becomes:
    # User: explain skew move
    # ↓
    # detect asset = EURUSD
    # ↓
    # retrieve only EURUSD notes
    # ↓
    # inject into prompt
    # ↓
    # LLM explains move
# Instead of:
    # retrieve random cross-asset commentary
# This is essential for building accurate multi-asset quant copilots.
    

# Advanced Metadata Filtering
----------------------------------------
# In LangChain and ChromaDB, you aren't limited to simple "equals" matches. You can use logical operators (like $and, $or) and comparison operators (like $ne for "not equal", $gt for "greater than", etc.) to create complex queries.

# To find all documents where the asset is not engineering, you would modify your filter like this:

# Python
# # 1. "Not Equal" filter
# retriever = vectorstore.as_retriever(
#     search_kwargs={
#         "filter": {"type": {"$ne": "engineering"}}
#     }
# )

# # 2. Logical "AND" filter (e.g., Market data that is NOT USDJPY)
# retriever = vectorstore.as_retriever(
#     search_kwargs={
#         "filter": {
#             "$and": [
#                 {"type": {"$eq": "market"}},
#                 {"asset": {"$ne": "USDJPY"}}
#             ]
#         }
#     }
# )
# Why this is a "Power User" Move
# When your vector database grows to thousands of documents, even the best embedding models can get "confused" by similar-sounding text. Metadata filtering acts as a hard constraint that sits on top of the fuzzy math of embeddings.

# Integrating with an LLM (The "Self-Query" Concept)
# The ultimate version of this is a Self-Querying Retriever. Instead of you hardcoding {"asset": "EURUSD"} in Python, you give the LLM a description of your metadata fields.

# If a user asks: "What happened to the EURUSD market yesterday?", the LLM is smart enough to:

# Extract the filter: {"asset": "EURUSD", "type": "market"}

# Extract the search query: "What happened yesterday?"

# Run the combined request automatically.

# This transforms your RAG system from a basic search tool into a sophisticated "Analyst" that knows exactly where to look in the files.

# Would you like to see the code for a Self-Querying Retriever that can translate natural language into these metadata filters?