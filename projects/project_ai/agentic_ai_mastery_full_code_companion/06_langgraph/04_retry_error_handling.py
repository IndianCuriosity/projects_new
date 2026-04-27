from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    attempts: int
    status: str

def unstable_node(state):
    attempts = state.get("attempts", 0) + 1
    if attempts < 2:
        return {"attempts": attempts, "status": "retry"}
    return {"attempts": attempts, "status": "success"}

def done(state):
    return {"status": f"completed after {state['attempts']} attempts"}

def route(state):
    return "retry" if state["status"] == "retry" else "done"

b = StateGraph(State)
b.add_node("unstable", unstable_node)
b.add_node("done", done)
b.add_edge(START, "unstable")
b.add_conditional_edges("unstable", route, {"retry": "unstable", "done": "done"})
b.add_edge("done", END)

print(b.compile().invoke({"attempts": 0, "status": ""}))
