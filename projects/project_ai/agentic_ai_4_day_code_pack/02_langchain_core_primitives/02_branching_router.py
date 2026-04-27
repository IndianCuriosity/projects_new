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

from typing import Literal
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# Defining the Schema (Route)
# The code uses Pydantic to define a strict structure for the router's output.
# By using Literal, you are forcing the LLM to choose exactly one of these three strings. This prevents the model from hallucinating a category like "math" or "history."
class Route(BaseModel):
    route: Literal["code", "finance", "general"]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# The Structured Router
# The .with_structured_output() method is a powerful feature. It leverages "tool calling" (or function calling) under the hood to ensure the LLM returns a 
# Python object (Route) rather than just a block of text. This makes it safe to use in programmatic logic like if/else statements.
router = llm.with_structured_output(Route)


# The Routing Logic
# The answer function follows a three-step process:
def answer(user_input: str):
    # Classification: It sends the user input to the LLM to determine the category.
    route = router.invoke(f"Classify this query: {user_input}").route

    # System Prompt Assignment: Based on that category, it selects a specific personality:
    if route == "code":
        system = "You are a Python coding tutor."
    elif route == "finance":
        system = "You are a macro quant research assistant."
    else:
        system = "You are a general assistant."

    # Dynamic Execution: It builds a new prompt using that specific persona and calls the LLM again to get the final answer.
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", "{input}")
    ])

    return (prompt | llm).invoke({"input": user_input}).content

print(answer("Write Python code for rolling FX volatility."))



""" 
To calculate rolling FX (foreign exchange) volatility, you typically want to compute the standard deviation of the logarithmic returns of the 
exchange rate over a specified rolling window. Below is a Python code example that demonstrates how to do this using the `pandas` library.

First, ensure you have the necessary libraries installed. You can install them using pip if you haven't already:

```bash
pip install pandas numpy
```

Here's a sample code to calculate rolling FX volatility:

```python
import pandas as pd
import numpy as np

# Sample data: Create a DataFrame with FX rates
# For demonstration, let's create a DataFrame with random FX rates
np.random.seed(42)  # For reproducibility
dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
fx_rates = np.random.uniform(low=1.0, high=1.5, size=len(dates))  # Random FX rates
fx_data = pd.DataFrame(data=fx_rates, index=dates, columns=['FX_Rate'])

# Calculate logarithmic returns
fx_data['Log_Returns'] = np.log(fx_data['FX_Rate'] / fx_data['FX_Rate'].shift(1))

# Define the rolling window size (e.g., 20 days)
window_size = 20

# Calculate rolling volatility (standard deviation of log returns)
fx_data['Rolling_Volatility'] = fx_data['Log_Returns'].rolling(window=window_size).std() * np.sqrt(252)  # Annualize the volatility

# Display the results
print(fx_data.tail(30))  # Show the last 30 rows of the DataFrame
```

### Explanation:
1. **Data Generation**: In this example, we generate random FX rates for demonstration purposes. In a real-world scenario, you would typically load this data from a financial data source (e.g., CSV file, API).
  
2. **Logarithmic Returns**: We calculate the logarithmic returns using the formula:
   \[
   \text{Log Return} = \log\left(\frac{\text{Current Rate}}{\text{Previous Rate}}\right)
   \]

3. **Rolling Volatility**: We compute the rolling standard deviation of the logarithmic returns over a specified window (e.g., 20 days). The result is then annualized by multiplying by the square root of 252 (the typical number of trading days in a year).

4. **Output**: Finally, we print the last 30 rows of the DataFrame to see the calculated rolling volatility.

You can adjust the `window_size` variable to change the length of the rolling window as needed.
 """