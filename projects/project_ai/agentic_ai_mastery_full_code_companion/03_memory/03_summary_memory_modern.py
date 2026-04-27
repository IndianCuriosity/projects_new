from langchain_openai import ChatOpenAI
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
store = {}
summaries = {}
TRIGGER_MESSAGES = 6

summary_prompt = ChatPromptTemplate.from_template(
    "Existing summary:\n{summary}\n\nNew messages:\n{messages}\n\nUpdate the summary."
)

def summarize(session_id):
    old = summaries.get(session_id, "")
    messages = "\n".join(str(m) for m in store[session_id].messages)
    summaries[session_id] = (summary_prompt | llm).invoke({"summary": old, "messages": messages}).content
    store[session_id].messages = []

def get_history(session_id):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
        summaries[session_id] = ""
    if len(store[session_id].messages) >= TRIGGER_MESSAGES:
        summarize(session_id)
    return store[session_id]

prompt = ChatPromptTemplate.from_messages([
    ("system", "Conversation summary:\n{summary}"),
    MessagesPlaceholder("history"),
    ("human", "{input}"),
])

def add_summary(inputs, config):
    sid = config["configurable"]["session_id"]
    return {**inputs, "summary": summaries.get(sid, "")}

chat = RunnableWithMessageHistory(add_summary | prompt | llm, get_history, input_messages_key="input", history_messages_key="history")

config = {"configurable": {"session_id": "summary"}}
for q in ["My name is Sugat.", "I focus on FX vol.", "I want Agentic AI mastery.", "Use quant examples.", "I like LangGraph.", "What is my goal?"]:
    print(chat.invoke({"input": q}, config=config).content)
