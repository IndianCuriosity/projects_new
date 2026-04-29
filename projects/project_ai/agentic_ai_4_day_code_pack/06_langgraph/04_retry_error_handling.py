
##################################################################################################################################################
# This code demonstrates a Looping Workflow in LangGraph. Unlike a linear chain that only moves forward, this graph can "circle back" to a previous 
# node based on a specific condition. This is the foundation for building Self-Correcting Agents or Retry Logic.

# Here is the breakdown of how this "Cyclic Graph" works:
##################################################################################################################################################

from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    attempts: int
    status: str


# 1. The Looping Logic
    # The "magic" happens in the unstable_node and the route function.
        # unstable_node: This node simulates a process that might fail or need multiple passes. It increments a counter (attempts) and sets a status.
        # route (The Traffic Cop): This function looks at the status in the state and decides where to send the flow next.
    # This simulates a node that may fail initially.

    #     Example real-world equivalents:

    #         API call
    #         database lookup
    #         vector retrieval
    #         tool execution
    #         model reasoning step
def unstable_node(state):
    attempts = state.get("attempts", 0) + 1
    if attempts < 2:
        return {"attempts": attempts, "status": "retry"}
    return {"attempts": attempts, "status": "success"}

def done(state):
    return {"status": f"completed after {state['attempts']} attempts"}

def route(state):
    return "retry" if state["status"] == "retry" else "done"

b = StateGraph(State)
b.add_node("unstable", unstable_node)
b.add_node("done", done)


b.add_edge(START, "unstable")

# 2. The Conditional Edge (The Decision Point)
    # The line b.add_conditional_edges("unstable", route, ...) creates a feedback loop:
        # First Run: attempts becomes 1. status is set to "retry".
        # Routing: The route function sees "retry" and points back to "unstable".
        # Second Run: The graph enters the "unstable" node again. attempts becomes 2. status is set to "success".
        # Exit: The route function sees "success", sends the flow to the "done" node, and then to END.

b.add_conditional_edges("unstable", route, {"retry": "unstable", "done": "done"})
b.add_edge("done", END)

print(b.compile().invoke({"attempts": 0, "status": ""}))



# # 3. Step-by-Step Execution Trace
# ----------------------------------------------------------------------------------------------------------------
# # Step,         Current Node,               attempts,       status,                                     Next Step
# # Start,        START,                      0,              """""",                                     Go to unstable
# # 1,            unstable,                   1,              """retry""",                                Loop back to unstable
# # 2,            unstable,                   2,              """success""",                              Go to done
# # 3,            done,                       2,              """completed after 2 attempts""",           Go to END



# 4. Why is this useful?
    # In real AI applications, you use this pattern for Self-Reflection:
        # Step 1: The AI generates code.
        # Step 2: A "Tester" node runs the code and finds an error.
        # Step 3: The graph loops back to the AI node with the error message.
        # Step 4: The AI fixes the code and tries again until it passes the test.


# Summary Table
# --------------------------

# Component,          Role in this Graph
# ----------------------------------
# State,              Tracks the attempts counter across loops.
# Node,               unstable_node acts as the worker that updates the counter.
# Edge,               "The conditional edge creates the ""cycle"" or loop."
# Termination,        The logic eventually points to END once attempts >= 2.


# This is a very safe loop because it has a clear exit condition. Without that attempts < 2 check, you would create an Infinite Loop that would run until you ran out of
# memory or API credits!




# Why retry loops are critical in Agentic AI systems
    # This pattern appears everywhere in production agents:
    # Example workflow:
        # Call tool
        # ↓
        # Did tool succeed?
        #    YES → continue
        #    NO → retry

    # Real examples:

        # Scenario	                Retry target
        # ----------------------------------------------
        # API timeout	            retry request
        # vector retrieval empty	expand query
        # tool output invalid	    re-run tool
        # LLM format wrong	        regenerate
        # evaluation fails	        refine answer

    # So your graph implements:
        # self-healing execution loop
    # which is a core building block of robust LangGraph agents.

