
###############################################################################
# Reason → Act/tool call → Observe result → Reason again → Final answer

# This code is a manual implementation of a ReAct (Reasoning + Acting) Agent. Instead of relying on a pre-built library like AgentExecutor or LangGraph, 
# you have built the engine yourself using a basic for loop.

# This is the most "under-the-hood" way to understand how AI agents actually work.

# Decoupled Logic: The LLM doesn't know how to calculate volatility; it only knows when to ask for it.

###############################################################################


###############################################################################################################
# 4. Key Message Types Used
# This code demonstrates the three pillars of a tool-calling conversation:

""" 
Message Type        Who sends it?       Purpose
-------------------------------------------------------
SystemMessage       Developer           "Sets the ""rules"" and persona (FX Assistant)."
HumanMessage        User                "The question (""Should I buy gamma?"")."
AIMessage           LLM                 Contains either the reasoning text or the tool call ID.
ToolMessage         Your Loop           Passes the output of the Python function back to the AI.

 """
###############################################################################################################



import math
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage

# 1. The Toolset (The "Acting" Layer)
# You’ve defined two domain-specific tools:
    # annualized_vol: Converts raw price returns into a standardized volatility number.
    # vol_breakeven: Compares market prices (implied vol) to actual movement (realized vol) to provide trade advice.

@tool
def annualized_vol(returns_csv: str) -> float:
    """Calculate annualized volatility from comma-separated daily returns."""
    returns = [float(x.strip()) for x in returns_csv.split(",")]
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    return math.sqrt(variance) * math.sqrt(252)

@tool
def vol_breakeven(implied_vol: float, realized_vol: float) -> str:
    """Compare implied volatility and realized volatility."""
    diff =  realized_vol - implied_vol

    if diff > 0:
        return f"Realized vol is higher by {diff:.2%}. Long gamma may be attractive."
    else:
        return f"Realized vol is lower by {-diff:.2%}. Long gamma may struggle."

# 2. The Tool Map (The "Glue")
# This is a critical helper. When the LLM says, "I want to use annualized_vol," it returns a string. This dictionary allows your Python code to look up that string
# and find the actual executable function.

tools = [annualized_vol, vol_breakeven]
tool_map = {t.name: t for t in tools}

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
llm_with_tools = llm.bind_tools(tools)

messages = [
    SystemMessage(content="""
You are an FX volatility research assistant.

Use ReAct style internally:
1. Reason about what is needed.
2. Call tools when calculations are required.
3. Observe tool results.
4. Continue until you can give a final answer.

Do not reveal private chain-of-thought. Give concise reasoning summary only.
"""),
    HumanMessage(content="""
EURUSD implied vol is 8.0%.
Recent daily returns are:
0.005, -0.004, 0.006, -0.003, 0.004

Should I consider buying gamma?
""")
]

# 3. The Orchestration (The "ReAct" Loop)
# The for step in range(5) loop is the "brain" of the agent. Here is the sequence of events in every iteration:

# Reasoning: The LLM receives the messages list. It looks at the history and decides: "I have the returns, but I need the realized vol to answer the user. 
# I should call annualized_vol."

# Tool Request: llm_with_tools.invoke(messages) returns an AIMessage containing tool_calls.

# Execution: Your Python code loops through those tool_calls, pulls the arguments (the returns string), and runs the local Python function 
# (tool_map[tool_name].invoke(tool_args)).

# Observation: You create a ToolMessage. This is essential—it tells the LLM: "Here is the result of that tool you asked for."

# Iteration: The loop starts again. Now the LLM sees the original question and the calculation result. It then decides if it has enough info to provide the Final Answer.



# ReAct loop (This is the core of ReAct-style agent execution.)
# Ask model what to do next
# If it wants a tool, execute tool
# Return observation to model
# Repeat
# Stop when no tool is needed

for step in range(5):
    ai_msg = llm_with_tools.invoke(messages)
    messages.append(ai_msg)

    print(f"\n--- STEP {step + 1} ---")
    print("AI content:", ai_msg.content)
    print("Tool calls:", ai_msg.tool_calls)

    # Stopping Condition: The if not ai_msg.tool_calls: break line is the exit strategy. 
    # Once the AI stops asking for tools and starts talking to the human, the loop ends.
    if not ai_msg.tool_calls:
        break

    for tool_call in ai_msg.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        tool_result = tool_map[tool_name].invoke(tool_args)

        print(f"Tool used: {tool_name}")
        print(f"Tool result: {tool_result}")

        # State Management: By appending every message to the messages list, you are maintaining the "short-term memory" of the agent.
        messages.append(
            ToolMessage(
                content=str(tool_result),
                tool_call_id=tool_call["id"]
            )
        )
    print ('Step', step)

print("\nFINAL ANSWER:")
print(messages[-1].content)




""" 
-- STEP 1 ---
AI content: 
Tool calls: [{'name': 'annualized_vol', 'args': {'returns_csv': '0.005,-0.004,0.006,-0.003,0.004'}, 'id': 'call_ruOqvJNke9sdQnZBbS5Q3OGk', 'type': 'tool_call'}, 
{'name': 'vol_breakeven', 'args': {'implied_vol': 8.0, 'realized_vol': 0}, 'id': 'call_F8P0Wzhek1lQfA7rYfc8oqnE', 'type': 'tool_call'}]
Tool used: annualized_vol
Tool result: 0.07496399135585032
Tool used: vol_breakeven
Tool result: Realized vol is lower by 800.00%. Long gamma may struggle.
Step 0

--- STEP 2 ---
AI content: The annualized realized volatility from the recent daily returns is approximately 7.50%. Since the implied volatility is 8.0%, 
the realized volatility is significantly lower by 800%. This suggests that buying gamma may struggle to be profitable under current conditions.
Tool calls: []
>>> print("\nFINAL ANSWER:")

FINAL ANSWER:
>>> print(messages[-1].content)
The annualized realized volatility from the recent daily returns is approximately 7.50%. Since the implied volatility is 8.0%, 
the realized volatility is significantly lower by 800%. This suggests that buying gamma may struggle to be profitable under current conditions. """
