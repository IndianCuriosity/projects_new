"""
Modern replacement for ConversationBufferWindowMemory:
Keep only the last K user/AI turns.
"""
#########################################################################################################

# This code implements a Sliding Window Memory (also known as "Buffer Window Memory"). Instead of letting the conversation history grow indefinitely—which would 
# eventually become too expensive or exceed the LLM's context limit—this script ensures the AI only remembers the most recent interactions.
# Here is the breakdown of the logic:

# 1. The "Window" Constraint
#     The variable K_TURNS = 2 defines the limit. In chat terms, one "turn" usually consists of one Human message and one AI message. 
#       Therefore, 2 turns equals 4 messages total.

#########################################################################################################

from langchain_openai import ChatOpenAI
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

K_TURNS = 2
MAX_MESSAGES = K_TURNS * 2

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
store = {}

def get_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    
    #  2. Slicing the History: The "magic" happens inside the get_history function:
    #     Every time the chain is invoked, this line looks at the stored list of messages for that user and slices it. 
    #     It keeps only the last 4 messages (2 * 2) and discards everything older.
    store[session_id].messages = store[session_id].messages[-MAX_MESSAGES:]
    return store[session_id]

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a concise assistant."),
    MessagesPlaceholder("history"),
    ("human", "{input}")
])

chat = RunnableWithMessageHistory(
    prompt | llm,
    get_history,
    input_messages_key="input",
    history_messages_key="history",
)

config = {"configurable": {"session_id": "window-demo"}}
human_mssgs = ["My name is Sugat.","I trade FX vol.","I am learning LangGraph.","What am I learning?","What is my name?"]

for q in human_mssgs:
    print("USER:", q)
    print("AI:", chat.invoke({"input": q}, config=config).content)





""" 

USER: My name is Sugat.
AI: Nice to meet you, Sugat! How can I assist you today?
USER: I trade FX vol.
AI: That's great! Trading FX volatility can be quite complex. Are you looking for specific strategies, market insights, or something else related to FX volatility?
USER: I am learning LangGraph.
AI: That's interesting! LangGraph is a tool for working with language models and graph structures. What specific aspects of LangGraph are you focusing on, or do you have any questions about it?
USER: What am I learning?
AI: In learning LangGraph, you are likely exploring how to integrate language models with graph-based data structures. This may include:

1. **Graph Representation**: Understanding how to represent data as graphs, including nodes and edges.
2. **Natural Language Processing (NLP)**: Learning how to apply NLP techniques to extract insights from text data.
3. **Graph Algorithms**: Familiarizing yourself with algorithms that can analyze and manipulate graph structures.
4. **Applications**: Exploring use cases such as knowledge graphs, recommendation systems, or semantic search.

If you have specific topics or questions in mind, feel free to share!
USER: What is my name?
AI: I don't have access to personal information, so I don't know your name. If you'd like to share it or have any other questions, feel free to let me know!

 """
########################################################################################################################################################
# 3. Trace of the Execution

# Let's look at how the AI's "brain" changes as the loop runs:

# Turn 1: "My name is Sugat."
    # Memory: [Human: My name is Sugat]
# Turn 2: "I trade FX vol."
    # Memory: [Human: My name is Sugat, AI: Hello Sugat..., Human: I trade FX vol]
# Turn 3: "I am learning LangGraph."
    # Memory: The window is full! As "I am learning LangGraph" is added, the very first message ("My name is Sugat") starts to fall off the edge.
# Turn 4: "What am I learning?"
    # Memory: The AI sees "I trade FX vol" and "I am learning LangGraph."
# Result: It will correctly answer "LangGraph."

# Crucial Note: If you asked "What is my name?" in Turn 5, the AI would likely say "I don't know" or ask for your name again, 
# because that information was in the first turn, which has now been "pushed out" of the sliding window.

# 4. Why use this?
#     Cost Efficiency: You aren't paying for the LLM to re-read the entire conversation every time you ask a new question.

#     Focus: It prevents the model from getting distracted by old, irrelevant parts of a long conversation.

#     Token Limits: Every model has a maximum "context window." Slicing the history manually ensures you never hit that hard limit and crash your app.



# Feature         Strategy in this Code
# Storage         InMemoryChatMessageHistory (Volatile/RAM)
# Management      Manual Slicing (-2 * K_TURNS)
# Logic           "FIFO (First-In, First-Out)"

########################################################################################################################################################