
#################################################################################################################################################################################
# # Prompting with Prompt Templates for LLM Input / Output with LangChain
#################################################################################################################################################################################




# ## Install OpenAI and LangChain dependencies
# ## Enter API Tokens
# #### Enter your Open AI Key here
# You can get the key from [here](https://platform.openai.com/api-keys) after creating an account or signing in

from getpass import getpass
OPENAI_KEY = getpass('Enter Open AI API Key: ')

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
#chatgpt = ChatOpenAI(model='gpt-5.5', temperature=0)

# ## Prompt Templates
# Prompt templates are pre-designed formats used to generate prompts for language models. These templates can include instructions, few-shot examples, and 
# specific contexts and questions suited for particular tasks.
# 
# LangChain provides tools for creating and using prompt templates. It aims to develop model-agnostic templates to facilitate the reuse of existing templates 
# across different language models. Typically, these models expect prompts in the form of either a string or a list of chat messages.
# 
# ### Types of Prompt Templates
# 
# - **PromptTemplate:**
#   - Used for creating string-based prompts.
#   - Utilizes Python's `str.format` syntax for templating, supporting any number of variables, including scenarios with no variables.
# 
# - **ChatPromptTemplate:**
#   - Designed for chat models, where the prompt consists of a list of chat messages.
#   - Each chat message includes content and a role parameter. For instance, in the OpenAI Chat Completions API, a chat message could be assigned to an 
# AI assistant, a human, or a system role.
# - **FewShotChatMessagePromptTemplate**
#   - A few-shot prompt template can be constructed from a set of examples
# 


# ### PromptTemplate
# 
# We can use `PromptTemplate` to create a template for a string prompt.
# 
# By default, `PromptTemplate` uses Python's `str.format` syntax for templating.
# 
# You can create custom prompt templates that format the prompt in any way you want. For more information, see [Prompt Template 
# Composition](https://python.langchain.com/v0.1/docs/modules/model_io/prompts/composition/).


from langchain_core.prompts import PromptTemplate

# Simple prompt

prompt = """Explain to me what is Generative AI in 3 bullet points?"""
prompt_template = PromptTemplate.from_template(prompt)
prompt_template


prompt_template.format()


response = chatgpt.invoke(prompt_template.format())
print(response.content)


# more complex prompt with placeholders
prompt = """Explain to me briefly about {topic} in {language}."""

prompt_template = PromptTemplate.from_template(prompt)
prompt_template


inputs = [("Generative AI", "english"),
          ("Artificial Intelligence", "hindi"),
          ("Deep Learning", "german")]

prompts = [prompt_template.format(topic=topic, language=language) for topic, language in inputs]
prompts


# use map to run on multiple prompts in one go
responses = chatgpt.map().invoke(prompts)


responses


for response in responses:
  print(response.content)
  print('-----')


# ### ChatPromptTemplate
# 
# The standard prompt format to [chat models](https://python.langchain.com/v0.1/docs/modules/model_io/chat/) is a list of 
# [chat messages](https://python.langchain.com/v0.1/docs/modules/model_io/chat/message_types/).
# 
# Each chat message is associated with content, and an additional parameter called `role`. For example, in the OpenAI Chat Completions API, 
# a chat message can be associated with an AI assistant, a human or a system role.


# Updated import paths for prompt templates - using simplified paths:
from langchain_core.prompts import ChatPromptTemplate

# simple prompt with placeholders
prompt = """Explain to me briefly about {topic}."""

chat_template = ChatPromptTemplate.from_template(prompt)
chat_template


topics = ['mortgage', 'fractional real estate', 'commercial real estate']
prompts = [chat_template.format(topic=topic) for topic in topics]
prompts


responses = chatgpt.map().invoke(prompts)
for response in responses:
  print(response.content)
  print('-----')


responses[0]


# more complex prompt with a series of messages
messages = [
        ("system", "Act as an expert in real estate and provide brief answers"),
        ("human", "what is your name?"),
        ("ai", "my name is AIBot"),
        ("human", "{user_prompt}"),
]
chat_template = ChatPromptTemplate.from_messages(messages)
chat_template


text_prompts = ["what is your name?",
                "explain commercial real estate to me"]
chat_prompts = [chat_template.format(user_prompt=prompt) for prompt in text_prompts]
chat_prompts


print(chat_prompts[0])


print(chat_prompts[1])


responses = chatgpt.map().invoke(chat_prompts)
for response in responses:
  print(response.content)
  print('-----')


messages = [
        ("system", "Act as an expert in real estate and provide very detailed answers with examples"),
        ("human", "what is your name?"),
        ("ai", "my name is AIBot"),
        ("human", "{user_prompt}"),
]
chat_template = ChatPromptTemplate.from_messages(messages)
text_prompts = ["what is your name?", "explain commercial real estate to me"]
chat_prompts = [chat_template.format(user_prompt=prompt) for prompt in text_prompts]
chat_prompts


responses = chatgpt.map().invoke(chat_prompts)
for response in responses:
  print(response.content)
  print('-----')


# #### PromptTemplate and ChatPromptTemplate supports LCEL
# 
# `PromptTemplate` and `ChatPromptTemplate` implement the [Runnable interface](https://python.langchain.com/v0.1/docs/expression_language/interface/),
#  the basic building block of the LangChain Expression Language (LCEL). This means they support `invoke`, `ainvoke`, `stream`, `astream`, `batch`, `abatch`, `astream_log` calls.
# 
# `PromptTemplate` accepts a dictionary (of the prompt variables) and returns a `StringPromptValue`. A `ChatPromptTemplate` accepts a dictionary and returns 
# a `ChatPromptValue`.


text_prompts = ["what is your name?", "explain commercial real estate to me"]
chat_prompts = [chat_template.invoke({'user_prompt' : prompt}) for prompt in text_prompts]
chat_prompts


chat_prompts[1]


print(chat_prompts[1].to_string())


chat_prompts[1].to_messages()


responses = chatgpt.map().invoke(chat_prompts)
for response in responses:
  print(response.content)
  print('-----')




