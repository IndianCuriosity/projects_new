from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    question: str
    macro_view: str
    quant_view: str
    final: str

def macro(state):
    return {"macro_view": "Macro: event risk is high."}

def quant(state):
    return {"quant_view": "Quant: compare implied vs realized and theta."}

def combine(state):
    return {"final": state["macro_view"] + "\n" + state["quant_view"]}

b = StateGraph(State)
b.add_node("macro", macro)
b.add_node("quant", quant)
b.add_node("combine", combine)

b.add_edge(START, "macro")
b.add_edge(START, "quant")
b.add_edge("macro", "combine")
b.add_edge("quant", "combine")
b.add_edge("combine", END)

print(b.compile().invoke({"question": "Evaluate long gamma"}))
