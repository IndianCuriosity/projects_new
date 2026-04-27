"""
Tool calling:
Expose deterministic Python functions to the model.
"""

""" 
The important flow is:

User asks question
   ↓
LLM returns tool_call
   ↓
Your Python code executes the tool
   ↓
You send ToolMessage back to LLM
   ↓
LLM gives final natural-language answer 

bind_tools() only lets the LLM request a tool call. It does not automatically execute the tool.

"""

import math
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage

@tool
def annualized_vol(daily_returns_csv: str) -> float:
    """Calculate annualized volatility from comma-separated daily returns."""
    returns = [float(x.strip()) for x in daily_returns_csv.split(",")]
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    return math.sqrt(variance) * math.sqrt(252)

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

tools = [annualized_vol]
tool_map = {tool.name: tool for tool in tools}

llm_with_tools = llm.bind_tools(tools)

messages = [
    ("user", "Calculate annualized vol for returns: 0.01, -0.004, 0.006, -0.002, 0.003")
]

# Step 1: LLM decides whether to call a tool
ai_msg = llm_with_tools.invoke(messages)

print("AI message content:", ai_msg.content)
print("Tool calls:", ai_msg.tool_calls)

# Step 2: Execute requested tool calls
messages.append(ai_msg)

for tool_call in ai_msg.tool_calls:
    selected_tool = tool_map[tool_call["name"]]
    tool_output = selected_tool.invoke(tool_call["args"])

    messages.append(
        ToolMessage(
            content=str(tool_output),
            tool_call_id=tool_call["id"]
        )
    )

# Step 3: Send tool result back to LLM
final_msg = llm_with_tools.invoke(messages)

print("Final answer:")
print(final_msg.content)



""" 

>> print("AI message content:", ai_msg.content)
AI message content: 
>>> print("Tool calls:", ai_msg.tool_calls)
Tool calls: [{'name': 'annualized_vol', 'args': {'daily_returns_csv': '0.01,-0.004,0.006,-0.002,0.003'}, 'id': 'call_gGT2mSlO15SZmye1UvigzbiR', 'type': 'tool_call'}]

>>> print("Final answer:")
Final answer:
>>> print(final_msg.content)
The annualized volatility for the given returns is approximately 0.0909, or 9.09%.

 """

################################ wrong way of calling ##########################################

import math
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

@tool
def annualized_vol(returns_csv: str) -> float:
    """Calculate annualized volatility from comma-separated daily returns."""
    rs = [float(x.strip()) for x in returns_csv.split(",")]
    mean = sum(rs) / len(rs)
    var = sum((x - mean) ** 2 for x in rs) / (len(rs) - 1)
    return math.sqrt(var) * math.sqrt(252)

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
llm_with_tools= llm.bind_tools([annualized_vol])

msg = llm_with_tools.invoke("Calculate vol for 0.01, -0.004, 0.006, -0.002, 0.003")
print("Content may be empty:", repr(msg.content))
print("Tool calls:", msg.tool_calls)

"""
Technically, there is nothing "broken" in the code—it runs without error. However, logically and practically, there is a fundamental "issue" with how 
LLMs handle tool calls that often surprises developers.

Here is the breakdown of what is happening and how to fix it:

1. The "Empty Content" Confusion
    When you run this code, msg.content will likely be an empty string ''.

    Why? Because the LLM has decided to call a tool instead of talking to you. In the OpenAI API, a message typically contains either 
    conversational text or a list of tool calls. Since it found a tool that matches your request perfectly, it skips the "chatter" and 
    goes straight to the structured request.

2. The Tool Isn't Actually Executed
    The biggest "gotcha" for beginners is thinking that llm.invoke() will run the Python function.

        What happens: The LLM returns a JSON plan (the tool_calls) saying, "Hey, please run annualized_vol with these specific arguments."

        What doesn't happen: The LLM does not execute the Python code itself. You are responsible for taking that JSON, running the function, and passing the result back to the LLM.




"""

# How to make it work (The Manual Way)
# To get an actual answer, you have to bridge the gap between the LLM's "request" and your Python "function":

# 1. Get the tool call from the LLM
tool_call = msg.tool_calls[0]

# 2. Extract the arguments (it's a dictionary)
args = tool_call['args']

# 3. Actually execute your Python tool
result = annualized_vol.invoke(args)

# 4. (Optional) Feed the result back to the LLM so it can give you a sentence
# This requires a second invoke or using a LangChain Agent
print(f"The calculated volatility is: {result}")

################################ Pro Fix : Use an Agent ##########################################


# First, run: pip install langgraph

from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
import math

# Your tool
@tool
def annualized_vol(returns_csv: str) -> float:
    """Calculate annualized volatility from comma-separated daily returns."""
    rs = [float(x.strip()) for x in returns_csv.split(",")]
    mean = sum(rs) / len(rs)
    var = sum((x - mean) ** 2 for x in rs) / (len(rs) - 1)
    return math.sqrt(var) * math.sqrt(252)

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# In LangGraph, create_react_agent handles the loop for you:
# 1. Ask LLM -> 2. Call Tool -> 3. Pass Result back to LLM -> 4. Final Answer
app = create_react_agent(llm, tools=[annualized_vol])

# Execute
query = "Calculate vol for 0.01, -0.004, 0.006, -0.002, 0.003"
result = app.invoke({"messages": [("human", query)]})

# The result contains the whole conversation history
# The last message is the final answer
print(result["messages"][-1].content)
