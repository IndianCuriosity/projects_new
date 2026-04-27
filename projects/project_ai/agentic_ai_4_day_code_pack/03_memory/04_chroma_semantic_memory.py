

###################################################################################################
# This code implements Semantic Memory using a Vector Database (ChromaDB).

# Unlike the previous examples that used "Short-Term Memory" (keeping the last few messages) or "Summarization Memory," this approach
# creates "Long-Term Memory." It stores every interaction in a searchable database and only retrieves the pieces of information that are 
# mathematically relevant to the current question.

# This script implements a semantic long-term memory system using Chroma vector storage + embeddings + retrieval-augmented prompting. 
    # It’s effectively the modern replacement for VectorStoreRetrieverMemory.
    # Think of it as: store experiences → embed them → retrieve relevant ones later → inject into prompt
    # So your agent can remember meaning, not just exact conversation history.

# Pro-Tip for this Code
# Since you are using persist_directory, your ./chroma_semantic_memory_demo folder will grow. If you want to "reset" the AI's memory, you have to delete that folder 
# from your computer!

###################################################################################################

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate

# Initialize model + embedding engine
# Two different models are doing different jobs:

# Model	                Purpose
# gpt-4o-mini	            reasoning + responses
# text-embedding-3-small	semantic similarity

# Important idea: LLMs think & embeddings remember

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
emb = OpenAIEmbeddings(model="text-embedding-3-small")

# 1. The Vector Database (Chroma): Create persistent Chroma memory store
    # Chroma: This is the storage engine. Instead of a standard SQL database, it stores Vectors (lists of numbers representing meaning).
    # persist_directory: This is crucial. It saves the memory to your hard drive. Even if you stop the script and run it again tomorrow, the AI will still remember you.

# This creates a vector database on disk.
# So memory survives:  script restart, kernel restart, machine restart
# Internally Chroma stores: text → embedding vector → index
# Example entry: # User specializes in FX volatility and wants quant-focused examples becomes: [0.12, -0.88, 0.34, ...]

vs = Chroma(collection_name="semantic_memory_demo", embedding_function=emb, persist_directory=".db_others/chroma_semantic_memory_demo")


# 3. The save_memory Function: Function to store memory
# Every time you or the AI speaks, the interaction is saved:

    # Python
    # save_memory(f"User: {user_input}\nAssistant: {response.content}")
# This ensures the database grows more "knowledgeable" about your preferences over time. Because it uses embeddings, if you previously mentioned you
#  like "quant-focused examples," that memory will be pulled when you ask about "memory in LangChain," even if the words "quant" or "examples" aren't in your 
# current question.

# Adds memory to vector DB.

    # Example stored entry:
        # User: Teach me LangChain
        # Assistant: explanation...
    # This enables: experience-based recall
    # instead of:  chat-history recall

def save_memory(text):
    vs.add_texts([text])


# 2. The recall Function (Semantic Search): Function to retrieve relevant memory: Searches semantic memory.
    # Instead of passing the entire history to the LLM, the recall function acts like a librarian:
    # It turns your current question ("Teach me memory...") into a vector.
    # It searches the database for the Top K (in this case, 3) most similar memories.
    # It returns only those relevant snippets to be injected into the prompt.

def recall(query, k=3):

    # Chroma performs:
        #     embed(query)
        #     compare with stored vectors
        #     return closest matches

    #     Example:
    #     Query:
        #     Teach me memory in LangChain
    #     Stored memory:
        #     User specializes in FX volatility and wants quant-focused examples.
    #     Returned because:
        #     LangChain memory + quant context = semantically related

    docs = vs.similarity_search(query, k=k)

    # Formats retrieved memories as text.
    #     Example output:
    #     User specializes in FX volatility and wants quant-focused examples.

    return "\n".join(d.page_content for d in docs)

# Prompt template using memory
    # This injects retrieved memory into the system prompt.
    # So actual prompt becomes:

    #     System:
    #     Relevant memories:
    #     User specializes in FX volatility and wants quant-focused examples.

    #     User:
    #     Teach me memory in LangChain.

    # This changes model behavior dramatically.

    # Instead of generic explanation, it gives:

    #     quant-oriented explanation

prompt = ChatPromptTemplate.from_messages([
    ("system", "Relevant memories:\n{memory}"),
    ("human", "{input}"),
])

# Chat function (core agent logic): This runs the full pipeline.
def chat(user_input):
        # retrieve memory (example: User specializes in FX volatility...)
    memory = recall(user_input)

        # generate response: Pipeline: memory → prompt → LLM → answer
        # Now the assistant answers context-aware.
    response = (prompt | llm).invoke({"memory": memory, "input": user_input})

        # store interaction: This makes memory self-updating. 
        # So system learns: every interaction becomes future knowledge
        # Example stored entry:
            # User: Teach me memory in LangChain.
            # Assistant: explanation...
    save_memory(f"User: {user_input}\nAssistant: {response.content}")
        # return response
        # Outputs answer to user.
    return response.content

