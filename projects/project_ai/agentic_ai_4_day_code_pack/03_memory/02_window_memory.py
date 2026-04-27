"""
Modern replacement for ConversationBufferWindowMemory:
Keep only the last K user/AI turns.
"""

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

for q in [
    "My name is Sugat.",
    "I work in FX volatility.",
    "I am learning LangGraph.",
    "What am I learning?"
]:
    print("USER:", q)
    print("AI:", chat.invoke({"input": q}, config=config).content)
