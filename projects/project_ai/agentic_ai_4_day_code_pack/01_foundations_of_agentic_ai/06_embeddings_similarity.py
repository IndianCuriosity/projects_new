
####################################################################################
#This code is a concise demonstration of Semantic Search (the core technology behind RAG). Instead of searching for exact words (like Ctrl+F), 
# it uses Embeddings to find pieces of text that have similar meanings.
#This script shows how semantic search with embeddings works under the hood. It converts text into vectors, compares them using cosine similarity, 
# and ranks which sentence is closest in meaning to a query.

# Embeddings are the backbone of:

# RAG systems
# vector databases (Chroma, FAISS)
# semantic memory
# retrieval agents


# Why this matters for Agentic AI
# This exact logic powers:

# RAG retrieval
#     query → embedding → nearest documents
# semantic memory recall
#     "What does user trade?"
#     returns: "User trades FX volatility"

# vector databases like Chroma
#     Internally they do:

#     cosine(query, doc_vector)

#     millions of times efficiently

####################################################################################

########################################################################################################################################################################
## Key Takeaway
# This is exactly how a Vector Database works. It transforms the world into math so that an AI can "calculate" which information is most relevant to your question
########################################################################################################################################################################

import numpy as np
from langchain_openai import OpenAIEmbeddings # OpenAIEmbeddings → converts text into numerical vectors (embeddings)

# 1. Generating the Embeddings
# The code uses OpenAI's text-embedding-3-small model.
# What it does: It turns human language into a long list of numbers (a vector).
# The Magic: In this numerical space, sentences with similar financial concepts (like "EURUSD" and "FX options") are placed physically close to each other, 
# even if they don't share the same words.

emb = OpenAIEmbeddings(model="text-embedding-3-small") # Initialize embedding model

# This model converts text into vectors like: [0.021, -0.338, 0.774, ...]
    # Each sentence becomes a point in semantic space 📐
    # Similar meaning → vectors close together
    # Different meaning → vectors far apart

# 2. The Vector Space
# You have three distinct "documents":
# Text A: About EURUSD skew (Finance).
# Text B: About USDJPY gamma (Finance).
# Text C: About LangGraph (Technology).

# Example dataset: vector database entries (stored documents)
texts = [
    "EURUSD skew richened after ECB event",
    "USDJPY gamma rose before BOJ",
    "LangGraph is a state machine for agents",
]

# Convert documents into embeddings: Each sentence becomes a high-dimensional numeric vector (usually ~1536 dimensions).
# [
#   vector(text1),
#   vector(text2),
#   vector(text3)
# ]

vectors = emb.embed_documents(texts)

# Convert search query into embedding: Now the query is also a vector:

# vector("FX options skew")
# So comparison becomes: vector(query) vs vector(document)
# instead of: string vs string
# This enables semantic matching, not keyword matching.

query_vec = emb.embed_query("FX options skew")


# 3. Measuring Similarity (Cosine Similarity)
# The cosine(a, b) function is the mathematical "ruler" used to measure the distance between the query and your texts.

# The Dot Product (a @ b): Measures how much the two vectors point in the same direction.
# The Norms: This "normalizes" the vectors so that the length of the sentence doesn't affect the score—only the angle between them matters.
# The Result: A score of 1.0 means the meanings are identical; 0.0 means they are completely unrelated. negative have opposite meaning

# This measures how similar two vectors are.
# Formula: similarity = a * b /||a|| ||b||


def cosine(a, b):
    a, b = np.array(a), np.array(b)
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))

# 4. Ranking the Results
# The code embeds your query: "FX options skew". It then compares this query vector to every text in your list and sorts them by the highest score.

# Compute similarity scores
# This calculates
# similarity(query, text1)
# similarity(query, text2)
# similarity(query, text3)

scores = [(text, cosine(query_vec, vec)) for text, vec in zip(texts, vectors)]

# Ranks results from most relevant → least relevant. So the closest semantic match appears first.
for text, score in sorted(scores, key=lambda x: x[1], reverse=True):
    print(round(score, 4), text)


""" 
.5164 EURUSD skew richened after ECB event
0.347 USDJPY gamma rose before BOJ
0.1085 LangGraph is a state machine for agents
 """

# Why the output looks the way it does:
    # When you run this, you'll see a result similar to this:

# ~0.5164+ "EURUSD skew richened after ECB event" (Highest, because "skew" and "FX" match perfectly).

# ~0.347+ "USDJPY gamma rose before BOJ" (Medium, because it's still about FX options/volatility).

# ~0.1085+ "LangGraph is a state machine for agents" (Lowest, because coding is conceptually far from FX markets).

################################################################################################################################
# Trading-specific intuition

# Your example works because embeddings capture concept similarity, not just words.

# Example:

# Query:

# FX options skew

# Matches:

# EURUSD skew richened after ECB event

# even though the words are not identical.

# That’s why embeddings outperform keyword search for:

# vol surface notes
# trade journals
# research logs
# macro commentary retrieval
# agent memory systems
#############################################################################################################################