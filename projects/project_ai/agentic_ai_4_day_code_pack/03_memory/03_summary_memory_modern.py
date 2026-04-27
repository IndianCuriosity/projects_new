"""
Modern replacement for ConversationSummaryMemory:
Maintain a rolling summary and inject it into the prompt.
"""
###################################################################################################
# This code implements Summarization Memory. Instead of deleting old messages (sliding window) or keeping all of them (raw history), 
# it periodically "combs" through the chat, condenses it into a short summary, and clears the message history.
# This is a professional strategy for long-running agents where you need to preserve core context without bloating the token count.
###################################################################################################


from langchain_openai import ChatOpenAI
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

# Create the LLM
# This model:
    # answers questions
    # generates summaries
    # updates memory compression

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Create memory storage
    # Two memory structures exist:
    # Raw message store
    #     store = {session_id → message history object}
    #         Example:
    #         store["summary"] =
    #             User: My name is Sugat
    #             AI: Nice to meet you

    # Summary store
    #     summaries = {session_id → compressed history string}
    #         Example:
    #         summaries["summary"] =
    #         User specializes in FX vol and wants Agentic AI mastery

store = {}
summaries = {}

# 1. The Core Mechanism: The "Trigger"
    # The variable TRIGGER_MESSAGES = 6 acts as a threshold.
    # The system allows the conversation to proceed naturally until there are 6 messages (3 back-and-forth turns) in the InMemoryChatMessageHistory.
    # Once hit, the summarize function is triggered.
# This prevents context window overflow.
TRIGGER_MESSAGES = 6

"""
summary_prompt = ChatPromptTemplate.from_template(
    "Existing summary:\n{summary}\n\nNew messages:\n{messages}\n\nUpdate the summary."
)

"""
# Define summarization prompt
# This tells the LLM:
    # Here is previous summary
    # Here are new messages
    # Update summary

# So summary evolves incrementally:
    # summary_t+1 = f(summary_t + new_messages)

summary_prompt = ChatPromptTemplate.from_template("""
Current summary:
{summary}

New conversation messages:
{messages}

Update the summary. Keep durable facts, preferences, goals, and decisions.
""")

# 2. How the Summarization Works
    # When the threshold is reached:
    # Extraction: It grabs the current summary and the New messages.
    # Compression: It asks the LLM to merge them into a single, updated summary.
    # Purge: It sets store[session_id].messages = []. The history is wiped clean, but the essence is saved in the summaries dictionary.

def summarize(session_id):
    #load previous summary

    # If no summary exists:
        #     old = ""
        #     Otherwise:
        #     old = previous conversation summary

    old = summaries.get(session_id, "")
    
    # collect recent messages
    messages = "\n".join(str(m) for m in store[session_id].messages)
    
    # generate updated summary
    summaries[session_id] = (summary_prompt | llm).invoke({"summary": old, "messages": messages}).content

    # clear raw message buffer. This keeps memory size small.
    # So now:
            #     raw history cleared
            #     summary preserved
    store[session_id].messages = []

# History retrieval function
    # This function is called automatically before each LLM execution.
def get_history(session_id):
        # create session if missing
        # Initialize:
            # store[session_id]
            # summaries[session_id]
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
        summaries[session_id] = ""
        # trigger summarization if needed. if conversation too long → compress it
    if len(store[session_id].messages) >= TRIGGER_MESSAGES:
        summarize(session_id)
        # return history: This feeds recent messages into prompt.
    return store[session_id]

# Prompt template using summary + history
    # Prompt becomes:

        # System: Conversation summary:
        # <User summary here>

        # History:
        # <recent messages>

        # User: latest question
    # So LLM sees both:
        # compressed long-term memory
        # +
        # short-term conversation buffer

prompt = ChatPromptTemplate.from_messages([
    ("system", "Conversation summary:\n{summary}"),
    MessagesPlaceholder("history"),
    ("human", "{input}"),
])

# 3. The Custom Chain Logic (add_summary)
# This part is quite clever. In standard memory chains, the prompt only looks at the "history" variable. Here, you've added a custom step:

# This function "injects" the current summary into the inputs before they hit the prompt. Your SystemMessage then displays that summary to the 
# LLM so it knows who you are and what you've discussed, even though the history placeholder might be empty.

