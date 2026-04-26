
################################################################################################################################################################################
# # Exploring Conversation Chains and Memory with LCEL
#################################################################################################################################################################################


from getpass import getpass

OPENAI_KEY = getpass('Enter Open AI API Key: ')


# ## Setup Environment Variables


import os

os.environ['OPENAI_API_KEY'] = OPENAI_KEY


# ## Load Connection to LLM
# 
# Here we create a connection to ChatGPT to use later in our chains


from langchain_openai import ChatOpenAI
# Updated parameter name from model_name to model:
chatgpt = ChatOpenAI(model='gpt-4o-mini', temperature=0)


# ## Working with LangChain Chains
# 
# Using an LLM in isolation is fine for simple applications, but more complex applications require chaining LLMs - either with each other or with other 
# components. Also running on multiple data points can be done easily with chains.
# 
# Chain's are the legacy interface for "chained" applications. We define a Chain very generically as a sequence of calls to components, which can include other chains.
# 
# Here we will be using LCEL chains exclusively


# ### The Problem with Simple LLM Chains
# 
# Simple LLM Chains cannot keep a track of past conversation history


# Updated import paths for prompt templates:
from langchain.prompts import ChatPromptTemplate

prompt_txt = """{query}"""
prompt = ChatPromptTemplate.from_template(prompt_txt)

# you can also write this as llm_chain = prompt | chatgpt
llm_chain = (
    prompt
      |
    chatgpt
)


response = llm_chain.invoke({'query': 'What are the first four colors of a rainbow?'})
print(response.content)


response = llm_chain.invoke({'query': 'and the other 3?'})
print(response.content)


# ### Conversation Chains with LCEL
# 
# LangChain Expression Language (LCEL) connects prompts, models, parsers and retrieval components using a `|` pipe operator.
# 
# A conversation chain basically consists of user prompts, historical conversation memory and the LLM. The LLM uses the history memory to give more 
# contextual answers to every new prompt or user query.
# 
# Memory is very important for having a true conversation with LLMs. LangChain allows us to manage conversation memory using various constructs. 
# The main ones we will cover include:
# 
# - ConversationBufferMemory
# - ConversationBufferWindowMemory
# - ConversationSummaryMemory
# - VectorStoreRetrieverMemory
# - ChatMessageHistory
# - SQLChatMessageHistory


# ### Conversation Chains with ConversationBufferMemory
# 
# This is the simplest version of in-memory storage of historical conversation messages. It is basically a buffer for storing conversation memory.
# 
# Remember if you have a really long conversation, you might exceed the max token limit of the context window allowed for the LLM.


# Updated import paths for prompt templates - using simplified paths:
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.schema.runnable import RunnablePassthrough, RunnableLambda

SYS_PROMPT = """Act as a helpful assistant and give brief answers"""
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYS_PROMPT),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{query}"),
    ]
)

memory = ConversationBufferMemory(return_messages=True)


# function to get historical conversation messages from the memory
memory.load_memory_variables({})


# lets create a function now which returns the list of messages from memory
def get_memory_messages(query):
    return memory.load_memory_variables(query)['history']

get_memory_messages('What are the first four colors of a rainbow?')


# testing out the function with a runnable lambda which will go into our chain
# this returns the history but we also need to send our current query to the prompt
RunnableLambda(get_memory_messages).invoke({'query': 'What are the first four colors of a rainbow?'})


# we use a runnable passthrough to pass our current query untouched
# along with the history messages to the next step in the chain
RunnablePassthrough.assign(
        history=RunnableLambda(get_memory_messages)
    ).invoke({'query': 'What are the first four colors of a rainbow?'})


# creating our conversation chain now
def get_memory_messages(query):
    return memory.load_memory_variables(query)['history']

conversation_chain = (
    RunnablePassthrough.assign(
        history=RunnableLambda(get_memory_messages)
    ) # sends current query (input by user at runtime) and history messages to next step
      |
    prompt # creates prompt using the previous two variables
      |
    chatgpt # generates response using the prompt from previous step
)


query = {'query': 'What are the first four colors of a rainbow?'}
response = conversation_chain.invoke(query)
response


print(response.content)


memory.load_memory_variables({})


memory.save_context(query, {"output": response.content})


memory.load_memory_variables({})


query = {'query': 'and the other 3?'}
response = conversation_chain.invoke(query)
memory.save_context(query, {"output": response.content}) # remember to save your current conversation in memory
print(response.content)


memory.load_memory_variables({})


