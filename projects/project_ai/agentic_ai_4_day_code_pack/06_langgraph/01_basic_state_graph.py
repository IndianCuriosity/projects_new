"""
LangGraph basics:
A graph is made of nodes. Each node reads and updates shared state.
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class GraphState(TypedDict):
    question: str
    classification: str
    answer: str

def classify(state: GraphState):
    q = state["question"].lower()
    if "vol" in q or "option" in q:
        return {"classification": "finance"}
    return {"classification": "general"}

def answer_finance(state: GraphState):
    return {"answer": "This is a finance/options question. Analyze spot, vol, skew, carry, and event risk."}

def answer_general(state: GraphState):
    return {"answer": "This is a general question."}

def route(state: GraphState):
    return "finance" if state["classification"] == "finance" else "general"

builder = StateGraph(GraphState)
builder.add_node("classify", classify)
builder.add_node("finance", answer_finance)
builder.add_node("general", answer_general)

builder.add_edge(START, "classify")
builder.add_conditional_edges("classify", route, {
    "finance": "finance",
    "general": "general",
})
builder.add_edge("finance", END)
builder.add_edge("general", END)

graph = builder.compile()

print(graph.invoke({"question": "Explain EURUSD vol skew"}))