# Inject summary into prompt: This function adds summary dynamically.
def add_summary(inputs, config):
    # Extract session id
    # sid = "summary"
    sid = config["configurable"]["session_id"]

    # Transforms input:
        # {"input": "..."}
    # into:
        # {
        # "input": "...",
        # "summary": "compressed conversation memory"
        # }

    return {**inputs, "summary": summaries.get(sid, "")}




# Attach memory to chain. This wraps pipeline with memory.
# Pipeline becomes:

    # add_summary
    # ↓
    # prompt
    # ↓
    # LLM
    # ↓
    # save messages
# Parameters:
    # input_messages_key="input"
    # history_messages_key="history"
# tell LangChain where variables go inside prompt.

chat = RunnableWithMessageHistory(add_summary | prompt | llm, get_history, input_messages_key="input", history_messages_key="history")

# Session configuration
# Creates memory namespace:
    # session = "summary"
# Different users:
    # session_1
    # session_2
    # session_3
# each get separate memory.

config = {"configurable": {"session_id": "summary"}}

# Conversation execution loop
# Simulates multi-turn chat.
for q in ["My name is Sugat.", "I focus on FX vol.", "I want Agentic AI mastery.", "Use quant examples.", "I like LangGraph.", "What is my goal?"]:
    print(chat.invoke({"input": q}, config=config).content)

# 4. Trace of the Execution
# Let's look at what happens during your loop:

    # Queries 1–5: The AI answers using the messages stored in history. The summary is initially empty.
    # Query 6 ("What is my goal?"): * Before this runs, the history contains 5 messages. After this is sent, it hits 6.
        # The get_history function triggers summarize().
        # The messages ("My name is Sugat", "I focus on FX vol", etc.) are turned into: "The user is Sugat, a quant focused on FX vol seeking Agentic AI mastery."
        # The history is cleared.
        # The LLM answers "Your goal is Agentic AI mastery" by reading the Summary in the System Message, not the chat history.



# Why use this approach?
    # Infinite Context: You can talk to the AI for weeks. It will never "run out" of memory or exceed the token limit.

    # Context Distillation: It filters out the noise (like "Hello" or "How are you?") and keeps only the "meat" (like "I trade FX vol").

    # Performance: The prompt stays relatively small, keeping the LLM responses fast and cost-effective.


# Summary of the Flow:
    # Check History Size: If >6, compress messages into a summary and clear history.
    # Inject Summary: Add the saved summary to the current prompt context.
    # Process Input: LLM sees: Summary + Recent Messages (if any) + New Question.
    # Repeat





# Why this architecture matters
# This is production-grade memory logic. Equivalent to:

    # ConversationSummaryMemory
    # +
    # ConversationBufferMemory

# combined into:
    # Hybrid memory system

# Used in:
    # research copilots
    # trading assistants
    # coding agents
    # long-running chat agents
    # LangGraph workflows


# Visual execution pipeline

# Each interaction runs:

    # load summary
    # +
    # load recent history
    # +
    # append new message
    # +
    # run LLM
    # +
    # store output
    # +
    # check if summarization needed
    # +
    # maybe compress history

# So memory stays:

    # compact
    # accurate
    # scalable
    # context-window safe


