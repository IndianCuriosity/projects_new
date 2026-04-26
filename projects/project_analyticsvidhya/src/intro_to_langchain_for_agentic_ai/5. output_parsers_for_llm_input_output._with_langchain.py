################################################################################################################################################################################
# # Output Parsers for LLM Input / Output with LangChain
#################################################################################################################################################################################


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
#  interacting with almost every LLM out there.
# 
# There are lots of LLM providers (OpenAI, Hugging Face, etc) - the LLM class is designed to provide a standard interface for all of them.


# ## Accessing Commercial LLMs like ChatGPT


from langchain_openai import ChatOpenAI

chatgpt = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)


# ## Output Parsers
# Output parsers are essential in Langchain for structuring the responses from language models. Below, we will discuss the role of output parsers and 
# include examples using Langchain's specific parser types: PydanticOutputParser, JsonOutputParser, and CommaSeparatedListOutputParser.
# 
# - **Pydantic parser:**
#   - This parser allows the specification of an arbitrary Pydantic Model to query LLMs for outputs matching that schema. Pydantic's BaseModel functions s
# imilarly to a Python dataclass but includes type checking and coercion.
# 
# - **JSON parser:**
#   - Users can specify an arbitrary JSON schema with this parser to ensure outputs from LLMs adhere to that schema. Pydantic can also be used to declare 
# your data model here.
# 
# - **CSV parser:**
#   - Useful for outputs requiring a list of items separated by commas. This parser facilitates the extraction of comma-separated values from model outputs.
# 


# ### PydanticOutputParser
# 
# This output parser allows users to specify an arbitrary Pydantic Model and query LLMs for outputs that conform to that schema.
# 
# Keep in mind that large language models are non-deterministic! You'll have to use an LLM with sufficient capacity to generate well-formed responses.
# 
# Use Pydantic to declare your data model. Pydantic's BaseModel is like a Python dataclass, but with actual type checking + coercion.


# Updated import paths for prompt templates - using simplified paths:
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

# Define your desired data structure - like a python data class.
class QueryResponse(BaseModel):
    description: str = Field(description="A brief description of the topic asked by the user")
    pros: str = Field(description="3 bullet points showing the pros of the topic asked by the user")
    cons: str = Field(description="3 bullet points showing the cons of the topic asked by the user")
    conclusion: str = Field(description="One line conclusion of the topic asked by the user")

# Set up a parser + inject instructions into the prompt template.
parser = PydanticOutputParser(pydantic_object=QueryResponse)
parser


# langchain pre-generated output response formatting instructions
print(parser.get_format_instructions())


# create the final prompt with formatting instructions from the parser
prompt_txt = """
             Answer the user query and generate the response based on the following formatting instructions

             Format Instructions:
             {format_instructions}

             Query:
             {query}
            """
prompt = PromptTemplate(
    template=prompt_txt,
    input_variables=["query"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

prompt


# create a simple LCEL chain to take the prompt, pass it to the LLM, enforce response format using the parser
chain = (prompt
           |
         chatgpt
           |
         parser)


question = "Tell me about Commercial Real Estate"
response = chain.invoke({"query": question})


response


response.description


response.dict()


for k,v in response.dict().items():
    print(f"{k}:\n{v}\n")


# ### JsonOutputParser
# 
# This output parser allows users to specify an arbitrary JSON schema and query LLMs for outputs that conform to that schema.
# 
# Keep in mind that large language models are non-deterministic! You'll have to use an LLM with sufficient capacity to generate well-formed responses.
# 
# It is recommended use Pydantic to declare your data model.


from typing import List
# Updated import paths for prompt templates - using simplified paths:
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, JsonOutputParser
from pydantic import BaseModel, Field
# Define your desired data structure - like a python data class.
class QueryResponse(BaseModel):
    description: str = Field(description="A brief description of the topic asked by the user")
    pros: str = Field(description="3 bullet points showing the pros of the topic asked by the user")
    cons: str = Field(description="3 bullet points showing the cons of the topic asked by the user")
    conclusion: str = Field(description="One line conclusion of the topic asked by the user")

# Set up a parser + inject instructions into the prompt template.
parser = JsonOutputParser(pydantic_object=QueryResponse)
parser


# create the final prompt with formatting instructions from the parser
prompt_txt = """
             Answer the user query and generate the response based on the following formatting instructions

             Format Instructions:
             {format_instructions}

             Query:
             {query}
            """
prompt = PromptTemplate(
    template=prompt_txt,
    input_variables=["query"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

prompt


# create a simple LCEL chain to take the prompt, pass it to the LLM, enforce response format using the parser
chain = (prompt
              |
            chatgpt
              |
            parser)
chain


topic_queries = [
    "Tell me about commercial real estate",
    "Tell me about Generative AI"
]

topic_queries_formatted = [{"query": topic} for topic in topic_queries]
topic_queries_formatted


responses = chain.map().invoke(topic_queries_formatted)


responses[0], type(responses[0])


import pandas as pd

df = pd.DataFrame(responses)
df


for response in responses:
  for k,v in response.items():
    print(f"{k}:\n{v}\n")
  print('-----')


# ### CommaSeparatedListOutputParser
# 
# This output parser can be used when you want to return a list of comma-separated items.

# %%
from langchain_core.output_parsers import CommaSeparatedListOutputParser
from langchain_core.prompts import PromptTemplate

output_parser = CommaSeparatedListOutputParser()

format_instructions = output_parser.get_format_instructions()
format_instructions


format_instructions = output_parser.get_format_instructions()

# And a query intented to prompt a language model to populate the data structure.
prompt_txt = """
             Create a list of 5 different ways in which Generative AI can be used

             Output format instructions:
             {format_instructions}
             """

prompt = PromptTemplate.from_template(template=prompt_txt)
prompt


# create a simple LLM Chain - more on this later
llm_chain = (prompt
              |
            chatgpt
              |
            output_parser)

# run the chain
response = llm_chain.invoke({'format_instructions': format_instructions})
response


type(response)

