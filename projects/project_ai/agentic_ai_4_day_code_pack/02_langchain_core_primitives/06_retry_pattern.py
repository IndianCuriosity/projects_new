####################################################################################################################
# This code demonstrates a simple LCEL (LangChain Expression Language) chain with an added Reliability Layer.While the logic of the chain 
# is straightforward (Prompt -> LLM), the most important part of this snippet is the .with_retry() method.

# 1. The Core Logic: The Pipe (|)

    # The line chain = prompt | llm creates a Runnable.
    # When you call .invoke(), the dictionary {"topic": "..."} is passed into the prompt.
    # The prompt formats the string and passes a ChatPromptValue to the llm.
    # The llm processes the request and returns an AIMessage.

# 2. The Reliability Layer: with_retry()
    # This is the "production-grade" part of your code. In a real-world agent pipeline, LLM calls can fail for several reasons:
    # API Rate Limits: You sent too many requests too fast (HTTP 429).
    # Server Overload: OpenAI's servers are busy (HTTP 500 or 503).
    # Network Blips: A temporary connection drop.
    # By adding .with_retry(stop_after_attempt=3), you are telling LangChain: "If the API call fails for a transient reason, don't crash the whole program. 
    # Wait a moment and try again, up to 3 times."

# 3. Why is this important for "Agent Pipelines"?
    # The prompt specifically asks about retries in agent pipelines. In a standard chatbot, a failure just means the user has to click "send" again. However, in an Agent:
    # The agent might be 5 steps deep into a complex reasoning loop.
    # If step 6 fails, you don't want the agent to "forget" everything it just did.
    # Automated retries ensure that the "chain of thought" remains unbroken by temporary technical hiccups.

####################################################################################################################

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_retry(stop_after_attempt=3)
prompt = ChatPromptTemplate.from_template("Explain {topic} briefly.")
chain = prompt | llm

print(chain.invoke({"topic": "retries in agent pipelines"}).content)

# 4. Advanced Retries (Pro Tip)
# If you want even more control, you can specify exactly which errors to retry on. For example, you might want to retry on a 
# RateLimitError but not on an InvalidRequestError (since a bad prompt will fail no matter how many times you retry it).
# One thing to watch out for: Retries add latency. If the API is genuinely down, your user might be staring at a loading spinner for a
#  long time while the code tries all 3 attempts.

# Example of more granular control (pseudo-code)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)..with_retry(retry_if_exception_type=(RateLimitError, APIConnectionError),stop_after_attempt=5)
prompt = ChatPromptTemplate.from_template("Explain {topic} briefly.")
chain = prompt | llm

print(chain.invoke({"topic": "retries in agent pipelines"}).content)







"""
>>> print(chain.invoke({"topic": "retries in agent pipelines"}).content)
Retries in agent pipelines refer to the mechanism that allows a pipeline to automatically attempt to rerun a failed step or job a specified number of times before
 ultimately failing the entire pipeline. This feature is useful for handling transient errors, such as network issues or temporary service outages, which
   may resolve themselves upon subsequent attempts.

When a step fails, the retry logic can be configured to:

1. **Specify the Number of Retries**: Define how many times the step should be retried before giving up.
2. **Set Delay Between Retries**: Introduce a wait time between retries to allow for recovery from transient issues.
3. **Log Attempts**: Keep track of each attempt, including successes and failures, for debugging and monitoring purposes.

By implementing retries, pipelines can improve resilience and reduce the likelihood of failure due to temporary issues, leading to more reliable 
automation and continuous integration/continuous deployment (CI/CD) processes.

"""