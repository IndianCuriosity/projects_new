from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

specialist_outputs = {
    "macro": "Event risk supports owning optionality, but market may already price it.",
    "quant": "Check implied vs realized, breakeven, gamma/theta, and skew.",
    "risk": "Main risks are vol crush, poor realized vol, and transaction costs.",
}

coordination_prompt = f"""
You are a coordinator PM.
Synthesize these specialist views into one action plan:

{specialist_outputs}
"""

print(llm.invoke(coordination_prompt).content)
