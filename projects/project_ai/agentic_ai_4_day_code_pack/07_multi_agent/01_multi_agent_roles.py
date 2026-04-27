"""
Multi-agent pattern:
Use different system prompts as specialist roles.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def agent(role: str, task: str) -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", role),
        ("human", "{task}")
    ])
    return (prompt | llm).invoke({"task": task}).content

question = "Evaluate a possible long EURUSD 1M straddle before an ECB meeting."

strategist = agent("You are a macro strategist.", question)
quant = agent("You are an FX options quant. Focus on vol, skew, carry, theta, and gamma.", question)
risk = agent("You are a risk manager. Focus on downside and failure modes.", question)

final = agent(
    "You are a portfolio manager. Synthesize specialist views into one decision.",
    f"Strategist:\n{strategist}\n\nQuant:\n{quant}\n\nRisk:\n{risk}"
)

print(final)
