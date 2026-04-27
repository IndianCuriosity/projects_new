"""
LangGraph research workflow:
Plan -> Retrieve -> Analyze -> Risk Check -> Final Answer
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

class ResearchState(TypedDict):
    question: str
    plan: str
    context: str
    analysis: str
    risk_check: str
    final: str

def planner(state: ResearchState):
    msg = llm.invoke(f"Create a concise research plan for: {state['question']}")
    return {"plan": msg.content}

def retriever(state: ResearchState):
    context = "Mock context: EURUSD 1M risk reversals have richened; realized vol remains below implied."
    return {"context": context}

def analyst(state: ResearchState):
    msg = llm.invoke(f"Question: {state['question']}\nPlan: {state['plan']}\nContext: {state['context']}\nAnalyze.")
    return {"analysis": msg.content}

def risk_check(state: ResearchState):
    msg = llm.invoke(f"Check this analysis for missing risks:\n{state['analysis']}")
    return {"risk_check": msg.content}

def final_answer(state: ResearchState):
    msg = llm.invoke(f"Produce final answer.\nAnalysis: {state['analysis']}\nRisk check: {state['risk_check']}")
    return {"final": msg.content}

builder = StateGraph(ResearchState)
for name, fn in [
    ("planner", planner),
    ("retriever", retriever),
    ("analyst", analyst),
    ("risk_check", risk_check),
    ("final_answer", final_answer),
]:
    builder.add_node(name, fn)

builder.add_edge(START, "planner")
builder.add_edge("planner", "retriever")
builder.add_edge("retriever", "analyst")
builder.add_edge("analyst", "risk_check")
builder.add_edge("risk_check", "final_answer")
builder.add_edge("final_answer", END)

graph = builder.compile()

result = graph.invoke({"question": "Should I buy EURUSD gamma before an ECB event?"})
print(result["final"])
