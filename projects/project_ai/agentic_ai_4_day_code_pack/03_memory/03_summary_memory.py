"""
Modern replacement for ConversationSummaryMemory:
Maintain a rolling summary and inject it into the prompt.
"""

from langchain_openai import ChatOpenAI
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

store = {}
summaries = {}
TRIGGER_MESSAGES = 6

summary_prompt = ChatPromptTemplate.from_template("""
Current summary:
{summary}

New conversation messages:
{messages}

Update the summary. Keep durable facts, preferences, goals, and decisions.
""")

def summarize(session_id: str):
    messages = store[session_id].messages
    old_summary = summaries.get(session_id, "")
    new_summary = (summary_prompt | llm).invoke({
        "summary": old_summary,
        "messages": "\n".join(str(m) for m in messages),
    }).content
    summaries[session_id] = new_summary
    store[session_id].messages = []

def get_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
        summaries[session_id] = ""
    if len(store[session_id].messages) >= TRIGGER_MESSAGES:
        summarize(session_id)
    return store[session_id]

prompt = ChatPromptTemplate.from_messages([
    ("system", "Conversation summary:\n{summary}"),
    MessagesPlaceholder("history"),
    ("human", "{input}")
])

def inject_summary(inputs, config):
    session_id = config["configurable"]["session_id"]
    return {**inputs, "summary": summaries.get(session_id, "")}

chain = inject_summary | prompt | llm

chat = RunnableWithMessageHistory(
    chain,
    get_history,
    input_messages_key="input",
    history_messages_key="history",
)

config = {"configurable": {"session_id": "summary-demo"}}

for q in [
    "My name is Sugat.",
    "I specialize in FX volatility.",
    "I want to master Agentic AI in 4 days.",
    "I prefer quant-style examples.",
    "I am building trading analytics tools.",
    "What do you remember about my goal?"
]:
    print("USER:", q)
    print("AI:", chat.invoke({"input": q}, config=config).content)
