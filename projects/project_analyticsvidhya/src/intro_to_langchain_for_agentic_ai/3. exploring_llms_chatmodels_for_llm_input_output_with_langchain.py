

#################################################################################################################################################################################
# # Exploring LLMs and ChatModels for LLM Input / Output with LangChain
#################################################################################################################################################################################

from getpass import getpass

OPENAI_KEY = getpass('Enter Open AI API Key: ')


import os
os.environ['OPENAI_API_KEY'] = OPENAI_KEY


# #### Enter your HuggingFace token here
# You can get the key from [here](https://huggingface.co/settings/tokens) after creating an account or signing in. This is free.


# skip if only using chatgpt
from getpass import getpass
HUGGINGFACEHUB_API_TOKEN = getpass('Please enter your HuggingFace Token here: ')


# ## Setup necessary system environment variables
import os
os.environ['HUGGINGFACEHUB_API_TOKEN'] = HUGGINGFACEHUB_API_TOKEN


# # Model I/O
# 
# In LangChain, the central part of any application is the language model. This module provides crucial tools for working effectively with any language model, 
# ensuring it integrates smoothly and communicates well.
# 
# ### Key Components of Model I/O
# 
# **LLMs and Chat Models (used interchangeably):**
# - **LLMs:**
#   - **Definition:** Pure text completion models.
#   - **Input/Output:** Receives a text string and returns a text string.
# - **Chat Models:**
#   - **Definition:** Based on a language model but with different input and output types.
#   - **Input/Output:** Takes a list of chat messages as input and produces a chat message as output.
# 


# ## Chat Models and LLMs
# Large Language Models (LLMs) are a core component of LangChain. 
# LangChain does not implement or build its own LLMs. It provides a standard API for interacting with almost every LLM out there.
# There are lots of LLM providers (OpenAI, Hugging Face, etc) - the LLM class is designed to provide a standard interface for all of them.


# ## Accessing Commercial LLMs like ChatGPT
# ### Accessing ChatGPT as an LLM
# Here we will show how to access a basic ChatGPT Instruct LLM. However the ChatModel interface which we will see later, 
# is better because the LLM API doesn't support the chat models like `gpt-3.5-turbo`and only support the `instruct`models which can respond to 
# instructions but can't have a conversation with you.


from langchain_openai import OpenAI

chatgpt = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0)
prompt = """Explain what is Generative AI in 3 bullet points"""
print(prompt)

response = chatgpt.invoke(prompt)
print(response)


# ### Accessing ChatGPT as an Chat Model LLM
# Here we will show how to access the more advanced ChatGPT Turbo Chat-based LLM. The ChatModel interface is better because this supports
# the chat models like `gpt-3.5-turbo`which can respond to instructions as well as have a conversation with you. We will look at the conversation 
# aspect slightly later in the notebook.


from langchain_openai import ChatOpenAI
chatgpt = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
prompt = """Explain what is Generative AI in 3 bullet points"""
print(prompt)

response = chatgpt.invoke(prompt)
response

print(response.content)


# ## Accessing Open Source LLMs with HuggingFace and LangChain


# ### Accessing Open LLMs with HuggingFace Serverless API
# 
# The free [serverless API](https://huggingface.co/inference-api/serverless) lets you implement solutions and iterate in no time, but it may be rate limited for
#  heavy use cases, since the loads are shared with other requests.
# 
# For enterprise workloads, you can use Inference Endpoints - Dedicated which would be hosted on a specific cloud instance of your choice and would have a cost 
# associated with it. Here we will use the free serverless API which works quite well in most cases.
# 
# The advantage is you do not need to download the models or run them locally on a GPU compute infrastructure which takes time and also would cost you a fair amount.


# #### Accessing Microsoft Phi-3 Mini Instruct
# 
# The Phi-3-Mini-4K-Instruct is a 3.8B parameters, lightweight, state-of-the-art open model trained with the Phi-3 datasets that includes both synthetic data
# and the filtered publicly available websites data with a focus on high-quality and reasoning dense properties. Check more details 
# [here](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct)

from huggingface_hub import login


login()

from langchain_huggingface import HuggingFaceEndpoint

repo_id = "microsoft/Phi-3-mini-4k-instruct"                                                               #"microsoft/Phi-3.5-mini-instruct"

