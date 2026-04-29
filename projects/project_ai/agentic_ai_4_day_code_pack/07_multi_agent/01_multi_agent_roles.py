"""
Multi-agent pattern:
Use different system prompts as specialist roles.
"""


########################################################################################################################################################
# This code demonstrates the Multi-Agent Orchestration pattern. Instead of asking one "generalist" AI to solve a complex problem, 
# you are delegating the task to several "specialist" agents with distinct personas and then using a "lead" agent to synthesize their outputs.

# Think of this as a Virtual Investment Committee.
########################################################################################################################################################

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 1. The Core Agent Function
    # The agent function is a reusable template that takes a role (the System Prompt) and a task.
    # By changing the system message, you are effectively "priming" the LLM to access different parts of its training data. 
    # The "Macro Strategist" will prioritize geopolitical news, while the "FX Options Quant" will prioritize mathematical Greek calculations
    # (gamma, theta, vega).
                                                                                                                                                                                                                                                              
def agent(role: str, task: str) -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", role),
        ("human", "{task}")
    ])
    return (prompt | llm).invoke({"task": task}).content

question = "Evaluate a possible long EURUSD 1M straddle before an ECB meeting."

# 2. The Specialist Tier (Parallel Processing)
    # In this code, three specialists analyze the exact same question simultaneously from different angles:
    # Strategist: Looks at the "Why" (ECB policy, inflation, rate paths).
    # Quant: Looks at the "How" (Implied vs. Realized vol, cost of carry, decay).
    # Risk Manager: Looks at "What could go wrong" (Vol crush, liquidity gaps, gap risk).

strategist = agent("You are a macro strategist.", question)
quant = agent("You are an FX options quant. Focus on vol, skew, carry, theta, and gamma.", question)
risk = agent("You are a risk manager. Focus on downside and failure modes.", question)

# 3. The Synthesis Tier (The Supervisor)
    # The final step is the most important:
    # The "Portfolio Manager" agent doesn't see the original question in isolation; it sees the structured debate between the specialists. 
    # This helps the AI avoid "tunnel vision." If the Quant is bullish but the Risk Manager highlights a 5% chance of a catastrophic event, 
    # the Portfolio Manager can make a balanced, nuanced decision


final = agent(
    "You are a portfolio manager. Synthesize specialist views into one decision.",
    f"Strategist:\n{strategist}\n\nQuant:\n{quant}\n\nRisk:\n{risk}"
)

print(final)


# 4. Why this is effective for Finance/Quant Work
    # Reduction of Bias: Individual LLMs can sometimes "hallucinate" a single direction. Having a Risk Manager agent specifically looking for 
    # failure modes forces the system to consider the downside.

    # Context Density: By splitting the prompts, you give each agent more "room" to think. If one prompt tried to cover Macro, Quant, and Risk, 
    # the LLM might gloss over the technical details of the options Greeks to save space.

    # Modular Debugging: If the final decision is bad, you can look at the intermediate outputs. You might find that the "Quant" was right, 
    # but the "Strategist" was wrong, allowing you to tweak only the Strategist's prompt.


# Summary of the Flow:

# Agent,                    Input,                  Objective
# ---------------------------------------------------------------------------------------------------
# Strategist,               Question,               Fundamental/Macro analysis.
# Quant,                    Question,               Mathematical/Derivatives analysis.
# Risk Manager,             Question,               Stress testing and edge cases.
# Portfolio Manager,        Combined Notes,         Executive summary and actionable trade.


# How to take this to the next level?
    # In this script, the agents are "static"—they don't talk to each other. In a more advanced LangGraph version, you could allow them to argue:
    # The Risk Manager could see the Quant's report and say, "Wait, you're ignoring the gap risk on the ECB announcement."
    # The Quant could then revise their report.
