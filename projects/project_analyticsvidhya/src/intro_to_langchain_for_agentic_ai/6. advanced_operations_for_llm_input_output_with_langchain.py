
################################################################################################################################################################################
# # Advanced Operations for LLM Input / Output with LangChain
#################################################################################################################################################################################


# 
# This notebook covers the following operations:
# 
# - LLM Cost Monitoring
# - Caching
# - Streaming




# ## Enter API Tokens
# #### Enter your Open AI Key here
# 
# You can get the key from [here](https://platform.openai.com/api-keys) after creating an account or signing in


from getpass import getpass
OPENAI_KEY = getpass('Please enter your Open AI API Key here: ')


# ## Setup necessary system environment variables
import os
os.environ['OPENAI_API_KEY'] = OPENAI_KEY


# ## Chat Models and LLMs
# 
# Large Language Models (LLMs) are a core component of LangChain. LangChain does not implement or build its own LLMs. It provides a standard API for 
# interacting with almost every LLM out there.
# 
# There are lots of LLM providers (OpenAI, Hugging Face, etc) - the LLM class is designed to provide a standard interface for all of them.


# ## Accessing Commercial LLMs like ChatGPT


from langchain_openai import ChatOpenAI
# Updated parameter name from model_name to model:
chatgpt = ChatOpenAI(model="gpt-4o-mini", temperature=0)


# ## Tracking LLM Costs
# 
# Typically LLMs like ChatGPT charge you based on the number of tokens per request and response. You can track your token usage for specific calls. 
# It is currently only implemented for the OpenAI API.


# Updated import path for callbacks:
#from langchain_core.callbacks import get_openai_callback
from langchain_community.callbacks.manager import get_openai_callback

prompt = """Explain Generative AI in one line"""

with get_openai_callback() as cb:
    response = chatgpt.invoke(prompt)
    print(response.content)
    print(cb)


cb.total_tokens


cb.prompt_tokens, cb.completion_tokens


cb.total_cost


# ## Caching in LangChain
# 
# LangChain includes an optional caching layer for language model APIs (LLMs). This caching feature is beneficial for two main reasons:
# 
# 1. **Cost Efficiency:** By caching responses, you reduce the number of API calls made to LLM providers, especially helpful if you are frequently requesting 
# the same completions. This can significantly lower costs.
# 
# 2. **Performance Improvement:** Caching can enhance your application's speed by decreasing the need for repeated API calls to the LLM provider, 
# making interactions quicker and more efficient.
# 


# #### InMemoryCache



# integrations with other caching tools:
# https://api.python.langchain.com/en/latest/community_api_reference.html#module-langchain_community.cache
#from langchain.cache import InMemoryCache
from langchain_community.cache import InMemoryCache
from langchain_core.globals import set_llm_cache

set_llm_cache(InMemoryCache())

# The first time, it is not yet in cache, so it should take longer

from langchain_core.prompts import ChatPromptTemplate

prompt = """Explain to me what is mortgage"""

chat_template = ChatPromptTemplate.from_template(prompt)

chatgpt.invoke(chat_template.format())


%%time
# The second time it is, so it goes faster
chatgpt.invoke(chat_template.format())


# #### SQLite Cache


# just to remove cache if it already exists, ignore if you get an error message below, that is normal (when cache doesnt exist)
!rm langchain.db


# We can do the same thing with a SQLite cache
from langchain_community.cache import SQLiteCache

set_llm_cache(SQLiteCache(database_path="db_others/langchain.db"))


%%time

# The first time, it is not yet in cache, so it should take longer
prompt = """Explain to me what is fractional real estate"""

chat_template = ChatPromptTemplate.from_template(prompt)

chatgpt.invoke(chat_template.format())


%%time
# The second time it is, so it goes faster
chatgpt.invoke(chat_template.format())


# ## Streaming in LLMs
# 
# All language model interfaces (LLMs) in LangChain implement the `Runnable` interface, which provides default methods such as `ainvoke`, `batch`, 
# `abatch`, `stream`, and `astream`. This setup equips all LLMs with basic streaming capabilities.
# 
# ### Streaming Defaults:
# 
# - **Synchronous Streaming:** By default, streaming operations return an `Iterator` that yields a single value, the final result from the LLM provider.
# - **Asynchronous Streaming:** Similarly, async streaming defaults to returning an `AsyncIterator` with the final result.
# 
# ### Limitations:
# 
# - These default implementations do not support token-by-token streaming. For such detailed streaming, the LLM provider must offer native support. 
# However, the default setup ensures that your code expecting an iterator of tokens will function correctly within these constraints.
# 


prompt = """Explain to me what is mortgage in detail with pros and cons"""
chat_template = ChatPromptTemplate.from_template(prompt)

for chunk in chatgpt.stream(chat_template.format()):
    print(chunk.content)


prompt = """Explain to me what is mortgage in detail with pros and cons"""
chat_template = ChatPromptTemplate.from_template(prompt)

response = []
for chunk in chatgpt.stream(chat_template.format()):
    print(chunk.content, end="")
    response.append(chunk.content)


response[:10]


print(''.join(response))





