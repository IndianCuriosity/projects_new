

##################################################################################################################################################
# This code demonstrates one of the most powerful features of LangGraph: Parallel Execution (also known as "Fan-out/Fan-in").
# Instead of running steps one after another in a straight line, this graph runs the macro and quant nodes at the same time (parallel) 
# and then merges their results in the combine node.

# This script demonstrates a parallel-branch workflow in LangGraph. Instead of routing to one node (like your previous example), 
# the graph runs multiple nodes simultaneously, then merges their outputs into a final answer.

    # Conceptually:
        # Question
        #    ↓
        #  ┌───────┬────────┐
        # Macro   Quant   (run in parallel)
        #  └───────┴────────┘
        #         ↓
        #      Combine
        #         ↓
        #        END

# This pattern is extremely important for multi-perspective agent design (e.g., macro + quant + risk + execution views).
    
##################################################################################################################################################
from typing import TypedDict
# Import LangGraph primitives

# These define the workflow structure:
    # | Element    | Meaning         |
    # | ---------- | --------------- |
    # | START      | entry point     |
    # | END        | termination     |
    # | StateGraph | workflow engine |


from langgraph.graph import StateGraph, START, END

# 2. State Merging : Define shared graph state
    #     The State TypedDict acts as the shared memory structure.
        #     The macro node updates the macro_view key.
        #     The quant node updates the quant_view key.
    #     Because LangGraph uses a Reducer pattern (by default, it performs a shallow merge of dictionaries), the two nodes don't overwrite each other. 
    #     They each fill in their respective "slot" in the state.
   
    # Each node:
        # reads from State
        # writes back into State

    # Example runtime state:
        # {
        # "question": "Evaluate long gamma",
        # "macro_view": "...",
        # "quant_view": "...",
        # "final": "..."
        # }
    # Think of this as a shared blackboard 🧠 where nodes collaborate.
class State(TypedDict):
    question: str
    macro_view: str
    quant_view: str
    final: str

# Define macro-analysis node
    # This node writes:
        # macro_view
    # into the shared state.
    # After execution:
        # {
        #   "macro_view": "Macro: event risk is high."
        # }
    # is added to state.

def macro(state):
    return {"macro_view": "Macro: event risk is high."}

# Define quant-analysis node
    # This node writes:
        # quant_view
    # into state.
    # Now state contains:
        # {
        #   "macro_view": "...",
        #   "quant_view": "..."
        # }
def quant(state):
    return {"quant_view": "Quant: compare implied vs realized and theta."}

# Define combine node
    # This node:
        # reads outputs from previous nodes
        # merges them
        # writes final answer
    # Example output:
        # {
        #   "final":
        #   "Macro: event risk is high.
        #    Quant: compare implied vs realized and theta."
        # }

    # So this node acts like an aggregator

def combine(state):
    return {"final": state["macro_view"] + "\n" + state["quant_view"]}

# Create graph builder: This initializes a workflow that operates on the State schema.
b = StateGraph(State)

# Register nodes
    # Graph now contains three nodes:
        # macro
        # quant
        # combine
b.add_node("macro", macro)
b.add_node("quant", quant)
b.add_node("combine", combine)


# 1. The Parallel Architecture: Connect START → macro and START → quant
    # In a standard chain, the "Macro" analysis would have to finish before the "Quant" analysis starts. Here, you've connected START to two different nodes:
    # When the graph starts, LangGraph sees that both nodes are ready to run. In a multi-threaded or production environment, these could run 
    # simultaneously on different servers, significantly speeding up the total response time.
    # This is the key idea. Unlike routing graphs, this creates parallel execution:
        # START
        #  ├── macro
        #  └── quant
    # Both nodes run independently but share state.
b.add_edge(START, "macro")
b.add_edge(START, "quant")

# 3. The Synchronization Point (Fan-in): Connect macro + quant → combine
    # The combine node acts as a "barrier" or "join" point:
    # The combine node will wait until both macro and quant have finished their work before it executes. This ensures that when combine looks 
    # at state["macro_view"] and state["quant_view"], both values are guaranteed to be present.
        # macro completes
        # quant completes
        # ↓
        # combine executes

    # This is a synchronization barrier.
b.add_edge("macro", "combine")
b.add_edge("quant", "combine")

# Connect combine → END
    # Graph stops after combine executes.
    
    # Full workflow now:
    #         START
    #         /   \
    #    macro   quant
    #         \   /
    #        combine
    #           |
    #          END

b.add_edge("combine", END)

# 4. Step-by-Step Execution
    # START: The graph triggers both macro and quant.
    # Parallel Work:
        # macro produces: "Macro: event risk is high."
        # quant produces: "Quant: compare implied vs realized and theta."
    # Merge: The state now contains both views.
    # Combine: The combine node runs, concatenating the two strings into the final key.
    # END: The graph returns the complete state.

    # Compile graph
        # b.compile()
        # Transforms graph definition into executable workflow engine.
        # Equivalent to:
            # build agent runtime
    # Execute graph
        # .invoke({"question": "Evaluate long gamma"})
            # Initial state:

            #     {
            #     "question": "Evaluate long gamma"
            #     }

    # Final output: Returns full state:
        #     {
        #     "question": "Evaluate long gamma",
        #     "macro_view": "Macro: event risk is high.",
        #     "quant_view": "Quant: compare implied vs realized and theta.",
        #     "final": "Macro: event risk is high.\nQuant: compare implied vs realized and theta."
        #     }

print(b.compile().invoke({"question": "Evaluate long gamma"}))

"""
>>> print(b.compile().invoke({"question": "Evaluate long gamma"}))
{'question': 'Evaluate long gamma', 'macro_view': 'Macro: event risk is high.', 
'quant_view': 'Quant: compare implied vs realized and theta.', 
'final': 'Macro: event risk is high.\nQuant: compare implied vs realized and theta.'}

"""


# Why use this for Finance/Quant work?
    # In complex research, you often have different "experts" (models) that don't need to talk to each other to do their initial jobs.
        # Expert A checks technical indicators.
        # Expert B checks fundamental news.
        # Expert C checks sentiment analysis.
    # Running these in parallel saves time and keeps the logic for each expert clean and isolated.



# Summary of Graph Flow
    # Node,               Type,               Input,                              Output
    # ------------------------------------------------------------------------------------------
    # macro,              Parallel Worker,    question,                           macro_view
    # quant,              Parallel Worker,    question,                           quant_view
    # combine,            Aggregator,         "macro_view, quant_view",           final


# Why this pattern matters for Agentic AI mastery

    # This is the foundation of multi-agent collaboration workflows.
    # Example production architecture:

        # User question
        #    ↓
        #  ┌──────────┬──────────┬──────────┐
        # Macro     Quant      Risk
        # analysis  analysis   analysis
        #  └──────────┴──────────┴──────────┘
        #             ↓
        #          Synthesizer
        #             ↓
        #           Output

    # So your example implements:
        # parallel reasoning agents
        # +
        # state synchronization
        # +
        # final aggregation

    # which is a core LangGraph design pattern for building institution-grade research copilots
        