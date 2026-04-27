from langchain_openai import ChatOpenAI
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
store = {}
summary = {"default": "User wants concise quant-focused Agentic AI examples."}

def get_history(session_id):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    store[session_id].messages = store[session_id].messages[-4:]
    return store[session_id]

prompt = ChatPromptTemplate.from_messages([
    ("system", "Longer-term summary:\n{summary}"),
    MessagesPlaceholder("history"),
    ("human", "{input}"),
])

def inject_summary(inputs, config):
    return {**inputs, "summary": summary["default"]}

chat = RunnableWithMessageHistory(inject_summary | prompt | llm, get_history, input_messages_key="input", history_messages_key="history")

print(chat.invoke({"input": "Explain hybrid memory."}, config={"configurable": {"session_id": "hybrid"}}).content)
