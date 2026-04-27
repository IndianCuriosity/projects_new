from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    question: str
    route: str
    answer: str

def classify(state):
    q = state["question"].lower()
    return {"route": "finance" if "vol" in q else "general"}

def finance(state):
    return {"answer": "Finance route: analyze spot, vol, skew, carry."}

def general(state):
    return {"answer": "General route."}

def route(state):
    return state["route"]

builder = StateGraph(State)
builder.add_node("classify", classify)
builder.add_node("finance", finance)
builder.add_node("general", general)
builder.add_edge(START, "classify")
builder.add_conditional_edges("classify", route, {"finance": "finance", "general": "general"})
builder.add_edge("finance", END)
builder.add_edge("general", END)

print(builder.compile().invoke({"question": "Explain vol skew"}))
