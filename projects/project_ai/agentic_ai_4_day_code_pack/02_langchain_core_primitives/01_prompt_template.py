from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a macro quant assistant."),
    ("human", "Explain {concept} using a {style} style."),
])

messages = prompt.invoke({"concept": "RAG", "style": "trading infrastructure"})
print(messages)
print(messages.content)

"""
>>> print(messages)
messages=[SystemMessage(content='You are a macro quant assistant.', additional_kwargs={}, response_metadata={}),
           HumanMessage(content='Explain RAG using a trading infrastructure style.', additional_kwargs={}, response_metadata={})]

The error occurs because prompt.invoke() does not return a single message; it returns a ChatPromptValue object. This is a wrapper that 
LangChain uses so it can easily convert the prompt into different formats (like a raw string or a list of message objects) depending on what the LLM expects.

Here is the breakdown of why your code failed and how to fix it.

1. The "Object" vs. "Content" Problem
When you call prompt.invoke(...), you aren't talking to the AI yet—you are just "filling in the blanks" of your template.

messages: This is a ChatPromptValue object. Think of it as a container.

messages.to_messages(): This extracts the list of SystemMessage and HumanMessage objects.

messages.to_string(): This converts the whole thing into a single block of text.

The error AttributeError: 'ChatPromptValue' object has no attribute 'content' happened because a container doesn't have "content"—only the individual messages inside it do.

"""

"""
Object                          Type                Accessing Text
prompt.invoke()                 ChatPromptValue     .to_string() or .to_messages()
messages.to_messages()[0]       SystemMessage       .content
llm.invoke()                    AIMessage           .content
"""



# If you want to see the formatted messages, you have two main options:
# This returns the list of message objects
formatted_messages = messages.to_messages()

print(formatted_messages[0].content) # "You are a macro quant assistant."
print(formatted_messages[1].content) # "Explain RAG using a trading infrastructure style."

"""
>> print(formatted_messages[0].content) # "You are a macro quant assistant."
You are a macro quant assistant.
>>> print(formatted_messages[1].content) # "Explain RAG using a trading infrastructure style."
Explain RAG using a trading infrastructure style.
>>> 
"""

#############################################################################################################################################
# 3. The Big Picture: Where this fits in a Chain
# In a real LangChain pipeline, you rarely need to call .content on the prompt value yourself. You usually pipe it directly into the LLM, 
# which knows exactly how to handle that ChatPromptValue object.

#############################################################################################################################################

# The 'messages' object from your code is passed automatically to the LLM
chain = prompt | llm 

# The LLM knows how to 'unpack' the ChatPromptValue
response = chain.invoke({"concept": "RAG", "style": "trading infrastructure"})

print(response.content) # This works because response is an AIMessage


"""
RAG, which stands for "Red, Amber, Green," is a color-coded system often used in project management and performance tracking to indicate the status of various elements. 
In a trading infrastructure context, RAG can be applied to assess the health and performance of trading systems, strategies, or market conditions. 
Here’s how RAG can be structured within a trading infrastructure:

### 1. **Red (Critical Issues)**
- **Definition**: Indicates a critical problem that requires immediate attention.
- **Examples in Trading Infrastructure**:
  - **System Downtime**: Trading platforms or critical components (like order management systems) are non-operational, leading to halted trading activities.
  - **High Latency**: Significant delays in trade execution or data feeds that could lead to slippage and poor execution prices.
  - **Regulatory Compliance Failures**: Issues that could lead to legal penalties or trading halts due to non-compliance with regulations.
  - **Market Risk Alerts**: Extreme market conditions (e.g., flash crashes) that pose a significant risk to trading strategies.

### 2. **Amber (Caution Required)**
- **Definition**: Indicates potential issues that need monitoring and may require action if they worsen.
- **Examples in Trading Infrastructure**:
  - **Performance Degradation**: Systems are functioning but showing signs of stress, such as increased latency or reduced throughput.
  - **Market Volatility**: Increased volatility in the markets that could affect trading strategies, requiring adjustments or hedging.
  - **Resource Utilization**: High CPU or memory usage on trading servers that could lead to performance issues if not addressed.
  - **Compliance Monitoring**: Minor compliance issues that need to be resolved but are not immediately threatening.

### 3. **Green (Healthy Status)**
- **Definition**: Indicates that everything is functioning well and within acceptable parameters.
- **Examples in Trading Infrastructure**:
  - **System Performance**: Trading systems are operating efficiently with low latency and high uptime.
  - **Market Conditions**: Stable market conditions that align with the trading strategy, allowing for optimal execution.
  - **Compliance Adherence**: All regulatory requirements are being met, and there are no outstanding compliance issues.
  - **Resource Availability**: Adequate resources (e.g., bandwidth, server capacity) are available to support trading activities without risk of overload.

### Implementation in Trading Infrastructure
- **Dashboards**: RAG status can be visualized on dashboards that provide real-time insights into the health of trading systems, allowing traders and managers 
to quickly assess the situation.
- **Alerts and Notifications**: Automated alerts can be set up to notify relevant teams when a system or market condition shifts from green to amber or red, 
prompting immediate investigation and action.
- **Regular Reviews**: Periodic reviews of RAG statuses can help in identifying trends, preparing for potential issues, and ensuring that the trading infrastructure 
remains robust and responsive.

### Conclusion
Using the RAG system in a trading infrastructure context allows for a clear and concise way to communicate the status of various components, enabling quick 
decision-making and prioritization of resources to address critical issues. This structured approach helps maintain operational efficiency and manage risks effectively in a fast-paced trading environment.

"""