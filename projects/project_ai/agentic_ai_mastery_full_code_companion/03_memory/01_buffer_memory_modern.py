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
