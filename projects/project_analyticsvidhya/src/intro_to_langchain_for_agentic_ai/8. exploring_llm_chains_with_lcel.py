

################################################################################################################################################################################
# # Exploring LLM Chains with LCEL
#################################################################################################################################################################################




# ## Enter Open AI API Key


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
# Using an LLM in isolation is fine for simple applications, but more complex applications require chaining LLMs - either with each other or with other components. 
# Also running on multiple data points can be done easily with chains.
# 
# Chain's are the legacy interface for "chained" applications. We define a Chain very generically as a sequence of calls to components, which can include other chains.
# 
# Here we will be using LCEL chains exclusively


# ### LLM Chain with LCEL
# 
# LangChain Expression Language (LCEL) connects prompts, models, parsers and retrieval components using a `|` pipe operator.
# 
# Any runnables can be "chained" together into sequences. The output of the previous runnable's `.invoke()` call is passed as input to the next runnable. 
# This can be done using the pipe operator `(|)`, or the more explicit `.pipe()` method, which does the same thing.
# 
# The resulting `RunnableSequence` is itself a runnable, which means it can be invoked, streamed, or further chained just like any other runnable.


# Updated import paths for prompt templates:
from langchain.prompts import ChatPromptTemplate

prompt_txt = """Explain to me about {topic} in 3 bullet points"""
prompt = ChatPromptTemplate.from_template(prompt_txt)

# you can also write this as llm_chain = prompt | chatgpt

llm_chain = (
    prompt
      |
    chatgpt
)


from IPython.display import Image, display

display(Image(llm_chain.get_graph().draw_mermaid_png()))


print(llm_chain.get_graph().draw_ascii())


response = llm_chain.invoke({'topic': 'Generative AI'})
response


print(response.content)


# Adding an output parser now to just get the response as a string


# Updated import path for output parsers:
from langchain_core.output_parsers import StrOutputParser

# chain with an output parser
llm_chain = (
    prompt
      |
    chatgpt
      |
    StrOutputParser()
)


display(Image(llm_chain.get_graph().draw_mermaid_png()))


response = llm_chain.invoke({'topic': 'Generative AI'})
print(response)


reviews = [
    f"""
    Purchased this adorable koala plush toy for my nephew's birthday,
    and he's absolutely smitten with it, carrying it around everywhere he goes.
    The plush is incredibly soft, and the koala's face has an endearing expression.
    However, I did find it a tad on the smaller side given its price point.
    I believe there may be larger alternatives available at a similar price.
    To my delight, it arrived a day earlier than anticipated,
    allowing me to enjoy it briefly before gifting it to him.
    """,
    f"""
    Required a stylish lamp for my office space, and this particular one
    came with added storage at a reasonable price.
    The delivery was surprisingly quick, arriving within just two days.
    However, the pull string for the lamp suffered damage during transit.
    To my relief, the company promptly dispatched a replacement,
    which arrived within a few days. Assembly was a breeze.
    Then, I encountered an issue with a missing component,
    but their support team responded swiftly and provided the missing part.
    It appears to be a commendable company that genuinely values its
    customers and the quality of its products.
    """
    ]


from langchain.prompts import ChatPromptTemplate

prompt = """
            Act as a product review analyst.
            Your task is to generate a short summary of a product
            review from an ecommerce site.

            Generate a summary of the review (max 2 lines)
            Also show both the positives and negatives from the review (max 2 bullets)

            ```{review}```
"""

prompt_template = ChatPromptTemplate.from_template(prompt)
llm_chain = (
    prompt_template
      |
    chatgpt
      |
    StrOutputParser()
)


result = llm_chain.invoke({'review': reviews[0]})


result


print(result)


formatted_reviews = [{'review': review}
                        for review in reviews]

results = llm_chain.map().invoke(formatted_reviews)
len(results)


for result in results:
    print(result)
    print()




