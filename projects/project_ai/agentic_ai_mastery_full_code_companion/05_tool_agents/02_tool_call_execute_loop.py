import math
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage
from langchain_openai import ChatOpenAI

@tool
def realized_vol(returns_csv: str) -> float:
    """Calculate annualized realized volatility."""
    rs = [float(x.strip()) for x in returns_csv.split(",")]
    mean = sum(rs) / len(rs)
    var = sum((x - mean) ** 2 for x in rs) / (len(rs) - 1)
    return math.sqrt(var) * math.sqrt(252)

tools = [realized_vol]
tool_map = {t.name: t for t in tools}
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(tools)

messages = [("user", "Calculate RV for 0.004,-0.003,0.006,-0.002")]
ai = llm.invoke(messages)
messages.append(ai)

for call in ai.tool_calls:
    result = tool_map[call["name"]].invoke(call["args"])
    messages.append(ToolMessage(str(result), tool_call_id=call["id"]))

print(llm.invoke(messages).content)
