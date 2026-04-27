from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

class State(TypedDict):
    question: str
    plan: str
    context: str
    analysis: str
    final: str

def plan(state):
    return {"plan": llm.invoke(f"Plan answer: {state['question']}").content}

def retrieve(state):
    return {"context": "Mock context: implied vol is high before central-bank events; vol crush risk after event."}

def analyze(state):
    return {"analysis": llm.invoke(f"Question: {state['question']}\nContext: {state['context']}").content}

def finalize(state):
    return {"final": llm.invoke(f"Give final answer:\n{state['analysis']}").content}

b = StateGraph(State)
for name, fn in [("plan", plan), ("retrieve", retrieve), ("analyze", analyze), ("finalize", finalize)]:
    b.add_node(name, fn)

b.add_edge(START, "plan")
b.add_edge("plan", "retrieve")
b.add_edge("retrieve", "analyze")
b.add_edge("analyze", "finalize")
b.add_edge("finalize", END)

print(b.compile().invoke({"question": "Should I buy EURUSD gamma before ECB?"})["final"])