phi3_params = {
                  # "do_sample": False, # greedy decoding - temperature = 0
                  # "return_full_text": False, # don't return input prompt
                  "max_new_tokens": 1000, # max tokens answer can go upto
                }

llm = HuggingFaceEndpoint(
    repo_id=repo_id,
    # max_length=128,
    temperature=0.5,
    huggingfacehub_api_token=HUGGINGFACEHUB_API_TOKEN,
   **phi3_params
)



prompt

# Phi3 expects input prompt to be formatted in a specific way
# check more details here: https://huggingface.co/microsoft/Phi-3-mini-4k-instruct
phi3_prompt = """<|user|>Explain what is Generative AI in 3 bullet points<|end|>
<|assistant|>"""
print(phi3_prompt)

from huggingface_hub import model_info
info = model_info("microsoft/Phi-3-mini-4k-instruct")
print(info.pipeline_tag)

# response = llm.invoke(phi3_prompt)
# print(response)

# response = llm(phi3_prompt)
# print(response)

from langchain_huggingface import HuggingFaceEndpoint

llm = HuggingFaceEndpoint(
    repo_id="microsoft/Phi-3-mini-4k-instruct",
    huggingfacehub_api_token=HUGGINGFACEHUB_API_TOKEN,
    max_new_tokens=1000,
    temperature=0.5,
)

phi3_prompt = "<|user|>Explain what is Generative AI in 3 bullet points<|end|>\n<|assistant|>"

response = llm(phi3_prompt)
print(response)

response = llm.invoke({"question": "Explain what is Generative AI in 3 bullet points"})
print(response)


response = llm.invoke(phi3_prompt)
print(response)

# #### Accessing Google Gemma 2B Instruct
# 
# Gemma is a family of lightweight, state-of-the-art open models from Google, built from the same research and technology used to create the Gemini models. 
# They are text-to-text, decoder-only large language models, available in English, with open weights, pre-trained variants, and instruction-tuned variants.
#  Gemma models are well-suited for a variety of text generation tasks, including question answering, summarization, and reasoning. Their relatively small 
# size makes it possible to deploy them in environments with limited resources such as a laptop, desktop or your own cloud infrastructure. Check more details 
# [here](https://huggingface.co/google/gemma-1.1-2b-it)


gemma_repo_id = "google/gemma-2b-it"

gemma_params = {
                  "do_sample": False, # greedy decoding - temperature = 0
                  "return_full_text": False, # don't return input prompt
                  "max_new_tokens": 1000, # max tokens answer can go upto
                }

llm = HuggingFaceEndpoint(
    repo_id=gemma_repo_id,
    **gemma_params
)


prompt
response = llm.invoke(prompt)
print(response)


# ### Accessing Local LLMs with HuggingFacePipeline API
# 
# Hugging Face models can be run locally through the `HuggingFacePipeline` class. However remember you need a good GPU to get fast inference
# 
# The Hugging Face Model Hub hosts over 500k models, 90K+ open LLMs
# 
# These can be called from LangChain either through this local pipeline wrapper or by calling their hosted inference endpoints through the `HuggingFaceEndpoint` 
# API we saw earlier.
# 
# To use, you should have the `transformers` python package installed, as well as `pytorch`.
# 
# Advantages include the model being completely local, high privacy and security. Disadvantages are basically the necessity of a good compute infrastructure,
#  preferably with a GPU

# #### Accessing Google Gemma 2B and running it locally

from langchain_huggingface import HuggingFacePipeline

gemma_params = {
                  "do_sample": False, # greedy decoding - temperature = 0
                  "return_full_text": False, # don't return input prompt
                  "max_new_tokens": 1000, # max tokens answer can go upto
                }

local_llm = HuggingFacePipeline.from_model_id(
    model_id="google/gemma-1.1-2b-it",
    task="text-generation",
    pipeline_kwargs=gemma_params,
    # device=0 # when running on Colab selects the GPU, you can change this if you run it on your own instance if needed
)


local_llm

prompt

# Gemma2B when used locally expects input prompt to be formatted in a specific way
# check more details here: https://huggingface.co/google/gemma-1.1-2b-it#chat-template
gemma_prompt = """<bos><start_of_turn>user\n""" + prompt + """\n<end_of_turn>
<start_of_turn>model
"""
print(gemma_prompt)


response = local_llm.invoke(gemma_prompt)
print(response)

