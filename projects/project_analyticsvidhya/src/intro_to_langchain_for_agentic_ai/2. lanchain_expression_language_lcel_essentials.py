

#################################################################################################################################################################################
##### LangChain Expression Language (LCEL) Essentials
#################################################################################################################################################################################


# # Simple LangChain LCEL Chain Example
# This notebook shows how to create a simple LLM Chain using LangChain's new LangChain Expression Language (LCEL) syntax
# ## Setup Open AI API credentials


from getpass import getpass
OPENAI_KEY = getpass('Enter Open AI API Key: ')

import os
os.environ['OPENAI_API_KEY'] = OPENAI_KEY

# ## Connect to the LLM
from langchain_openai import ChatOpenAI
# Parameter name change: 'model_name' is now 'model' in ChatOpenAI class
chatgpt = ChatOpenAI(model="gpt-4o-mini", temperature=0)
#chatgpt = ChatOpenAI(model='gpt-5.5', temperature=0)


# ## Create LCEL LLM Chain
# Updated import paths for prompt templates - using simplified paths:
from langchain_core.prompts import ChatPromptTemplate

# create a prompt template to accept user queries
prompt_txt = "{query}"
prompt_template = ChatPromptTemplate.from_template(prompt_txt)

# the chain has been formatted for better readability
# you could also write this as llmchain = prompt_template | chatgpt
llmchain = (prompt_template
              |
           chatgpt)

# ## Run the LLM Chain
response = llmchain.invoke({'query' : 'Explain Generative AI in 1 line'})
print(response.content)


#################





