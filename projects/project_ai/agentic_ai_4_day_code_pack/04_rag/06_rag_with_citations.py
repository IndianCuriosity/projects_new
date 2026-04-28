

##################################################################################################################################################
# This code implements RAG with Source Attribution. While standard RAG provides an answer, this version forces the AI to "cite its sources," 
# making the response verifiable and reducing the chance of hallucination.

# citations

# This script demonstrates a RAG pipeline with citations, meaning the model answers a question using retrieved documents and explicitly references their 
# sources like [1], [2]. This is a common production pattern for research assistants, trading copilots, and audit-traceable agent systems.

# Conceptually:
    # documents → embeddings → vector search → numbered context → prompt with citation instruction → grounded answer with sources

##################################################################################################################################################


from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

# 1. The Metadata Source
    # In your document list, each Document has a metadata dictionary containing a source key (e.g., "note_1").
    # This metadata is stored in the Chroma database alongside the text. When you retrieve a document, the AI also "remembers" where it came from.
    # This metadata becomes the citation label later.
docs = [
    Document(page_content="Long gamma profits when realized vol exceeds implied vol plus costs.", metadata={"source": "note_1"}),
    Document(page_content="Event vol can collapse after the catalyst passes.", metadata={"source": "note_2"}),
]

vs = Chroma.from_documents(docs, embedding=OpenAIEmbeddings(model="text-embedding-3-small"), collection_name="rag_citations", persist_directory="./db_others/chroma_rag_citations")


# Retrieve relevant documents
    # Pipeline:  question → embedding → similarity search → return top 2 docs
    # Likely retrieved:
        # [1] Long gamma profits when realized vol exceeds implied vol plus costs
        # [2] Event vol can collapse after catalyst passes

    # Both are relevant to event gamma trading decisions.


retrieved = vs.similarity_search("Should I buy gamma before an event?", k=2)

# 2. Manual Context Formatting (The "Citation" Logic): Build citation-aware context string
    # This is the most critical part of the script. Instead of just dumping text into the prompt, you are building a structured string:
        # Index ([i]): Assigns a simple number (1, 2, 3...) to each document.

        # Metadata Injection: Explicitly adds the source name into the text the AI reads.

        # The Result: The AI sees a list like:

            # [1] source=note_1: Long gamma profits when...
            # [2] source=note_2: Event vol can collapse after...

context = "\n".join(f"[{i}] source={d.metadata['source']}: {d.page_content}" for i, d in enumerate(retrieved, 1))

# 3. The Instruction Prompt : Create citation-aware prompt template
    # By giving the AI a specific format to follow in the SystemMessage, you are effectively giving it a "style guide." It now knows that for every
    # fact it states, it must reference the corresponding bracketed number from the context.


    # This instructs the model:
        # Use context
        # Include citation numbers
        # Ground your answer

    # Example final prompt sent to model:
        # System:
        # Answer with source numbers like [1], [2].

        # Context:
        # [1] source=note_1: Long gamma profits when realized vol exceeds implied vol plus costs.
        # [2] source=note_2: Event vol can collapse after the catalyst passes.

        # User:
        # Should I buy gamma before an event?


prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer with source numbers like [1], [2]. Context:\n{context}"),
    ("human", "{question}"),
])

# Initialize LLM
    # Used here to:
        # read retrieved context
        # generate grounded explanation
        # include citations

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0) # Temperature = 0 improves consistency.


# Run the RAG pipeline
    # Execution flow:

        # retrieve docs
        # ↓
        # format numbered context
        # ↓
        # inject into prompt
        # ↓
        # LLM generates cited answer

    # Example output:
        # Buying gamma before an event can be attractive because realized volatility may exceed implied volatility if the move is large [1]. 
        # However, implied volatility often drops quickly after the event passes, which can offset gains if the move is smaller than expected [2].
    # Notice:
        # [1] and [2] citations included automatically


print((prompt | llm).invoke({"context": context, "question": "Should I buy gamma before an event?"}).content)



"""
>>> llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
>>> print((prompt | llm).invoke({"context": context, "question": "Should I buy gamma before an event?"}).content)
Buying gamma before an event can be beneficial if you anticipate that the realized volatility will exceed the implied volatility 
plus costs associated with the trade, as this can lead to profits [1]. However, be cautious, as event volatility can collapse after the catalyst passes, 
which may impact your position negatively [2]. It's essential to weigh these factors before making a decision.


"""

# 4. The Execution Flow
    # Retrieve: Find the 2 most relevant notes about "gamma" and "events."
    # Numbering: Label those notes as [1] and [2].
    # Synthesize: The LLM reads the labeled notes.
    # Answer: It generates a response like: "You should consider buying gamma because it profits when realized volatility exceeds 
    # implied volatility [1], but be aware that volatility can collapse after the event [2]."

# Why use Citations?
    # Trust: The user can see exactly which "note" the information came from.
    # Verification: If the AI says something strange, you can look up note_1 in your original files to check the facts.
    # Hallucination Prevention: When an AI is forced to cite a source, it is less likely to make up facts because it is looking for a specific reference 
    # number to "anchor" its statement.


# Summary Table: Retrieval vs. Citation

    # Step,                 Standard RAG,R                      AG with Citations
    # Search,               Finds relevant text.,               Finds relevant text + Metadata.
    # Prompt,               """Use this info to answer.""",     """Use this info and cite it as [1], [2]."""
    # Output,               A plain paragraph.,                 A paragraph with footnotes/citations.




# Why citation-aware RAG matters
    # Normal RAG:
        # answer generated from context
        # (no traceability)

    # Citation-aware RAG:
        # answer generated from context
        # + explicit references

    # Benefits:

        # Feature	                    Advantage
        #  ----------------------------------------------
        # auditability	                know source of claims
        # trust	                        reduces hallucinations
        # explainability	            improves interpretability
        # research workflows	        production-ready
        # compliance environments	    essential


# How this fits into a trading-agent workflow
    # Example pipeline:
        # User: Should I buy gamma before ECB?
        # ↓
        # Retrieve event-vol research notes
        # ↓
        # Inject numbered context
        # ↓
        # LLM answers with citations
        # ↓
        # Trader sees reasoning + source references

    # Instead of:
        # black-box LLM answer

    # you get:
        # traceable research-backed answer

    # which is exactly how institutional research copilots are designed.
