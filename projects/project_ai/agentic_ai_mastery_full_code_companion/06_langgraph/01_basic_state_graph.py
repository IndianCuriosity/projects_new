from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    input: str
    output: str

def node(state: State):
    return {"output": f"Processed: {state['input']}"}

builder = StateGraph(State)
builder.add_node("node", node)
builder.add_edge(START, "node")
builder.add_edge("node", END)

graph = builder.compile()
print(graph.invoke({"input": "hello"}))
