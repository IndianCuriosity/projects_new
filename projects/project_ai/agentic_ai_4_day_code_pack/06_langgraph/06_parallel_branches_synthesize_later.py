
##################################################################################################################################################
# Integrating an LLM into the combine node transforms your graph from a simple string concatenator into a Synthesis Engine.

# In this setup, the LLM acts as the "Senior Researcher" who takes the raw notes from the Macro and Quant specialists and polishes them into a cohesive final report.

# Why this is a "Production-Grade" Pattern
    # 1. Context Separation
    # By keeping the specialists separate, you prevent the LLM from getting "distracted." The macro specialist focuses purely on the calendar and news, 
    # while the quant specialist focuses purely on the Greeks and data. This leads to higher accuracy in each component.

    # 2. The "Senior Editor" Effect
    # LLMs are excellent at merging conflicting or dense information. If the Quant view says "Sell" but the Macro view says "Buy because of a tail risk," 
    # the synthesiser node can weigh both and provide a balanced recommendation (e.g., "Stay long gamma but hedge the theta decay using a calendar spread").

    # 3. Structured Data flow
    # Notice how the final_report is added to the state. In a larger system, you could add another node after synthesis that automatically emails 
    # this report to a user or posts it to a Slack channel.

##################################################################################################################################################


from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# 1. Define the State
class State(TypedDict):
    question: str
    macro_view: str
    quant_view: str
    final_report: str

# 2. Initialize the LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 3. Define the Nodes
def macro_specialist(state: State):
    # In a real app, this would be an LLM call or API check
    return {"macro_view": "Event risk is high due to upcoming FOMC; volatility usually expands pre-announcement."}

def quant_specialist(state: State):
    return {"quant_view": "Current realized vol is 12% vs 15% implied; theta decay is accelerating."}

def synthesiser(state: State):
    """The LLM combines the parallel views into a polished report."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a senior macro quant strategist. Combine the following research notes into a concise, professional summary for a portfolio manager."),
        ("human", "Macro Notes: {macro}\nQuant Notes: {quant}\n\nOriginal Question: {question}")
    ])
    
    # Run the synthesis chain
    chain = prompt | llm
    response = chain.invoke({
        "macro": state["macro_view"],
        "quant": state["quant_view"],
        "question": state["question"]
    })
    
    return {"final_report": response.content}

# 4. Build the Graph
workflow = StateGraph(State)

workflow.add_node("macro", macro_specialist)
workflow.add_node("quant", quant_specialist)
workflow.add_node("synthesise", synthesiser)

# Parallel Fan-out
workflow.add_edge(START, "macro")
workflow.add_edge(START, "quant")

# Fan-in (Synchronization)
workflow.add_edge("macro", "synthesise")
workflow.add_edge("quant", "synthesise")

workflow.add_edge("synthesise", END)

# 5. Execute
app = workflow.compile()
result = app.invoke({"question": "Should I maintain a long gamma position?"})

print("--- FINAL RESEARCH NOTE ---")
print(result["final_report"])

# Summary of the Flow

# Step,               Process,                        Data Action
# Start,              System triggered,               question is initialized.
# Nodes 1 & 2,        Parallel Analysis,              macro_view and quant_view are populated simultaneously.
# Node 3,             LLM Synthesis,                  final_report is generated using data from both specialists.
# End,                Graph Completion,               The Portfolio Manager receives a polished report.


"""
>>> print(result["final_report"])
**Summary for Portfolio Manager:**

As we approach the upcoming FOMC meeting, event risk is elevated, which typically leads to increased market volatility in the pre-announcement period. 
Current market conditions show realized volatility at 12%, below the 15% implied volatility, indicating a potential for volatility expansion. Additionally, 
we are observing an acceleration in theta decay, which may impact the profitability of long gamma positions.

Given these factors, maintaining a long gamma position could be beneficial in capturing potential volatility spikes leading up to the FOMC announcement. 
However, we should closely monitor the theta decay and adjust our strategy accordingly to optimize risk and return.


"""