"""
LangGraph basics:
A graph is made of nodes. Each node reads and updates shared state.
"""

##################################################################################################################################################
# This code introduces LangGraph, which is a library for building stateful, multi-step applications with AI. While standard LangChain is a linear "chain" 
# (A -> B -> C), LangGraph allows you to create loops and conditional logic using a graph structure.
# Think of this as a "Flowchart as Code."

##################################################################################################################################################
# Import LangGraph components
    # These define the workflow structure:
        # | Component  | Role             |
        # | ---------- | ---------------- |
        # | StateGraph | workflow builder |
        # | START      | entry node       |
        # | END        | exit node        |

    # So your graph looks like:
        # START → classify → route → finance/general → END
from langgraph.graph import StateGraph, START, END

# Define the shared state structure
    # In LangGraph, all data lives in a central State object. Every function (node) in the graph receives the current state, 
    # makes a small change, and passes it along. This is much cleaner than passing dozens of variables back and forth between functions.
    # LangGraph workflows pass around a state dictionary between nodes.
    
    # Here the state contains:
        # | Field          | Meaning        |
        # | -------------- | -------------- |
        # | question       | user input     |
        # | classification | routing label  |
        # | answer         | final response |

    # Example state during execution:
        # {
        # "question": "Explain EURUSD vol skew",
        # "classification": "finance",
        # "answer": "..."
        # }

    # Each node reads from state and writes to state.
from typing import TypedDict
class GraphState(TypedDict):
    question: str
    classification: str
    answer: str

# 2. The Nodes (The "Actions")
    # Nodes are simply Python functions.

        # classify: Looks at the question and decides the category. Notice it returns a dictionary {"classification": "..."}—
        # LangGraph automatically merges this into the main state.
        # answer_finance / answer_general: Specialized workers that only run if they are called


# Classification node: This node inspects the question and determines its type.
def classify(state: GraphState):
        # Convert to lowercase for keyword matching.
    q = state["question"].lower()
        # Detect finance-related topics.
    if "vol" in q or "option" in q:
            # So the updated state becomes:
                # {
                # "question": "...",
                # "classification": "finance"
                # }
        return {"classification": "finance"}
    
    # Important rule in LangGraph:
        # Nodes return only the fields they update.
    return {"classification": "general"}

# Finance-answer node: Runs only if classification == finance.
    # Returns:

        # {
        #   "answer": "This is a finance/options question..."
        # }

    # Now state becomes:

        # {
        #   "question": "...",
        #   "classification": "finance",
        #   "answer": "This is a finance/options question..."
        # }

def answer_finance(state: GraphState):
    return {"answer": "This is a finance/options question. Analyze spot, vol, skew, carry, and event risk."}

# General-answer node
    # Fallback node for non-finance questions.
        # Returns:

        # {
        #   "answer": "This is a general question."
        # }
def answer_general(state: GraphState):
    return {"answer": "This is a general question."}

# Routing logic node
    # This determines which branch the graph follows.
        # return "finance" if state["classification"] == "finance" else "general"
    # So routing decision depends on earlier node output.

        # Example:
            # classification = "finance"
        # returns:
            # "finance"
        # Graph jumps to finance node.

def route(state: GraphState):
    return "finance" if state["classification"] == "finance" else "general"


# Create graph builder: This initializes a graph that operates on: GraphState
# So every node must accept and return compatible state updates.
builder = StateGraph(GraphState)

# Register nodes

# Graph now has three nodes:
    #     classify
    #     finance
    #     general

# Each node is a function.

builder.add_node("classify", classify)
builder.add_node("finance", answer_finance)
builder.add_node("general", answer_general)



# 3. The Edges (The "Connections")
    # Edges define the flow of the program:
        # Normal Edges: builder.add_edge(START, "classify") tells the graph exactly where to begin.

        # Conditional Edges: This is the most powerful part. builder.add_conditional_edges uses the route function to act as a traffic cop, 
            # sending the state to either the "finance" node or the "general" node based on the data

# Connect START → classify :Execution begins here: START → classify
builder.add_edge(START, "classify")

# Add conditional routing
    # This is the most important LangGraph feature ⚡
    # After classify runs:

        # call route(state)
        # read returned label
        # jump to matching node
    # Graph continues:
        # classify → finance
builder.add_conditional_edges("classify", route, {
    "finance": "finance",
    "general": "general",
})

# Connect answer nodes to END
    # So execution stops after answer node.
    
    # Graph now looks like:
        #           ┌──────────┐
        # START → classify
        #           │
        #      ┌────┴────┐
        #  finance    general
        #      │           │
        #      └──── END ──┘

builder.add_edge("finance", END)
builder.add_edge("general", END)


# Compile the graph
    # Transforms workflow definition into executable object. Equivalent to: build agent runtime
graph = builder.compile()



# 4. Step-by-Step Execution: Execute the graph
    # When you run graph.invoke({"question": "Explain EURUSD vol skew"}):
        # START: The graph enters the classify node.
        # Classify: It sees the word "vol," updates the state to {"classification": "finance"}, and finishes.
        # Router: The route function checks the state, sees "finance," and points the flow toward the finance node.
        # Finance Node: The answer_finance function runs and adds the technical answer to the state.
        # END: The graph follows the final edge to END and returns the finished state dictionary.

    # Initial state:
        # {
        #   "question": "Explain EURUSD vol skew"
        # }

    # Execution sequence:
        # Step 1
            # Run:
                # classify()
            # Output:
                # {"classification": "finance"}
            # State becomes:
                # {
                #   "question": "...",
                #   "classification": "finance"
                # }
        # Step 2
            # Run:
                # route()
            # Returns:
                # "finance"
            # Graph jumps to finance node.
        # Step 3
            # Run:
                # answer_finance()
            # Output:
                # {
                #   "answer": "This is a finance/options question..."
                # }
            # Final state:
                # {
                #   "question": "Explain EURUSD vol skew",
                #   "classification": "finance",
                #   "answer": "This is a finance/options question..."
                # }

# Print result
print(graph.invoke({"question": "Explain EURUSD vol skew"}))

"""
>>> print(graph.invoke({"question": "Explain EURUSD vol skew"}))
{'question': 'Explain EURUSD vol skew', 'classification': 'finance', 'answer': 'This is a finance/options question. Analyze spot, vol, skew, carry, and event risk.'}
"""

# Why use LangGraph instead of a simple if/else?
    # Persistence: LangGraph can "save" the state of a conversation to a database between steps.
    # Human-in-the-loop: You can pause the graph at a specific node, wait for a human to approve the action, and then resume it.
    # Cycles: You can create loops (e.g., if the answer isn't good enough, go back to the "classify" node and try again).

# Summary Table: Graph Components
    # ------------------------------------------
    # Component,                    Purpose
    # State,                        The single source of truth (shared memory).
    # Node,                         A Python function that does work.
    # Edge,                         A fixed path between two nodes.
    # Conditional Edge,             A decision point (logic-based routing).




# Why this example matters for Agentic AI mastery
    # This is the core primitive behind LangGraph agents:

    # Instead of: single LLM call
    # you now have:
        # state
        # → classifier node
        # → router node
        # → specialist node
        # → output

    # Production systems extend this pattern into:

        # retriever node
        # tool node
        # planner node
        # risk node
        # execution node
        # memory node
        # evaluation node

    # So what you built here is essentially your first state-machine agent