"""
Modern replacement for ConversationBufferMemory:
RunnableWithMessageHistory stores chat messages per session.
"""
########################################################################################################################################
# This code demonstrates the modern way to handle Conversation Memory in LangChain.
# Older versions used a class called ConversationBufferMemory, but it was difficult to manage multiple users or "sessions." 
# The new RunnableWithMessageHistory is a "wrapper" that attaches a database (or in-memory store) to your chain based on a specific ID.
# It lets an LLM remember conversation history across turns, grouped by session.

# Summary of the Flow:
    # User Input + Session ID
    # Fetch History from store 
    # Fill Prompt (System + History + Human) 
    # Get LLM Answer 
    # Save Update back to store

########################################################################################################################################



from langchain_openai import ChatOpenAI                                         # Purpose : LLM
from langchain_core.chat_history import InMemoryChatMessageHistory              # Purpose : stores messages
from langchain_core.prompts import ChatPromptTemplate                           # Purpose : build structured prompts
from langchain_core.prompts import MessagesPlaceholder                          # Purpose : injects history into prompt
from langchain_core.runnables.history import RunnableWithMessageHistory         # Purpose : attaches memory to chain

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)                            # Standard deterministic chat model.

# 1. The Ingredients

# MessagesPlaceholder("history"): This is a "parking spot" in your prompt. When the chain runs, it will inject all previous messages from 
# the conversation into this specific location. This tells LangChain: Insert past conversation messages here automatically

# Define prompt template. This builds a structured prompt:
    # System: You are a helpful assistant.
    # History: <previous messages inserted here>
    # User: current input

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    MessagesPlaceholder("history"),
    ("human", "{input}")
])

# Build the chain. This creates a runnable pipeline:
# input → prompt → LLM → output
    # But currently:
    # ❌ no memory yet
chain = prompt | llm



# Create memory storage dictionary
# store = {}: This is your dictionary where keys are session_ids (like "sugat") and values are the actual message histories
# This holds chat history per session:
    # {
    #   "sugat": InMemoryChatMessageHistory(...)
    # }

# Think of it like:
    # session_id → conversation history
store = {}



# Define history loader function
# This function retrieves memory for each user/session.
#         Meaning:

#     If session doesn't exist → create memory
#     Otherwise: Return existing memory
#     So: session "sugat" always gets the same history object.

# InMemoryChatMessageHistory: This is a simple list stored in your computer's RAM that holds the messages. In a real app, you'd swap this for 
# PostgresChatMessageHistory or RedisChatMessageHistory.
    
def get_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# 3. Key Parameters in the Wrapper
    # The RunnableWithMessageHistory requires a few specific "map" instructions:
        # input_messages_key: Tells the wrapper which key in your input dictionary contains the new human message ("input").
        # history_messages_key: Tells the wrapper which variable in the prompt represents the history ("history").

# Attach memory to chain
    # It converts: stateless chain into: stateful conversational chain
    # Explanation of parameters:
        # chain : Your pipeline : prompt | llm
        # get_history : Function that returns chat history per session
        # input_messages_key input_messages_key="input": Matches this prompt variable: ("human", "{input}"). So LangChain knows: User message → goes into "input"
        # history_messages_key history_messages_key="history": Matches MessagesPlaceholder("history") . So LangChain knows: Insert past messages here

chat = RunnableWithMessageHistory(
    chain,
    get_history,
    input_messages_key="input",
    history_messages_key="history",
)

# 2. The Logic: How it Works
    
    # When you call chat.invoke(...), several things happen behind the scenes:

        # Lookup: LangChain looks at your config and finds the session_id ("sugat").
        # Retrieval: It calls get_history("sugat"). If this is the first time, it creates a new empty history.
        # Injection: It takes all past messages (e.g., "My name is Sugat") and puts them into the MessagesPlaceholder labeled "history".
        # Execution: The LLM receives the full context, generates an answer, and—this is the important part—automatically saves both your question and 
        # its answer back into the store.

# Define session ID. This tells LangChain: Use memory bucket: sugat
    # If instead: session_id="trader_1", it would create separate conversation memory.
    # So this supports: multi-user chat memory

config = {"configurable": {"session_id": "sugat"}}

# First message

# Execution flow:
#     Step 1
# History is empty:
# []
# Prompt becomes:
    # System: You are a helpful assistant.
    # User: My name is Sugat.

# Model responds:
    # Nice to meet you Sugat.

# LangChain stores:
    # User: My name is Sugat
    # AI: Nice to meet you Sugat

# inside memory.

print(chat.invoke({"input": "My name is Sugat."}, config=config).content)

# Second message

# Now history exists:
    # User: My name is Sugat
    # AI: Nice to meet you Sugat

# Prompt becomes:
    # System: You are a helpful assistant.
    # History:
    # User: My name is Sugat
    # AI: Nice to meet you Sugat
    # User: What is my name?

# Model answers:
    # Your name is Sugat.

# Because memory was injected automatically.

print(chat.invoke({"input": "What is my name?"}, config=config).content)


""" 
>>> print(chat.invoke({"input": "My name is Sugat."}, config=config).content)
Nice to meet you, Sugat! How can I assist you today?
>>> print(chat.invoke({"input": "What is my name?"}, config=config).content)
Your name is Sugat. How can I help you today, Sugat?
 """

#############################################################################################################
# What RunnableWithMessageHistory does internally
# Each call:
    # invoke()

# automatically performs:
    # load history
    # append user message
    # run chain
    # append AI message
    # save history

# So memory evolves like:
    # Turn 1:
    # User → stored
    # AI → stored

    # Turn 2:
    # User → stored
    # AI → stored

# Benefits of RunnableWithMessageHistory(): multisession, composable chains, langGraph compatible, streaming support, production-ready

# How this is used in real agent systems
# Example architecture:

    # User question
    #    ↓
    # RunnableWithMessageHistory
    #    ↓
    # LangGraph workflow
    #    ↓
    # Retriever
    #    ↓
    # Tools
    #    ↓
    # LLM

# Memory becomes:
    # short-term reasoning context
# inside agents.

# Quick mental model

# This line: chat = RunnableWithMessageHistory(...)
# wraps your chain like this:

    # stateless LLM
    #       ↓
    # + session-aware memory
    #       ↓
    # stateful conversational agent

########################################################################################################################################


# 4. Why this is powerful
# Because of the session_id, you can support thousands of users at once using the same

# Sugat's session
config_sugat = {"configurable": {"session_id": "sugat"}}
chat.invoke({"input": "My name is Sugat."}, config=config_sugat)

# A different user's session
config_bob = {"configurable": {"session_id": "bob"}}
chat.invoke({"input": "What is my name?"}, config=config_bob) 
# Result: Bob's session is empty, so the AI won't know his name!



#########################################################################################################################################
from langchain_openai import ChatOpenAI
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
store = {}

def get_history(session_id):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are helpful."),
    MessagesPlaceholder("history"),
    ("human", "{input}"),
])

chat = RunnableWithMessageHistory(prompt | llm, get_history, input_messages_key="input", history_messages_key="history")

config = {"configurable": {"session_id": "demo"}}
print(chat.invoke({"input": "My name is Sugat."}, config=config).content)
print(chat.invoke({"input": "What is my name?"}, config=config).content)