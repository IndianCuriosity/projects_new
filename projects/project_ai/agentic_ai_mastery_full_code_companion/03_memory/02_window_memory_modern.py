from langchain_openai import ChatOpenAI
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

K_TURNS = 2
store = {}
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def get_history(session_id):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    store[session_id].messages = store[session_id].messages[-2 * K_TURNS:]
    return store[session_id]

prompt = ChatPromptTemplate.from_messages([
    ("system", "You use only recent chat history."),
    MessagesPlaceholder("history"),
    ("human", "{input}"),
])

chat = RunnableWithMessageHistory(prompt | llm, get_history, input_messages_key="input", history_messages_key="history")
config = {"configurable": {"session_id": "window"}}

for q in ["My name is Sugat.", "I trade FX vol.", "I am learning LangGraph.", "What am I learning?"]:
    print("USER:", q)
    print("AI:", chat.invoke({"input": q}, config=config).content)
