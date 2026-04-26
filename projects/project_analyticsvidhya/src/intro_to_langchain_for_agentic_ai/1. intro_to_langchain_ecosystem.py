

#################################################################################################################################################################################
##### Intro to LangChain Eco System
#################################################################################################################################################################################

###########################################################################################
# ## Load OpenAI API Credentials : Run this section only if you are using Open AI
###########################################################################################

from getpass import getpass
openai_key = getpass("Enter your OpenAI API Key: ")

# ## Configure Open AI Key in Environment

import os
os.environ['OPENAI_API_KEY'] = openai_key
#print (openai_key)

# ## Use OpenAI ChatGPT with LangChain
# Import path standardization - use updated import paths for cleaner code

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
# Parameter name change: 'model_name' is now 'model' in ChatOpenAI class
#chatgpt = ChatOpenAI(model='gpt-4o-mini', temperature=0)
chatgpt = ChatOpenAI(model='gpt-5.5', temperature=0)

PROMPT = "Explain {topic} in 2 bullets"
prompt = ChatPromptTemplate.from_template(PROMPT)

chain = (
         prompt
           |
         chatgpt
)

response = chain.invoke({"topic": "AI"})
print(response.content)


###########################################################################################
# ## Load Gemini API credentials : Run this section only if you are using Google Gemini
###########################################################################################

from getpass import getpass
gemini_key = getpass("Enter your Gemini API Key: ")

# ## Configure Gemini Key in Environment

import os
os.environ["GOOGLE_API_KEY"] = gemini_key


# ## Use Gemini for Prompting: Import path standardization - use updated import paths for cleaner code
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
# Parameter name change: 'model_name' is now 'model' in ChatOpenAI class
gemini = ChatGoogleGenerativeAI(model="gemini-3.1-pro-preview")
#gemini = ChatGoogleGenerativeAI(model="gemini-3-pro")
#gemini = ChatGoogleGenerativeAI(model="gemini-1.5-flash")


PROMPT = "Explain {topic} in 2 bullets"
prompt = ChatPromptTemplate.from_template(PROMPT)

chain = (
         prompt
           |
         gemini
)

try:
  response = chain.invoke({"topic": "AI"})
  print(response.content)
except Exception as e:
  if "429" in str(e):
    print("Quota hit. Sleeping for 60 seconds...")
  else:
    raise e



