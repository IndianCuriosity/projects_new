"""
RAG with Chroma:
Load documents -> embed -> retrieve -> inject into prompt.
"""
##################################################################################################################################################

# This code is a classic/minimal implementation of Retrieval-Augmented Generation (RAG). While the previous example showed "Semantic Memory" 
# (saving chat history to a database), this code shows how to provide an LLM with a "knowledge base" of external facts it wasn't originally trained on.
# Here is the step-by-step breakdown of the RAG pipeline:
# It follows the standard RAG workflow:
    # documents → embeddings → vector store → retrieval → prompt injection → LLM answer

# High-level architecture:
    # Your pipeline is:

    # User question
    #    ↓
    # Convert question → embedding
    #    ↓
    # Search vector database (Chroma)
    #    ↓
    # Retrieve relevant documents
    #    ↓
    # Inject into prompt
    #    ↓
    # LLM answers using retrieved context
# This prevents hallucinations and improves accuracy.

##################################################################################################################################################

| Component            | Role                      |
| -------------------- | ------------------------- |
| `ChatOpenAI`         | reasoning model           |
| `OpenAIEmbeddings`   | converts text → vectors   |
| `Chroma`             | vector database           |
| `Document`           | structured storage object |
| `ChatPromptTemplate` | builds LLM prompt         |


from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

# 1. Data Ingestion (The "Library"): Define documents (your knowledge base)
    # You start with a list of Document objects. Each document contains the content (the text) 
    # and metadata (labels like "topic"). Think of this as the raw material for your AI's private library.

# Each entry is stored as a Document object:
    # page_content → actual knowledge
    # metadata → optional filtering/tagging
# Metadata becomes useful later for filtering retrieval.
docs = [
    Document(page_content="FX vol skew measures demand for calls versus puts across strikes.", metadata={"topic": "fx_vol"}),
    Document(page_content="A risk reversal is long one option and short another option with different strikes.", metadata={"topic": "fx_options"}),
    Document(page_content="LangGraph represents agent workflows as stateful graphs with nodes and edges.", metadata={"topic": "agentic_ai"}),
]

# Initialize embedding model
    # This converts text like: "What is FX vol skew?" into: [0.023, -0.441, 0.771, ...]. These vectors allow semantic similarity search.
    # Important idea: Embeddings enable meaning-based retrieval, not keyword matching

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# 2. Vectorization & Storage ( Embed docs, store vectors and persist locally)
    # The code takes those documents and:
    #     Embeds them: Converts the text into numerical vectors using text-embedding-3-small.
    #     Indexes them: Stores them in Chroma (your vector database) so they can be searched lightning-fast.

vectorstore = Chroma.from_documents(
    docs,
    embedding=embeddings,
    collection_name="rag_demo",
    persist_directory="./db_others/chroma_rag_demo",
)

# 3. The Retriever (The "Librarian"): Create retriever interface
    # The retriever is a specialized interface for the database. By setting k: 2, 
    # you are telling the system: "When I ask a question, find the two most similar documents from my library."
    # This wraps Chroma into a simple search tool.
        
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

# Define prompt template: This ensures the LLM answers only using retrieved knowledge.
# Actual prompt becomes:
#     System: Answer using the context below.
#     Context: FX vol skew measures demand for calls versus puts across strikes.
#     User: What is FX vol skew?

# This reduces hallucination risk significantly.

prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer using the context below.\n\nContext:\n{context}"),
    ("human", "{question}")
])

# Initialize LLM

# This model:
    # reads retrieved context
    # generates final answer
    # stays deterministic (temperature=0)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 4. The RAG Chain logic: This function executes the full retrieval pipeline.
    # The rag_answer function executes the three core stages of RAG:
        # Retrieve: retriever.invoke(question) looks up the two most relevant documents. If you ask about "FX vol skew," it will ignore the LangGraph 
        # document and grab the FX-related ones.
            # Internally:
                # embed(question)
                # ↓
                # compare against stored vectors
                # ↓
                # return closest matches
            # Example output:
                # [
                # Document("FX vol skew measures demand for calls versus puts...")
                # ]
        # Augment: It combines the retrieved text into a single string called context.
            # Transforms retrieved docs into:
                # FX vol skew measures demand for calls versus puts across strikes.
            # This becomes prompt input.
        # # Generate: It injects that context into the prompt. The LLM isn't answering from its own memory; it is essentially "reading" the context you
            # Pipeline:
                
            # Example response:
                # FX vol skew reflects the relative demand for calls versus puts across different strikes, indicating directional hedging pressure in FX options markets.
        #  just gave it and summarizing it for you.

def rag_answer(question: str):
    retrieved = retriever.invoke(question)                                              # retrieve relevant documents
    context = "\n".join(d.page_content for d in retrieved)                              # build context string
    return (prompt | llm).invoke({"question": question, "context": context}).content    # call LLM with retrieved context
    
    # Run the pipeline
        # Execution flow:
            # User question
            # ↓
            # Embedding created
            # ↓
            # Chroma searched
            # ↓
            # Relevant doc retrieved
            # ↓
            # Context injected into prompt
            # ↓
            # LLM generates grounded answer

print(rag_answer("What is FX vol skew?"))


# Feature               Semantic Memory (Previous)               RAG (This Code)
# ------------------------------------------------------------------------------------------------
# Source                Previous Chat History                    External Facts / Documents
# Purpose               To remember the user.                    To provide expertise.
# Updating              Done automatically after every chat.     Usually done via a batch upload of files.

# Summary of the Workflow
    # Ask Question: "What is FX vol skew?"
    # Search DB: Find documents that talk about "skew" and "FX."
    # Build Prompt: "System: Use this info: [FX vol skew measures...] Human: What is FX vol skew?"
    # Final Output: The LLM gives a grounded, factual answer based specifically on your provided documents.

# Why this is a real RAG system (not just vector search)
#     Because it performs all four steps:

#         Step	                Component
#         ----------------------------------------
#         store knowledge	        Chroma
#         embed text	            OpenAIEmbeddings
#         retrieve context	    retriever
#         inject into prompt	    ChatPromptTemplate



# Why this matters for Agentic AI mastery
    # This exact pattern powers:

        # research assistants
        # trading copilots
        # documentation bots
        # knowledge-aware agents
        # LangGraph retrieval nodes
        # long-term memory systems

# In your quant workflow context, the same structure becomes:

    # surface dynamics notes
    # ↓
    # retriever
    # ↓
    # vol regime classifier
    # ↓
    # strategy suggestion agent

# what you built here is the core retrieval engine behind modern agent systems.


"""
>>> print(rag_answer("What is FX vol skew?"))
FX vol skew refers to the difference in implied volatility between options with different strikes in the foreign exchange market. It measures the demand for 
call options versus put options across various strike prices. A positive skew indicates higher demand for calls, while a negative skew suggests higher demand 
for puts. This skew can provide insights into market sentiment and expectations regarding future currency movements.

"""