query = {'query': 'Explain AI in 2 bullet points'}
response = conversation_chain.invoke(query)
memory.save_context(query, {"output": response.content}) # remember to save your current conversation in memory
print(response.content)


query = {'query': 'Now do the same for Deep Learning'}
response = conversation_chain.invoke(query)
memory.save_context(query, {"output": response.content}) # remember to save your current conversation in memory
print(response.content)


query = {'query': 'What have we discussed so far?'}
response = conversation_chain.invoke(query)
memory.save_context(query, {"output": response.content}) # remember to save your current conversation in memory
print(response.content)


memory.load_memory_variables({})


# ### Conversation Chains with ConversationBufferWindowMemory
# 
# If you have a really long conversation, you might exceed the max token limit of the context window allowed for the LLM when using `ConversationBufferMemory` 
# so `ConversationBufferWindowMemory` helps in just storing the last K conversations (one conversation piece is one user message and the corresponding AI 
# message from the LLM) and thus helps you manage token limits and costs


from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema.runnable import RunnablePassthrough, RunnableLambda

SYS_PROMPT = """Act as a helpful assistant and give brief answers"""
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYS_PROMPT),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{query}"),
    ]
)

# stores last 2 sets of human-AI conversations
memory = ConversationBufferWindowMemory(return_messages=True, k=2)

# creating our conversation chain now
def get_memory_messages(query):
    return memory.load_memory_variables(query)['history']

conversation_chain = (
    RunnablePassthrough.assign(
        history=RunnableLambda(get_memory_messages)
    ) # sends current query (input by user at runtime) and history messages to next step
      |
    prompt # creates prompt using the previous two variables
      |
    chatgpt # generates response using the prompt from previous step
)


query = {'query': 'What are the first four colors of a rainbow?'}
response = conversation_chain.invoke(query)
memory.save_context(query, {"output": response.content}) # remember to save your current conversation in memory
print(response.content)


query = {'query': 'and the other 3?'}
response = conversation_chain.invoke(query)
memory.save_context(query, {"output": response.content}) # remember to save your current conversation in memory
print(response.content)


query = {'query': 'Explain AI in 2 bullet points'}
response = conversation_chain.invoke(query)
memory.save_context(query, {"output": response.content}) # remember to save your current conversation in memory
print(response.content)


query = {'query': 'Now do the same for Deep Learning'}
response = conversation_chain.invoke(query)
memory.save_context(query, {"output": response.content}) # remember to save your current conversation in memory
print(response.content)


memory.load_memory_variables({})


query = {'query': 'What have we discussed so far?'}
response = conversation_chain.invoke(query)
memory.save_context(query, {"output": response.content}) # remember to save your current conversation in memory
print(response.content)


memory.load_memory_variables({})


# ### Conversation Chains with ConversationSummaryMemory
# 
# If you have a really long conversation or a lot of messages, you might exceed the max token limit of the context window allowed for the LLM when using 
# `ConversationBufferMemory`
# 
# `ConversationSummaryMemory` creates a summary of the conversation history over time. This can be useful for condensing information from the 
# conversation messages over time.
# 
# This memory is most useful for longer conversations, where keeping the past message history in the prompt verbatim would take up too many tokens.


from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationSummaryMemory
from langchain.schema.runnable import RunnablePassthrough, RunnableLambda

SYS_PROMPT = """Act as a helpful assistant and give brief answers"""
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYS_PROMPT),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{query}"),
    ]
)

memory = ConversationSummaryMemory(return_messages=True, llm=chatgpt)
# creating our conversation chain now
def get_memory_messages(query):
    return memory.load_memory_variables(query)['history']

conversation_chain = (
    RunnablePassthrough.assign(
        history=RunnableLambda(get_memory_messages)
    ) # sends current query (input by user at runtime) and history messages as a summary to next step
      |
    prompt # creates prompt using the previous two variables
      |
    chatgpt # generates response using the prompt from previous step
)


query = {'query': 'Explain AI in 2 bullet points'}
response = conversation_chain.invoke(query)
memory.save_context(query, {"output": response.content}) # remember to save your current conversation in memory
print(response.content)


query = {'query': 'Now do the same for Deep Learning'}
response = conversation_chain.invoke(query)
memory.save_context(query, {"output": response.content}) # remember to save your current conversation in memory
print(response.content)


memory.load_memory_variables({})


query = {'query': 'What have we discussed so far?'}
response = conversation_chain.invoke(query)
memory.save_context(query, {"output": response.content}) # remember to save your current conversation in memory
print(response.content)


