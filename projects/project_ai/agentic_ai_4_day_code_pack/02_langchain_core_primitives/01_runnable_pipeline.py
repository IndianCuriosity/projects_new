"""
Runnable pipeline:
Prompt -> LLM -> string parser.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_template(
    "Explain {topic} to a senior FX options trader in 5 bullet points."
)

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
chain = prompt | llm | StrOutputParser()
print(chain.invoke({"topic": "LangGraph state machines"}))


""" 

Certainly! Here’s a concise explanation of LangGraph state machines tailored for a senior FX options trader:

1. **State Representation**: LangGraph state machines model complex systems by representing different states (or conditions) of a system, 
    akin to how market conditions can change in FX trading. Each state can represent a specific market scenario or trading strategy.

2. **Transitions**: Just as market conditions can shift due to economic indicators or geopolitical events, state machines have defined transitions 
    that dictate how and when the system moves from one state to another. This can help in automating decision-making processes based on market signals.

3. **Event-Driven**: State machines operate on events, similar to how traders react to market movements or news releases. Each event can trigger a 
    transition, allowing the system to adapt dynamically to changing market conditions, which is crucial in the fast-paced FX options market.

4. **Hierarchical Structure**: LangGraph state machines can be organized hierarchically, allowing for complex strategies to be 
    broken down into simpler components. This mirrors how traders might develop layered strategies based on different market scenarios, making it 
    easier to manage and optimize trading approaches.

5. **Predictive Modeling**: By analyzing the state transitions and outcomes, LangGraph state machines can help in predicting future states 
    based on historical data, similar to how traders use past market behavior to forecast future price movements and make informed trading decisions in FX options. 

This framework can enhance decision-making and strategy development in the dynamic FX options market.

 """