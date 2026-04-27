"""
Manual tool execution pattern:
The model proposes a tool call; Python executes it.
"""

import math
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage

@tool
def realized_vol(daily_returns_csv: str) -> float:
    """Calculate annualized realized volatility from comma-separated daily returns."""
    rs = [float(x.strip()) for x in daily_returns_csv.split(",")]
    mean = sum(rs) / len(rs)
    var = sum((x - mean) ** 2 for x in rs) / (len(rs) - 1)
    return math.sqrt(var) * math.sqrt(252)

tools = [realized_vol]
tool_map = {t.name: t for t in tools}

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(tools)

messages = [
    ("user", "Calculate realized vol for: 0.01, -0.004, 0.006, -0.002, 0.003")
]

ai_msg = llm.invoke(messages)
print("AI proposed:", ai_msg.tool_calls)

messages.append(ai_msg)

for call in ai_msg.tool_calls:
    result = tool_map[call["name"]].invoke(call["args"])
    messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))

final = llm.invoke(messages)
print(final.content)