# ### Conversation Chains with VectorStoreRetrieverMemory
# 
# `VectorStoreRetrieverMemory` stores historical conversation messages in a vector store and queries the top-K most "relevant" history messages every time it is called.
# 
# This differs from most of the other Memory classes in that it doesn't explicitly track the order of interactions but retrieves history based on embedding
#  similarity to the current question or prompt.
# 
# In this case, the "docs" are previous conversation snippets. This can be useful to refer to relevant pieces of information that the AI was told earlier in the conversation.


# #### Connect to  Open AI Embedding Models
# 
# LangChain enables us to access Open AI embedding models which include the newest models: a smaller and highly efficient `text-embedding-3-small` model, and a larger 
# and more powerful `text-embedding-3-large` model.


from langchain_openai import OpenAIEmbeddings

# details here: https://openai.com/blog/new-embedding-models-and-api-updates
openai_embed_model = OpenAIEmbeddings(model='text-embedding-3-small')


# #### Create a Vector Database to store conversation history
# 
# Here we use the Chroma vector DB and initialize an empty database collection to store conversation messages


from langchain_chroma import Chroma

# create empty vector DB
chroma_db = Chroma(collection_name='history_db',
                   embedding_function=openai_embed_model)


from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import VectorStoreRetrieverMemory
from langchain.schema.runnable import RunnablePassthrough, RunnableLambda

SYS_PROMPT = """Act as a helpful assistant and give brief answers"""
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYS_PROMPT),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{query}"),
    ]
)

# load 2 most similar conversation messages from vector db history for each new message \ prompt
# this uses cosine embedding similarity to load the top 2 similar messgages to the input prompt \ query
retriever = chroma_db.as_retriever(search_type="similarity",
                                   search_kwargs={"k": 2})
memory = VectorStoreRetrieverMemory(retriever=retriever, return_messages=True)

# creating our conversation chain now
def get_memory_messages(query):
    return [memory.load_memory_variables(query)['history']]

conversation_chain = (
    RunnablePassthrough.assign(
        history=RunnableLambda(get_memory_messages)
    ) # sends current query (input by user at runtime) and history messages to next step
      |
    prompt # creates prompt using the previous two variables
      |
    chatgpt # generates response using the prompt from previous step
)


query = {'query': 'Tell me about AI'}
response = conversation_chain.invoke(query)
memory.save_context(query, {"output": response.content}) # remember to save your current conversation in memory
print(response.content)


query = {'query': 'What about deep learning'}
response = conversation_chain.invoke(query)
memory.save_context(query, {"output": response.content}) # remember to save your current conversation in memory
print(response.content)


query = {'query': 'Tell me about the fastest animal in the world in 2 lines'}
response = conversation_chain.invoke(query)
memory.save_context(query, {"output": response.content}) # remember to save your current conversation in memory
print(response.content)


query = {'query': 'What about the cheetah?'}
response = conversation_chain.invoke(query)
memory.save_context(query, {"output": response.content}) # remember to save your current conversation in memory
print(response.content)


# Now for a new query around machine learning even if the most recent conversation messages have been about animals, it uses the vector databases to load
#  the last 2 historical conversations which are closest to the current question in terms of semantic similarity


print(memory.load_memory_variables({'query': 'What about machine learning?'})['history'])


query = {'query': 'What about machine learning?'}
response = conversation_chain.invoke(query)
memory.save_context(query, {"output": response.content}) # remember to save your current conversation in memory
print(response.content)


# ### Multi-user Conversation Chains with ChatMessageHistory
# 
# The concept of `ChatHistory` refers to a class in LangChain which can be used to wrap an arbitrary chain. This `ChatHistory` will keep track of inputs and 
# outputs of the underlying chain, and append them as messages to a message database. Future interactions will then load those messages and pass them into the 
# chain as part of the input.
# 
# The beauty of `ChatMessageHistory` is that we can store separate conversation histories per user or session which is often the need for real-world chatbots which 
# will be accessed by many users at the same time.
# 
# We use a `get_session_history` function which is expected to take in a `session_id` and return a Message History object. Everything is stored in memory. 
# This `session_id` is used to distinguish between separate conversations, and should be passed in as part of the config when calling the new chain


from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
# used to retrieve conversation history from memory
# based on a specific user or session ID
history_store = {}
def get_session_history(session_id):
    if session_id not in history_store:
        history_store[session_id] = ChatMessageHistory()
    return history_store[session_id]

