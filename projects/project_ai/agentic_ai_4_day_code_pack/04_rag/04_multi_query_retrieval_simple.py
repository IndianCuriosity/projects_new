
##################################################################################################################################################
# This code implements a technique called Multi-Query Retrieval. It is a "Query Expansion" strategy designed to overcome the limitations of distance-based vector search.
# Sometimes, a user's question is phrased in a way that doesn't perfectly match the technical wording in your database. Multi-query retrieval solves 
# this by using an LLM to rewrite the question from different perspectives, increasing the chances of "hitting" the right documents.


# 1. The Multi-Query Workflow
    # Instead of searching once, the script follows this process:
        # Expansion: You pass the original question ("Explain FX skew") to the LLM.
        # Generation: The LLM generates three different ways to ask the same thing (e.g., "How do risk reversals relate to skew?", 
        # "FX market skew definition", and "Measuring volatility bias").
        # Parallel Search: The code loops through all three generated queries and performs a similarity_search for each one.
        # Deduplication: Since multiple queries might find the same document, the code uses a seen set to ensure you don't return the same info twice.

# 2. Why use this?
# Vector search (Cosine Similarity) is sensitive to specific wording.
    # Problem: If your document says "risk reversal" but the user asks for "skew," the vector distance might be slightly too far to rank it as a top result.
    # Solution: By asking the LLM to generate synonyms and related technical terms, you effectively "cast a wider net." One of the three queries is 
        # bound to use the specific terminology present in your documents

# This script implements a multi-query retrieval strategy for RAG using Chroma + embeddings + an LLM query rewriter.
    # Instead of searching once with a single query, it generates multiple semantically different search queries and merges the results to improve recall.
    # Conceptually:
        # User question
        #    ↓
        # LLM generates multiple search queries
        #    ↓
        # Run vector search for each query
        #    ↓
        # Merge unique results
        #    ↓
        # Return richer context

    # This is a production technique used in advanced RAG pipelines.

##################################################################################################################################################

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

docs = [
    Document(page_content="FX risk reversal is a measure of skew."),
    Document(page_content="Skew reflects demand imbalance between upside and downside options."),
    Document(page_content="Gamma scalping monetizes realized volatility through delta hedging."),
]

vs = Chroma.from_documents(docs, embedding=OpenAIEmbeddings(model="text-embedding-3-small"), collection_name="multi_query", persist_directory="./db_others/chroma_multi_query")

question = "Explain FX skew"

# The Expansion Step
    # This is the "Brain" of the operation. You are leveraging the LLM's linguistic knowledge to translate a simple user question into professional search terms.

queries = llm.invoke(f"Generate 3 search queries for this question: {question}. Return one per line.").content.splitlines()

# The Unique Retrieval Loop
    # This loop is essential for quality control:
        # It searches for the top 2 documents for each of the 3 queries (potential for 6 documents total).
        # The if d.page_content not in seen logic prevents the final prompt from being cluttered with redundant information.
    # Prepare deduplication containers

seen = set()
results = []
for q in queries:
    for d in vs.similarity_search(q, k=2):
        if d.page_content not in seen:
            seen.add(d.page_content)
            results.append(d)

print("Queries:", queries)
print("\nRetrieved:")

# This becomes your expanded retrieval context.
for d in results:
    print("-", d.page_content)

"""
>>> for d in results:
...     print("-", d.page_content)
... 
- FX risk reversal is a measure of skew.
- Skew reflects demand imbalance between upside and downside options.
"""


# Summary of Benefits
--------------------------------------------------------------------------------------------------------------------------
# Feature,                      Single Query RAG,                       Multi-Query RAG
# Sensitivity,                  High (sensitive to exact wording),      Low (robust against phrasing variations)
# Recall,                       Lower (might miss relevant docs),       Higher (finds more related context)
# Cost,                         1 LLM call (final),                     1 LLM call (expansion) + 1 LLM call (final)


# Why multi-query retrieval improves RAG quality
    # So context becomes richer.
    # | Feature                 | Improvement |
    # | ----------------------- | ----------- |
    # | recall                  | ↑           |
    # | coverage                | ↑           |
    # | robustness              | ↑           |
    # | hallucination reduction | ↑           |

# How this fits inside real agent pipelines

    # Production RAG architecture:

        # User question
        #    ↓
        # Query rewriting agent
        #    ↓
        # Multi-query retrieval
        #    ↓
        # Merge results
        #    ↓
        # Context injection
        #    ↓
        # LLM answer


# Trading-agent example
    # Instead of: Explain FX skew

    # multi-query might generate:
        # risk reversal definition
        # 25-delta skew interpretation
        # call-put demand imbalance FX options

    # Which retrieves:
        # surface skew mechanics
        # dealer positioning signals
        # macro hedging pressure indicators

    # This produces institution-grade retrieval quality.



# ##################################################################################################################################################
# Pro-Tip
# LangChain actually has a built-in version of this called the MultiQueryRetriever. While your manual loop is great for learning, the built-in 
# version handles the parsing and deduplication automatically in a single line of code!
##################################################################################################################################################

