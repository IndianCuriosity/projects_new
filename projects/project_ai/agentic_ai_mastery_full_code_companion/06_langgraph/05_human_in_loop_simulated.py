from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    trade: str
    approved: bool
    final: str

def propose_trade(state):
    return {"trade": "Buy EURUSD 1M straddle"}

def human_approval_gate(state):
    approved = False
    return {"approved": approved}

def finalize(state):
    if state["approved"]:
        return {"final": f"Proceed: {state['trade']}"}
    return {"final": f"Do not execute. Human approval missing for: {state['trade']}"}

b = StateGraph(State)
b.add_node("propose_trade", propose_trade)
b.add_node("approval", human_approval_gate)
b.add_node("finalize", finalize)
b.add_edge(START, "propose_trade")
b.add_edge("propose_trade", "approval")
b.add_edge("approval", "finalize")
b.add_edge("finalize", END)

print(b.compile().invoke({"trade": "", "approved": False, "final": ""}))
