from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

class State(TypedDict):
    question: str
    market_context: str
    quant_analysis: str
    risk_review: str
    final: str

def retrieve_market_context(state):
    return {"market_context": "Mock: implied vol elevated into ECB; realized vol mixed; skew rich."}

def quant_analysis(state):
    prompt = f"Question: {state['question']}\nMarket context: {state['market_context']}\nDo quant vol analysis."
    return {"quant_analysis": llm.invoke(prompt).content}

def risk_review(state):
    prompt = f"Review risks in this analysis:\n{state['quant_analysis']}"
    return {"risk_review": llm.invoke(prompt).content}

def final_answer(state):
    prompt = f"Final recommendation.\nAnalysis:\n{state['quant_analysis']}\nRisk:\n{state['risk_review']}"
    return {"final": llm.invoke(prompt).content}

b = StateGraph(State)
b.add_node("retrieve_market_context", retrieve_market_context)
b.add_node("quant_analysis", quant_analysis)
b.add_node("risk_review", risk_review)
b.add_node("final_answer", final_answer)

b.add_edge(START, "retrieve_market_context")
b.add_edge("retrieve_market_context", "quant_analysis")
b.add_edge("quant_analysis", "risk_review")
b.add_edge("risk_review", "final_answer")
b.add_edge("final_answer", END)

graph = b.compile()
print(graph.invoke({"question": "Should I buy EURUSD gamma before ECB?"})["final"])
