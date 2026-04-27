"""
Router pattern:
Classify intent first, then route the request to the right expert prompt.

This code demonstrates a Semantic Router using LangChain. Instead of treating every user question the same way, the script first "classifies" the intent 
and then routes the query to a specialized persona (a "tutor," an "assistant," etc.).

The Workflow Visualized : Why use this approach?
---------------------------------------------------------------
Precision: A "General Assistant" might give a surface-level answer to a finance question. A "Macro Quant Assistant" will use industry-specific terminology and 
more rigorous logic.

Efficiency: You can route difficult questions to a large model (like GPT-4o) and simple questions to a cheaper, faster model (like GPT-4o-mini).

Modularity: You can easily add a new route (e.g., "legal" or "medical") just by updating the Literal list and adding one elif block.

One quick tip: In your example, the input "Write Python code for rolling FX volatility" hits both code and finance. Because of how the LLM interprets the prompt, 
it likely chose code because of the explicit request for "Python code," but if you wanted the finance persona to handle it, you might need to adjust your 
classification prompt to prioritize domain over format!

"""

from langchain_core.runnables import RunnableLambda, RunnablePassthrough

class Route(BaseModel):
    """Route the user query to the most relevant specialized assistant."""
    route: Literal["code", "finance", "general"]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_router = llm.with_structured_output(Route)

# 1. Define your specialized prompts
prompts = {
    "code": ChatPromptTemplate.from_messages([("system", "You are a Python tutor."), ("human", "{input}")]),
    "finance": ChatPromptTemplate.from_messages([("system", "You are a macro quant assistant."), ("human", "{input}")]),
    "general": ChatPromptTemplate.from_messages([("system", "You are a general assistant."), ("human", "{input}")])
}

# 2. The routing function
def route_query(input_data):
    # input_data now contains both 'destination' and 'original_input'
    destination = input_data["destination"].route
    original_input = input_data["original_input"]

      # Select prompt and return the sub-chain

    prompt = prompts.get(destination, prompts['general'])
    chain = prompt | llm
    return chain.invoke({"input": original_input})


# 3. The Unified Chain
# We use a dictionary in the chain to keep track of the input string 
# while the router does its work.
# We need to pass both the classification and the original input down the chain.
# RunnablePassthrough(): This is a LangChain tool that essentially says "take whatever input came into this step and pass it through unchanged."
# Input Mapping: Instead of full_chain = router | ..., I used a dictionary:
    # "destination": Runs the router to classify the text.
    # "original_input": Keeps the actual question ("Write Python code...") available.
# Data Extraction: Inside route_query, I updated it to pull the route from input_data["destination"] and the question from input_data["original_input"]
# Why this matters
    # In LCEL, each pipe (|) passes its output to the next function. If the first step is just router, the second step only sees {route: 'code'}. 
    # It has no idea what the user actually asked! By using the dictionary structure, you ensure the user's question "survives" the classification step.

full_chain = ({"destination": structured_router, "original_input": RunnablePassthrough()} | RunnableLambda(route_query))

# Execute
# Note: Since the final step of route_query returns a chain (prompt | llm), 
# invoking the full_chain executes that final sub-chain.
result = full_chain.invoke("Write Python code for rolling FX volatility.")
print(result.content)



###################################################### Main implementation #################################################

from typing import Literal
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

# --- 1. Schema Setup ---
class Route(BaseModel):
    """Route the user query to the most relevant specialized assistant."""
    route: Literal["code", "finance", "general"]

# --- 2. Model & Router Initialization ---
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_router = llm.with_structured_output(Route)

# --- 3. Prompt Library ---
# We store these in a dictionary to map the 'route' string to a PromptTemplate
prompt_map = {
    "code": ChatPromptTemplate.from_messages([
        ("system", "You are an expert Python coding tutor. Focus on PEP 8 standards and clarity."),
        ("human", "{input}")
    ]),
    "finance": ChatPromptTemplate.from_messages([
        ("system", "You are a macro quant research assistant specializing in derivatives and risk."),
        ("human", "{input}")
    ]),
    "general": ChatPromptTemplate.from_messages([
        ("system", "You are a helpful and versatile general assistant."),
        ("human", "{input}")
    ])
}

# --- 4. Routing Logic ---
def routing_logic(classification_output):
    """
    Selects the correct prompt based on the LLM's classification.
    """
    selected_route = classification_output.route
    # Use .get() to provide a 'general' fallback safely
    # Dictionary Mapping: By using prompt_map.get(), we avoid long if/else chains. If you want to add a "Legal" route tomorrow, you just add one 
    # line to the Literal and one line to the prompt_map.

    prompt = prompt_map.get(selected_route, prompt_map["general"])
    
    # Return the chain for the next step: Prompt | LLM
    return prompt | llm

# --- 5. Constructing the Full LCEL Chain ---
# Step 1: Classify input -> Step 2: Pass classification to logic -> Step 3: Run final LLM call
# The Full Chain Pipe (|): The code reads like a workflow. It flows from Input -> Router -> Logic -> Final LLM.
# Encapsulation: The logic is self-contained. The full_chain object can now be easily imported into other files or used in an API (like FastAPI) with a single .invoke() call.

full_chain = (
    {"input": RunnableLambda(lambda x: x)}  # Pass the raw string through
    | RunnableLambda(lambda x: structured_router.invoke(f"Classify: {x['input']}"))
    | RunnableLambda(routing_logic)
)

# --- 6. Execution ---
if __name__ == "__main__":
    user_query = "Write Python code for rolling FX volatility."
    
    # Run the chain
    # Note: Because the chain returns an AIMessage, we access .content
    response = full_chain.invoke(user_query)
    
    print(f"--- Final Response ---\n")
    print(response.content)