# Seed initial memory
    # This primes the agent with user profile. So later queries adapt automatically:
    # Example:Explain RAG becomes: Explain RAG for FX vol research workflows
    
save_memory("User specializes in FX volatility and wants quant-focused examples.")

# Run conversation
    # Execution flow:

    #     Embed query
    #     ↓
    #     Search Chroma
    #     ↓
    #     Retrieve FX-vol preference
    #     ↓
    #     Inject into prompt
    #     ↓
    #     LLM answers with quant framing
    #     ↓
    #     Store interaction

print(chat("Teach me memory in LangChain."))


# 4. The Execution Flow
    # 1. Manual Seeding: You explicitly save a memory that the user likes FX volatility.
    # 2. User Input: "Teach me memory in LangChain."
    # 3. Semantic Retrieval: The system searches the database. It finds the "FX volatility" note because it's a "quant" topic related to learning.
    # 4. Prompt Injection: The LLM receives a prompt like this:
        # System: Relevant memories: User specializes in FX volatility...
        # Human: Teach me memory in LangChain.
    # 5. Personalized Response: The LLM will now explain memory using FX volatility or quant examples because that context was provided in the memory variable.

# Comparison: Why use Semantic Memory?
# ------------------------------------------
# Memory                   TypeBest                               ForDownside
# Sliding                  WindowQuick back-and-forth chat.       Forgets everything older than X turns.
# SummarizationLong,       logical conversations.                 Details get lost in the summary.
# Semantic (This code)     Long-term personalization.             Can occasionally pull "irrelevant" similar-sounding memories.

# Memory grows like: experience log instead of: chat transcript



# Why this pattern matters for Agentic AI mastery

# This is the backbone of:

    # long-term agent memory
    # research copilots
    # trading assistants
    # personalization systems
    # adaptive multi-session workflows

# Compare memory types:

    # Memory Type	        Example
    # buffer memory	        last few messages
    # summary memory	    compressed history
    # semantic memory	    relevant past knowledge
    # vector memory	        scalable persistent recall

# Your script implements:
    # semantic + persistent + self-updating memory
# which is exactly how modern LangGraph agents manage long-term knowledge.


"""
>>> print(chat("Teach me memory in LangChain."))
LangChain is a framework designed to facilitate the development of applications using language models. One of its features is memory, which allows the application 
to retain information across interactions, making it more contextually aware and capable of maintaining a coherent conversation over time.

Here’s a brief overview of how memory works in LangChain:

### Types of Memory

1. **Simple Memory**: This is a basic form of memory where the application can remember a limited amount of information. It can store key-value pairs and retrieve them when needed.

2. **Conversation Memory**: This type of memory is designed for chat applications. It keeps track of the conversation history, allowing the model to refer back to previous messages 
and maintain context.

3. **Custom Memory**: You can implement your own memory logic to suit specific needs, such as storing data in a database or using more complex data structures.

### Implementing Memory in LangChain

Here’s a simple example of how to implement memory in a LangChain application:

1. **Install LangChain**: Make sure you have LangChain installed in your environment.

   ```bash
   pip install langchain
   ```

2. **Set Up Memory**: You can create a memory instance and integrate it into your LangChain application.

   ```python
   from langchain.memory import SimpleMemory
   from langchain.llms import OpenAI

   # Initialize memory
   memory = SimpleMemory()

   # Initialize language model
   llm = OpenAI()

   # Function to interact with the model
   def chat_with_memory(user_input):
       # Retrieve previous context from memory
       context = memory.get_memory()
       
       # Combine context with user input
       prompt = f"{context}\nUser: {user_input}\nAI:"
       
       # Get response from the language model
       response = llm(prompt)
       
       # Store the new context in memory
       memory.update_memory(f"User: {user_input}\nAI: {response}")
       
       return response
   ```

3. **Using the Memory**: You can now call the `chat_with_memory` function to interact with the model while retaining context.

   ```python
   print(chat_with_memory("Hello, how are you?"))
   print(chat_with_memory("What can you tell me about FX volatility?"))
   ```

### Considerations

- **Memory Size**: Be mindful of the amount of information you store. Too much data can lead to performance issues or irrelevant context.
- **Data Management**: Implement logic to manage memory, such as clearing old data or summarizing past interactions.
- **Privacy**: Ensure that sensitive information is handled appropriately, especially if the memory is persistent.

### Conclusion

Memory in LangChain enhances the interactivity and contextual awareness of applications built with language models. By implementing memory, 
you can create more engaging and coherent user experiences.


"""