# ### Accessing Open LLMs in HuggingFace as a Chat Model LLM
# 
# Here we will show how to access open LLMs from HuggingFace like Google Gemma 2B and make them have a conversation with you. We will look at the conversation
#  aspect slightly later in the notebook.

from langchain_huggingface import ChatHuggingFace

chat_gemma = ChatHuggingFace(llm=llm,
                             model_id='google/gemma-1.1-2b-it')


print(response.content)


# ## Message Types for ChatModels and Conversational Prompting
# 
# Conversational prompting is basically you, the user, having a full conversation with the LLM. The conversation history is typically represented as a list of messages.
# 
# ChatModels process a list of messages, receiving them as input and responding with a message. Messages are characterized by a few distinct types and properties:
# 
# - **Role:** Indicates who is speaking in the message. LangChain offers different message classes for various roles.
# - **Content:** The substance of the message, which can vary:
#   - A string (commonly handled by most models)
#   - A list of dictionaries (for multi-modal inputs, where each dictionary details the type and location of the input)
# 
# Additionally, messages have an `additional_kwargs` property, used for passing extra information specific to the message provider, not typically general.
#  A well-known example is `function_call` from OpenAI.
# 
# ### Specific Message Types
# 
# - **HumanMessage:** A user-generated message, usually containing only content.
# - **AIMessage:** A message from the model, potentially including `additional_kwargs`, like `tool_calls` for invoking OpenAI tools.
# - **SystemMessage:** A message from the system instructing model behavior, typically containing only content. Not all models support this type.
# 


# ## Conversational Prompting with ChatGPT
# 
# Here we use the `ChatModel` API in `ChatOpenAI` to have a full conversation with ChatGPT while maintaining a full flow of the historical conversations


from langchain_openai import ChatOpenAI

#chatgpt = ChatOpenAI(model="gpt-4o-mini", temperature=0)
chatgpt = ChatOpenAI(model='gpt-5.5', temperature=0)
from langchain_core.messages import HumanMessage, SystemMessage

prompt = """Can you explain what is Generative AI in 3 bullet points?"""
sys_prompt = """Act as a helpful assistant and give meaningful examples in your responses."""
messages = [
    SystemMessage(content=sys_prompt),
    HumanMessage(content=prompt),
]

messages

response = chatgpt.invoke(messages)
response


print(response.content)

# add the past conversation history into messages
messages.append(response)
# add the new prompt to the conversation history list
prompt = """What did we discuss so far?"""
messages.append(HumanMessage(content=prompt))
messages


# sent the conversation history along with the new prompt to chatgpt
response = chatgpt.invoke(messages)
response.content


# ## Conversational Prompting with Open LLMs via HuggingFace
# 
# Here we use the `ChatModel` API in `ChatHuggingFace` to have a full conversation with any open LLMs while maintaining a full flow of the historical 
# conversations. Here we use the Google Gemma 2B LLM.

llm

# not needed if you are only running chatgpt
from langchain_huggingface import ChatHuggingFace

chat_gemma = ChatHuggingFace(llm=llm,
                             model_id='google/gemma-1.1-2b-it')


# this runs prompts using the open LLM - however gemma doesnt support a system prompt
prompt = """Explain Deep Learning in 3 bullet points"""

messages = [
    HumanMessage(content=prompt),
]

response = chat_gemma.invoke(messages) # doesn't support system prompts
messages.append(response)
print(response.content)


# this runs prompts using the open LLM - however gemma doesnt support a system prompt
prompt = """Explain Deep Learning in 3 bullet points"""

messages = [
    HumanMessage(content=prompt),
]

response = chat_gemma.invoke(messages) # doesn't support system prompts
messages.append(response)
print(response.content)


messages


# formatting prompt is automatically done inside the chatmodel
# formats in this syntax: https://huggingface.co/google/gemma-1.1-2b-it#chat-template
print(chat_gemma._to_chat_prompt([messages[0]]))


prompt = """Now do the same for Machine learning"""
messages.append(HumanMessage(content=prompt))

response = chat_gemma.invoke(messages) # doesn't support system prompts
print(response.content)


from huggingface_hub import InferenceClient


import huggingface_hub


huggingface_hub.__version__


client = InferenceClient(model='google/gemma-1.1-2b-it')


for message in client.chat_completion(messages=[{'role': 'user', 'content': 'waht is the capital of france?'}],
                                      max_tokens=200, stream=True):
    print(message.choices[0].delta.content)





