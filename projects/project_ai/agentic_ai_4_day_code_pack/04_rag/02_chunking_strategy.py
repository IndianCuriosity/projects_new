


##################################################################################################################################################
# This code demonstrates Text Splitting, which is the "pre-processing" phase of RAG. LLMs have limits on how much text they can read at once, and 
# vector databases perform better when information is broken down into small, meaningful pieces rather than massive documents.

# This script demonstrates document chunking, a core step in building RAG pipelines and semantic memory systems. It splits long text into smaller overlapping pieces 
# so embeddings and retrieval work better.
    # raw document → smaller semantic chunks → embed → store → retrieve accurately
##################################################################################################################################################

# 1. The RecursiveCharacterTextSplitter
    # This is widely considered the best "all-purpose" splitter in LangChain. This is LangChain’s default production splitter for RAG systems.

    # Unlike a simple splitter that might just cut text every 100 characters (potentially in the middle of a word),
    #  this splitter is "smart." It tries to split by a hierarchy of characters:
        # Paragraphs (\n\n)
        # Newlines (\n)
        # Spaces ( )
        # Characters
    # It tries to keep paragraphs and sentences together as much as possible before moving down to the next character in the list.

    # Why “recursive”? Because it tries multiple splitting strategies in order:
        # paragraph → sentence → word → character
    # It keeps meaning intact as much as possible while respecting chunk size.
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Define input text
    # This is your source document (a volatility trading note).In real systems this might be:
        # research PDFs
        # trade journals
        # macro commentary
        # policy notes
        # documentation
        # transcripts

text = """
Long gamma benefits when realized volatility exceeds implied volatility plus transaction costs.
However, theta decay can dominate if the spot market remains quiet.
Before central bank events, implied volatility often rises.
After the event, volatility can collapse quickly.
"""

# 2. Key Parameters
    # chunk_size=120: This is the maximum length (in characters) of each chunk. The splitter tries to get as close to this number as possible without 
    # breaking the hierarchy rules. embeddings work best with moderate-length semantic units, not entire documents.

    # chunk_overlap=30: This is the "secret sauce" of retrieval. It ensures that the end of Chunk 1 and the beginning of Chunk 2 share some common text.
    # Why overlap matters:
        # Without overlap:
            # important context gets cut
            # retrieval quality drops
        # With overlap:
            # semantic continuity preserved ✅

splitter = RecursiveCharacterTextSplitter(chunk_size=120, chunk_overlap=30)
# Split the text
    # Output becomes:
        # [
        #   chunk_1,
        #   chunk_2,
        #   chunk_3,
        #   ...
        # ]
    # Each chunk:
        # ≤ 120 characters
        # overlaps previous chunk by 30 characters
    
    # Overlaps ensure semantic continuity across chunks.

chunks = splitter.split_text(text)

for i, chunk in enumerate(chunks, 1):
    print(f"--- chunk {i} ---")
    print(chunk)


# 4. Trace of the Result
    # In your specific example, the text is about 230 characters long.
        # Chunk 1 will contain the first sentence and likely the start of the second.
        # Chunk 2 will start about 30 characters before Chunk 1 ended, including the end of the second sentence and the third.
        # Chunk 3 will pick up the final sentence.

# Summary: The Splitting Pipeline
    # Input: One giant string of text.
    # Logic: Look for double newlines. If a chunk is too big, look for single newlines. If still too big, look for spaces.
    # Output: A list of smaller strings that are easy for the OpenAIEmbeddings model to process accurately.

# Why chunking is critical for RAG systems

    # Embedding entire documents at once is inefficient:
        # document too long 
        # retrieval inaccurate 
        # context noisy 

    # Chunking improves:

    # Feature	                Benefit
    ----------------------------------------
    # retrieval precision	    higher
    # embedding quality	        better
    # token usage	            lower
    # context relevance	        stronger

    # So production pipeline becomes:
        # document
        # ↓
        # chunk
        # ↓
        # embed
        # ↓
        # store in Chroma
        # ↓
        # retrieve relevant chunk
        # ↓
        # inject into prompt

# Why RecursiveCharacterTextSplitter is preferred
    # Compared to naive splitting:
        # split every 120 characters
    # it instead tries:
        # paragraph break
        # sentence break
        # word boundary
        # character boundary
    # Result: clean semantic chunks, instead of half sentences  & broken meaning 




# How this fits into your Agentic AI stack
    # This splitter is typically used here:
        #     PDF loader
        #     ↓
        #     text splitter
        #     ↓
        #     embedding model
        #     ↓
        #     Chroma vector DB
        #     ↓
        #     retriever
        #     ↓
        #     LLM

    # Example in your FX-vol workflow:
        # vol surface commentary
        # ↓
        # split into regime insights
        # ↓
        # store embeddings
        # ↓
        # retrieve when agent answers skew questions

"""
>>> for i, chunk in enumerate(chunks, 1):
...     print(f"--- chunk {i} ---")
...     print(chunk)
... 
--- chunk 1 ---
Long gamma benefits when realized volatility exceeds implied volatility plus transaction costs.
--- chunk 2 ---
However, theta decay can dominate if the spot market remains quiet.
--- chunk 3 ---
Before central bank events, implied volatility often rises.
After the event, volatility can collapse quickly.




>>> chunks
['Long gamma benefits when realized volatility exceeds implied volatility plus transaction costs.', 
'However, theta decay can dominate if the spot market remains quiet.', 
'Before central bank events, implied volatility often rises.\nAfter the event, volatility can collapse quickly.']

"""