"""

>>> for q in ["My name is Sugat.", "I focus on FX vol.", "I want Agentic AI mastery.", "Use quant examples.", "I like LangGraph.", "What is my goal?"]:
...     print(chat.invoke({"input": q}, config=config).content)
... 
Nice to meet you, Sugat! How can I assist you today?
That's interesting! FX volatility can be a complex but crucial area in trading and risk management. Are you looking for specific information or insights related to FX volatility, 
or do you have any particular questions in mind?
Achieving mastery in Agentic AI involves understanding how to create and utilize AI systems that can act autonomously and make decisions based on their environment. 
Here are some steps you might consider:

1. **Foundational Knowledge**: Start with a solid understanding of AI and machine learning principles. Familiarize yourself with key concepts such as supervised and 
unsupervised learning, neural networks, and reinforcement learning.

2. **Programming Skills**: Gain proficiency in programming languages commonly used in AI, such as Python. Libraries like TensorFlow, PyTorch, and scikit-learn 
are essential for building AI models.

3. **Study Agent-Based Systems**: Learn about agent-based modeling and how agents can interact with their environment. This includes understanding concepts like autonomy, 
adaptability, and decision-making processes.

4. **Explore Reinforcement Learning**: Since agentic AI often involves learning from interactions with the environment, delve into reinforcement learning techniques, 
where agents learn to make decisions based on rewards and penalties.

5. **Ethics and Safety**: Understand the ethical implications and safety concerns surrounding autonomous AI systems. This includes studying bias, accountability, 
and the impact of AI on society.

6. **Hands-On Projects**: Engage in practical projects that involve building and deploying agentic AI systems. This could include simulations, games, or real-world applications.

7. **Stay Updated**: The field of AI is rapidly evolving. Follow research papers, attend conferences, and participate in online communities to stay informed about the latest advancements.

8. **Collaborate and Network**: Connect with other professionals in the field. Collaboration can lead to new insights and opportunities for learning.

If you have specific areas within Agentic AI that you're interested in or particular goals you want to achieve, feel free to share!
Certainly! Here are some quant examples related to FX volatility and Agentic AI that can help you in your journey toward mastery:

### FX Volatility Examples

1. **Volatility Modeling:**
   - **GARCH Model:** Use a Generalized Autoregressive Conditional Heteroskedasticity (GARCH) model to forecast FX volatility. For instance, you can model the daily 
   returns of a currency pair (e.g., EUR/USD) and estimate the conditional volatility to understand how it changes over time.
   - **Example Code (Python):**
     ```python
     import numpy as np
     import pandas as pd
     from arch import arch_model

     # Load FX data
     data = pd.read_csv('EURUSD.csv')
     returns = data['Close'].pct_change().dropna()

     # Fit GARCH model
     model = arch_model(returns, vol='Garch', p=1, q=1)
     model_fit = model.fit()
     print(model_fit.summary())
     ```

2. **Volatility Surface:**
   - **Implied Volatility Surface:** Analyze the implied volatility surface for FX options. This involves plotting the implied volatility against different strikes and maturities 
   to identify patterns and anomalies.
   - **Example Code (Python):**
     ```python
     import matplotlib.pyplot as plt
     from mpl_toolkits.mplot3d import Axes3D

     strikes = np.linspace(1.1, 1.5, 10)
     maturities = np.linspace(30, 365, 10)
     implied_vols = np.random.rand(len(strikes), len(maturities))  # Replace with actual data

     X, Y = np.meshgrid(strikes, maturities)
     fig = plt.figure()
     ax = fig.add_subplot(111, projection='3d')
     ax.plot_surface(X, Y, implied_vols, cmap='viridis')
     ax.set_xlabel('Strike')
     ax.set_ylabel('Maturity (days)')
     ax.set_zlabel('Implied Volatility')
     plt.show()
     ```

3. **Risk Management:**
   - **Value at Risk (VaR):** Calculate the VaR for a FX portfolio using historical simulation or Monte Carlo methods to assess potential losses due to FX volatility.
   - **Example Code (Python):**
     ```python
     portfolio_returns = np.random.normal(0, 0.02, 1000)  # Simulated returns
     VaR_95 = np.percentile(portfolio_returns, 5)  # 5% VaR
     print(f"Value at Risk (95%): {VaR_95}")
     ```

### Agentic AI Examples

1. **Agent-Based Modeling:**
   - **Market Simulation:** Create an agent-based model to simulate trading behavior in the FX market. Each agent can have different strategies 
   (e.g., trend-following, mean-reversion) and interact with each other.
   - **Example Code (Python):**
     ```python
     import random

     class Trader:
         def __init__(self, strategy):
             self.strategy = strategy

         def trade(self, market_data):
             if self.strategy == 'trend':
                 return market_data[-1] > market_data[-2]  # Buy if trend is up
             else:
                 return market_data[-1] < market_data[-2]  # Sell if trend is down

     traders = [Trader(strategy=random.choice(['trend', 'mean-reversion'])) for _ in range(100)]
     ```

2. **Reinforcement Learning:**
   - **Trading Agent:** Develop a reinforcement learning agent that learns to trade FX pairs by maximizing cumulative rewards based on profit and loss from trades.
   - **Example Code (Python with TensorFlow):**
     ```python
     import tensorflow as tf

     # Define a simple neural network for the agent
     model = tf.keras.Sequential([
         tf.keras.layers.Dense(24, activation='relu', input_shape=(state_size,)),
         tf.keras.layers.Dense(24, activation='relu'),
         tf.keras.layers.Dense(action_size, activation='linear')
     ])
     model.compile(optimizer='adam', loss='mse')
     ```

3. **Ethics and Safety:**
   - **Bias Detection:** Implement techniques to detect and mitigate bias in your trading algorithms, ensuring that the AI system operates fairly and ethically.
   - **Example Approach:** Use fairness metrics to evaluate the performance of your trading strategies across different market conditions and ensure that no particular group is disadvantaged.

### Conclusion
These quant examples can help you apply your knowledge of FX volatility and Agentic AI in practical scenarios. Engaging in such projects will enhance your understanding 
and skills in both areas. If you have specific questions or need further examples, feel free to ask!
Great to hear that you like LangGraph! LangGraph is a powerful tool for building and analyzing language models, particularly in the context of natural language processing 
(NLP) and AI. Here are some ways you can leverage LangGraph in your journey toward mastering Agentic AI and applying it to FX volatility:

### Applications of LangGraph in Agentic AI

1. **Natural Language Processing for Market Sentiment Analysis:**
   - Use LangGraph to analyze news articles, social media posts, and financial reports related to FX markets. By extracting sentiment and key topics, you can gauge market sentiment
     and its potential impact on currency volatility.
   - **Example Approach:**
     - Build a sentiment analysis model using LangGraph to classify text data as positive, negative, or neutral regarding specific currency pairs.

2. **Agent Communication:**
   - In an agent-based model, you can use LangGraph to facilitate communication between agents. For instance, agents can share insights or market predictions in natural language, 
   allowing for more complex interactions and decision-making processes.
   - **Example Approach:**
     - Implement a dialogue system where agents can discuss their trading strategies and adjust their behavior based on the information shared.

3. **Reinforcement Learning with Natural Language Feedback:**
   - Combine reinforcement learning with LangGraph to create agents that learn from both numerical data (e.g., price movements) and natural language feedback (e.g., expert commentary). 
   This can enhance the agent's understanding of market dynamics.
   - **Example Approach:**
     - Train an agent to trade based on both historical price data and textual feedback from analysts, allowing it to adapt its strategy based on qualitative insights.

4. **Data Visualization:**
   - Use LangGraph to generate visualizations of language data, such as word clouds or topic distributions, to better understand the context of market movements and volatility.
   - **Example Approach:**
     - Create visual representations of the most frequently discussed topics in FX news and correlate them with volatility spikes in currency pairs.

5. **Ethics and Bias in Language Models:**
   - Investigate the ethical implications of using language models in trading. LangGraph can help you analyze biases in the data and ensure that your models are fair and transparent.
   - **Example Approach:**
     - Conduct a bias audit on the training data used for sentiment analysis to ensure that it does not disproportionately favor certain currencies or market perspectives.

### Getting Started with LangGraph

- **Documentation and Tutorials:** Explore the official LangGraph documentation and tutorials to familiarize yourself with its features and capabilities.
- **Hands-On Projects:** Start with small projects, such as building a sentiment analysis model for FX news, and gradually increase the complexity as you gain confidence.
- **Community Engagement:** Join online communities or forums related to LangGraph and AI to share your projects, seek feedback, and learn from others.

By integrating LangGraph into your studies and projects, you can enhance your understanding of both language processing and its applications in trading and risk management.
 If you have specific questions about using LangGraph or need further examples, feel free to ask!
Your goal is to achieve mastery in Agentic AI, with a specific focus on the following areas:

1. **Foundational Knowledge:** Understanding AI and machine learning principles.
2. **Programming Skills:** Proficiency in programming languages like Python and familiarity with libraries such as TensorFlow, PyTorch, and scikit-learn.
3. **Study Agent-Based Systems:** Learning about agent-based modeling and decision-making processes.
4. **Explore Reinforcement Learning:** Delving into techniques where agents learn from environmental interactions.
5. **Ethics and Safety:** Understanding ethical implications and safety concerns of autonomous AI systems.
6. **Hands-On Projects:** Engaging in practical projects involving agentic AI systems.
7. **Stay Updated:** Following research, attending conferences, and participating in online communities.
8. **Collaborate and Network:** Connecting with other professionals in the field for insights and learning opportunities.

Additionally, you have expressed an interest in FX volatility, which you may want to integrate into your studies and projects related to Agentic AI. 
If you have any specific aspects of your goal that you would like to focus on or explore further, feel free to let me know!

"""