# prompt to load in history and current input from the user
prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", "Act as a helpful AI Assistant"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{human_input}"),
    ]
)

# create a basic LLM Chain
llm_chain = (prompt_template
                |
             chatgpt)

# create a conversation chain which can load memory based on specific user or session id
conv_chain = RunnableWithMessageHistory(
    llm_chain,
    get_session_history,
    input_messages_key="human_input",
    history_messages_key="history",
)

# create a utility function to take in current user input prompt and their session ID
# streams result live back to the user from the LLM
def chat_with_llm(prompt: str, session_id: str):
    for chunk in conv_chain.stream({"human_input": prompt},
                                   {'configurable': { 'session_id': session_id}}):
        print(chunk.content, end="")


# Test conversation chain for user 1


user_id = 'bob123'
prompt = "Hi I am Bob, can you explain AI in 3 bullet points?"
chat_with_llm(prompt, user_id)


prompt = "Now do the same for deep learning"
chat_with_llm(prompt, user_id)


prompt = "Discuss briefly what have we discussed so far is bullet points?"
chat_with_llm(prompt, user_id)


# Now test conversation chain for user 2


user_id = 'james007'
prompt = "Hi can you explain what is an LLM in 2 bullet points?"
chat_with_llm(prompt, user_id)


prompt = "Actually I meant in the context of AI?"
chat_with_llm(prompt, user_id)


prompt = "Summarize briefly what we have discussed so far?"
chat_with_llm(prompt, user_id)


user_id = 'bob123'
prompt = "Discuss briefly what have we discussed so far is bullet points?"
chat_with_llm(prompt, user_id)


# ### Multi-user Window-based Conversation Chains with persistence - SQLChatMessageHistory
# 
# The beauty of `SQLChatMessageHistory` is that we can store separate conversation histories per user or session which is often the need for real-world chatbots 
# which will be accessed by many users at the same time. Instead of in-memory we can store it in a SQL database which can be used to store a lot of conversations.
# 
# We use a `get_session_history` function which is expected to take in a `session_id` and return a Message History object. Everything is stored in a SQL database. 
# his `session_id` is used to distinguish between separate conversations, and should be passed in as part of the config when calling the new chain
# 
# We also use a `memory_buffer_window` function to only use the top-K last historical conversations before sending it to the LLM, basically our own implementation 
# of `ConversationBufferWindowMemory`


# removes the memory database file - usually not needed
# you can run this only when you want to remove all conversation histories
!rm memory.db

# %%
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough

# used to retrieve conversation history from database
# based on a specific user or session ID
def get_session_history_db(session_id):
    return SQLChatMessageHistory(session_id, "sqlite:///memory.db")

# prompt to load in history and current input from the user
prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", "Act as a helpful AI Assistant"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{human_input}"),
    ]
)

# create a memory buffer window function to return the last K conversations
def memory_buffer_window(messages, k=2):
    return messages[-(k+1):]

# create a basic LLM Chain which only sends the last K conversations per user
llm_chain = (
    RunnablePassthrough.assign(history=lambda x: memory_buffer_window(x["history"]))
      |
    prompt_template
      |
    chatgpt
)


# create a conversation chain which can load memory based on specific user or session id
conv_chain = RunnableWithMessageHistory(
    llm_chain,
    get_session_history_db,
    input_messages_key="human_input",
    history_messages_key="history",
)

# create a utility function to take in current user input prompt and their session ID
# streams result live back to the user from the LLM
def chat_with_llm(prompt: str, session_id: str):
    for chunk in conv_chain.stream({"human_input": prompt},
                                   {'configurable': { 'session_id': session_id}}):
        print(chunk.content, end="")


# Test conversation chain for user 1


user_id = 'jim001'
prompt = "Hi can you tell me which is the fastest animal?"
chat_with_llm(prompt, user_id)


prompt = "what about the slowest animal?"
chat_with_llm(prompt, user_id)


prompt = "what about the largest animal?"
chat_with_llm(prompt, user_id)


prompt = "what topics have we discussed, show briefly as bullet points"
chat_with_llm(prompt, user_id)


# Now test conversation chain for user 2


user_id = 'john005'
prompt = "Explain AI in 3 bullets to a child"
chat_with_llm(prompt, user_id)


prompt = "Now do the same for Generative AI"
chat_with_llm(prompt, user_id)


prompt = "Now do the same for machine learning"
chat_with_llm(prompt, user_id)


prompt = "what topics have we discussed, show briefly as bullet points"
chat_with_llm(prompt, user_id)





