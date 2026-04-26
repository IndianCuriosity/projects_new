
################################################################################################################################################################################
# # Project: Prompt Engineering with LangChain and ChatGPT for real-world tasks
#################################################################################################################################################################################



# 
# In this notebook you will leverage ChatGPT and LangChain to solve and do a few mini-projects based on some real-world scenarios:
# 
# - Mini-Project 1: Review Analyst
# - Mini-Project 2: Research Paper Analyst
# - Mini-Project 3: Social Media Marketing Analyst
# - Mini-Project 4: IT Support Analyst
# 
# ___[Created By: Dipanjan (DJ)](https://www.linkedin.com/in/dipanjans/)___




# ## Enter API Token
# #### Enter your Open AI Key here
# 
# You can get the key from [here](https://platform.openai.com/api-keys) after creating an account or signing in

from getpass import getpass
OPENAI_KEY = getpass('Please enter your Open AI API Key here: ')


# ## Setup necessary system environment variables

import os
os.environ['OPENAI_API_KEY'] = OPENAI_KEY


# ## Load Necessary Dependencies and ChatGPT LLM

# %%
# Updated import paths for prompt templates:
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


# Updated parameter name from model_name to model:
chatgpt = ChatOpenAI(model='gpt-4o-mini', temperature=0.0)



###########################################################################################
# ## Mini-Project 1: Review Analyst
###########################################################################################



# 
# You are building an AI system to be able to look at customer reviews and do some complex analysis. for each review get ChatGPT to do the following:
# 
#   - Summarize the review. The summary should be at most 3 lines.
#   - Highlight both the positives and negatives
#   - Display the overall sentiment of the review (positive, negative, neutral)
#   - Display a list of 3 - 5 emotions expressed by the customer in the review
#   - If the sentiment is positive or neutral write an email and thank them for the review
#   - If the sentiment is negative apologize and write an email with an appropriate response
# 
# Try to get the response in a nice structured format using an output parser


# ### Access Customer Reviews


reviews = [
    f"""
    Just received the Bluetooth speaker I ordered for beach outings, and it's fantastic.
    The sound quality is impressively clear with just the right amount of bass.
    It's also waterproof, which tested true during a recent splashing incident.
    Though it's compact, the volume can really fill the space.
    The price was a bargain for such high-quality sound.
    Shipping was also on point, arriving two days early in secure packaging.
    """,
    f"""
    Purchased a new gaming keyboard because of its rave reviews about responsiveness and backlighting.
    It hasn't disappointed. The keys have a satisfying click and the LED colors are vibrant,
    enhancing my gaming experience significantly. Price-wise, it's quite competitive,
    and I feel like I got a good deal. The delivery was swift, and it came well-protected,
    ensuring no damage during transport.
    """,
    f"""
    Ordered a set of wireless earbuds for running, and they've been a letdown.
    The sound constantly cuts out, and the fit is uncomfortable after only a few minutes of use.
    They advertised a 12-hour battery life, but I'm barely getting four hours.
    Considering the cost, I expected better quality and performance.
    They did arrive on time, but the positives end there. I'm already looking into a return.
    """,
    f"""
    The tablet stand I bought was touted as being sturdy and adjustable,
    but it's anything but. It wobbles with the slightest touch,
    and the angles are not holding up as promised. It feels like a breeze could knock it over.
    It was also pricier than others I've seen, which adds to the disappointment.
    It did arrive promptly, but what's the use if the product doesn't meet basic expectations?
    """,
    f"""
    Needed a new kitchen blender, but this model has been a nightmare.
    It's supposed to handle various foods, but it struggles with anything tougher than cooked vegetables.
    It's also incredibly noisy, and the 'easy-clean' feature is a joke; food gets stuck under the blades constantly.
    I thought the brand meant quality, but this product has proven me wrong.
    Plus, it arrived three days late. Definitely not worth the expense.
    """
]


# ### Define Output Parser


from langchain_core.prompts import PromptTemplate
# Updated import path for output parsers:
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

# Define your desired data structure - like a python data class.
class ReviewAnalysisResponse(BaseModel):
    summary: str = Field(description="A brief summary of the customer review with maximum 3 lines")
    positives: list = Field(description="A list showing the positives mentioned by the customer in the review if any - max 3 points")
    negatives: list = Field(description="A list showing the negatives mentioned by the customer in the review if any - max 3 points")
    sentiment: str = Field(description="One word showing the sentiment of the review - positive, negative or neutral")
    emotions: list = Field(description="A list of 3 - 5 emotions expressed by the customer in the review")
    email: str = Field(description="Detailed email to the customer based on the sentiment")

# Set up a parser + inject instructions into the prompt template.
parser = PydanticOutputParser(pydantic_object=ReviewAnalysisResponse)


# ### Create the input prompt for the LLM


# create the final prompt with formatting instructions from the parser
prompt_txt = """
             Analyze the given customer review below and generate the response based on the instructions
             mentioned below in the format instructions.
             Also remember to write a detailed email response for the email field based on these conditions:
               - email should be addressed to Dear Customer and signed with Service Agent
               - thank them if the review is positive or neutral
               - apologize if the review is negative

             Format Instructions:
             {format_instructions}

             Review:
             {review}
            """
prompt = PromptTemplate(
    template=prompt_txt,
    input_variables=["review"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)


# ### Create a LCEL LLM Chain


# create a simple LCEL chain to take the prompt, pass it to the LLM, enforce response format using the parser
chain = (prompt
           |
         chatgpt
           |
         parser)


# ### Format the input reviews


reviews_formatted = [{'review': review} for review in reviews]
reviews_formatted[0]


# ### Get responses from the LLM


responses = chain.map().invoke(reviews_formatted)


# ### View LLM responses


responses[0]


responses[0].dict()


for response in responses:
  for k,v in response.dict().items():
    print(f'{k}:\n{v}')
  print('-----')
  print('\n')


import pandas as pd

#pd.DataFrame(response.dict() for response in responses)
pd.DataFrame(response.model_dump() for response in responses)


###########################################################################################
# ## Mini-Project 2: Research Paper Analyst
###########################################################################################


# 
# Make ChatGPT act as an AI expert and transform the given research paper abstract based on the nature of the audience mentioned below.
# 
# - Short summary of maximum 10 lines for a general audience
# - Detailed report for a healthcare company. Have bullet points for pros and cons of ethics in Generative AI as mentioned in the paper
# - Detailed report for a generative AI company solving healthcare problems. Have bullet points for key points mentioned for Generative AI for text,
#  images and structured data based healthcare
# 
# Try to use `ChatPromptTemplate` so you can have a conversation with ChatGPT for each of the above tasks using conversational prompting


# ### Access the Research Paper Abstract


paper_abstract = f"""
The widespread use of ChatGPT and other emerging technology powered by generative
artificial intelligence (AI) has drawn much attention to potential ethical issues, especially in
high-stakes applications such as healthcare.1–3 However, less clear is how to resolve such
issues beyond following guidelines and regulations that are still under discussion and
development. On the other hand, other types of generative AI have been used to synthesize
images and other types of data for research and practical purposes, which have resolved some
ethical issues and exposed other ethical issues,4,5 but such technology is less often the focus
of ongoing ethical discussions. Here we highlight gaps in current ethical discussions of
generative AI via a systematic scoping review of relevant existing research in healthcare, and
reduce the gaps by proposing an ethics checklist for comprehensive assessment and
transparent documentation of ethical discussions in generative AI development. While the
checklist can be readily integrated into the current peer review and publication system to
enhance generative AI research, it may also be used in broader settings to disclose ethicsrelated considerations in generative AI-powered products 
(or real-life applications of such products) to help users establish reasonable trust in their capabilities.

Current ethical discussions on generative AI in healthcare
We conducted a systematic scoping review to analyse current ethical discussions on
generative AI in healthcare. Our search in four major academic research databases for
relevant publications from January 2013 to July 2023 yielded 2859 articles (see Methods for
detailed search strategy and Supplementary Figure S1 for the PRISMA flow diagram), of
which 193 articles were included for analysis based on application data modality (text, image,
or structured data), ethical issues discussed, generative AI involved, and whether generative
AI causes or offers technical solutions for issues raised.

Generative AI for text data-based healthcare
Forty-one of the 193 articles discussed ethical considerations pertaining to generative AI
applications for text data, with 20 articles describing methodological developments or
applications of generative AI and the other 21 articles describing review-type works on this
topic. Although some of these review-type articles used the general term “generative AI”, the
main body and supporting evidence focused on LLMs. Twenty-nine articles had in-depth
discussions on ethical issues, whereas the other 12 articles only briefly touched on some
ethical aspects.
Among the 41 articles, 29 articles focused on discussing ethical issues caused by LLMs (and
specifically by GPT in 16 of the articles), covering a wide range of application scenarios and
considered the application of all 10 ethical principles identified in the review (see Figure 1),
as well as other less discussed concerns such as human-AI interaction, and the rights of
LLMs to be considered as co-authors in scientific papers. One paper only commented briefly
on the need for ethical considerations in LLMs and is summarised in the “Others” category.
Although all ethical principles are equally important, some are discussed more often than
others, e.g., non-maleficence (also referred to in the literature as ‘benevolence’), equity, and
privacy.
Fifteen of the 41 articles aimed to resolve some existing ethical issues (for example,
confidentiality of medical data) by using LLMs and other generative AI (e.g., GAN,
autoencoder or diffusion), such as, to reduce privacy concerns by generating synthetic
medical text, to reduce disparity by providing accessible services and assistance, to detect
health-related misinformation, to generate trusted content, and to improve accountability or
transparency over existing approaches. While most articles focused on either identifying
ethical issues caused by generative AI or proposing generative AI-based solutions, three
articles discussed both to provide a more balanced perspective.

Generative AI for image and structured data-based healthcare
Unlike the diverse application scenarios of generative AI based on text data, for image and
structured data, this use of generative AI focuses on data synthesis and encryption. Hence the
majority of articles discussed the methodological developments of generative AI as giving
rise to a more distinctive and focused set of ethical issues.
5
Notably, of the 98 articles on image data and 58 articles on structured data, more than half
(n=63 for image data and n=33 for structured data) only mentioned ethical considerations as a
brief motivation for methodological developments or as a general discussion point. The rest
included more in-depth discussions or evaluations of ethical issues. Among these 155 articles
(as one article covered multiple modalities), 11 articles were review-type work, where 10
articles reviewed methods that mentioned one or two ethical perspectives, and only one
article24 discussed detailed ethical concerns on generative AI applications.
Resolving privacy issues was the main aim of articles for these two data modalities (n=74 for
image data and n=50 for structured data; see Figure 1), predominantly by generating synthetic
data using GAN. Eight articles on image data and 9 articles on structured data used
generative AI to reduce bias, e.g., by synthesizing data for under-represented subgroups in
existing databases. For both data modalities, we did not see explicit discussions on resolving
autonomy, integrity, or morality issues using generative AI, and for structured data the articles
additionally lacked discussions on trust or transparency.
Only 11 articles for image data selectively discussed some ethical issues that generative AI
can give rise to, without specific discussions regarding autonomy, integrity, or morality. For
structured data, only 4 articles discussed equity, privacy, or data security issues caused by
generative AI. Only two articles on structured data included both the cause and resolving
perspectives by discussing ethical issues that may arise from limitations of methods
proposed, specifically bias induced when synthesizing data in order to resolve privacy issues.
"""


# ### Create a prompt template for paper analysis and transformation


SYS_PROMPT = """
Act as a Artificial Intelligence Expert.
Transform the input research paper abstract given below
based on the instruction input by the user.
"""
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYS_PROMPT),
        ("human", "{instruction}"),
    ]
)


# ### Create a simple LCEL LLM Chain


chain = (prompt
            |
         chatgpt)


# ### Generate the first summary report


# Updated import path for message classes:
from langchain_core.messages import HumanMessage

prompt_txt = f"""
Based on the following research paper abstract,
create the summary report of maximum 10 lines
for a general audience

Abstract:
{paper_abstract}
"""
messages = [HumanMessage(content=prompt_txt)]
user_instruction = {'instruction': messages}

response = chain.invoke(user_instruction)
messages.append(response)


print(response.content)


response.content


messages


# ### Generate the second summary report
# 
# Here we add the previous LLM response and the new instructions to the list of messages and send the whole thing to the LLM so it has access to the 
# historical conversation


prompt_txt = f"""
Use only the research paper abstract from earlier and create a detailed report for a healthcare company.
In the report, also include bullet points (3 max) for pros and cons of ethics in Generative AI
"""
messages.append(HumanMessage(content=prompt_txt))
user_instruction = {'instruction': messages}
response = chain.invoke(user_instruction)
messages.append(response)


print(response.content)


messages


# ### Generate the third summary report
# 
# Here we add the previous LLM response and the new instructions to the list of messages and send the whole thing to the LLM so it has access 
# to the historical conversation


prompt_txt = f"""
Use only the research paper abstract from earlier and create a detailed report for a generative AI company solving healthcare problems.
In the report also include sections for key points mentioned around Generative AI for text, images and structured data based healthcare
"""
messages.append(HumanMessage(content=prompt_txt))
user_instruction = {'instruction': messages}
response = chain.invoke(user_instruction)


print(response.content)

###########################################################################################
# ## Mini-Project 3: Social Media Marketing Analyst
###########################################################################################


# 
# You have the technical fact sheets of one smartphone. Try some iterative prompt engineering and do the following:
# 
# 1. Generate marketing product description for the smartphone
# 
# 2. Custom product description which has the following:
# 
# ```
# The description should follow this format:
# 
# Product Name: <Name of the smartphone>
# ​
# Description: <Brief Overview of the features>
# ​
# Product Specifications:
# <Table with key product feature specifications>
# ​
# The description should focus on the most important features
# a customer might look for in a phone including the foldable display screen, processing power, RAM, camera and battery life.
# ​
# After the description, the table should have the
# key specifications of the product. It should have two columns.
# The first column should have 'Feature'
# and the second column should have 'Specification'
# and try to put exact numeric values for features if they exist.
# Only put these features in the table - foldable display screen, processing power, RAM, camera and battery life
# ```
# 
# 3. Custom product description focusing on specific aspects like display, camera and in less than 60 words


# ### Access the product factsheet data


fact_sheet_mobile = """
PRODUCT NAME
Samsung Galaxy Z Fold4 5G Black
​
PRODUCT OVERVIEW
Stands out. Stands up. Unfolds.
The Galaxy Z Fold4 does a lot in one hand with its 15.73 cm(6.2-inch) Cover Screen.
Unfolded, the 19.21 cm(7.6-inch) Main Screen lets you really get into the zone.
Pushed-back bezels and the Under Display Camera means there's more screen
and no black dot getting between you and the breathtaking Infinity Flex Display.
Do more than more with Multi View. Whether toggling between texts or catching up
on emails, take full advantage of the expansive Main Screen with Multi View.
PC-like power thanks to Qualcomm Snapdragon 8+ Gen 1 processor in your pocket,
transforms apps optimized with One UI to give you menus and more in a glance
New Taskbar for PC-like multitasking. Wipe out tasks in fewer taps. Add
apps to the Taskbar for quick navigation and bouncing between windows when
you're in the groove.4 And with App Pair, one tap launches up to three apps,
all sharing one super-productive screen
Our toughest Samsung Galaxy foldables ever. From the inside out,
Galaxy Z Fold4 is made with materials that are not only stunning,
but stand up to life's bumps and fumbles. The front and rear panels,
made with exclusive Corning Gorilla Glass Victus+, are ready to resist
sneaky scrapes and scratches. With our toughest aluminum frame made with
Armor Aluminum, this is one durable smartphone.
World’s first water resistant foldable smartphones. Be adventurous, rain
or shine. You don't have to sweat the forecast when you've got one of the
world's first water-resistant foldable smartphones.
​
PRODUCT SPECS
OS - Android 12.0
RAM - 12 GB
Product Dimensions - 15.5 x 13 x 0.6 cm; 263 Grams
Batteries - 2 Lithium Ion batteries required. (included)
Item model number - SM-F936BZKDINU_5
Wireless communication technologies - Cellular
Connectivity technologies - Bluetooth, Wi-Fi, USB, NFC
GPS - True
Special features - Fast Charging Support, Dual SIM, Wireless Charging, Built-In GPS, Water Resistant
Other display features - Wireless
Device interface - primary - Touchscreen
Resolution - 2176x1812
Other camera features - Rear, Front
Form factor - Foldable Screen
Colour - Phantom Black
Battery Power Rating - 4400
Whats in the box - SIM Tray Ejector, USB Cable
Manufacturer - Samsung India pvt Ltd
Country of Origin - China
Item Weight - 263 g
"""


# ### Create prompt template for the first advert


prompt_txt = """
Act as a marketing manager.
Your task is to help a marketing team create a
description for a retail website advert of a product based
on a technical fact sheet specifications for a mobile smartphone
​
Write a brief product description

Technical specifications:
{fact_sheet_mobile}
"""
chat_template = ChatPromptTemplate.from_template(prompt_txt)


# ### Use an LCEL LLM Chain to generate the first advert


chain = (chat_template
            |
         chatgpt)
response = chain.invoke({"fact_sheet_mobile": fact_sheet_mobile})


print(response.content)


from IPython.display import display, Markdown
display(Markdown(response.content))


# ### Create prompt template for the second advert


prompt_txt = """
Act as a marketing manager.
Your task is to help a marketing team create a
description for a retail website advert of a product based
on a technical fact sheet specifications for a mobile smartphone
​
The description should follow this format:

Product Name: <Name of the smartphone>
​
Description: <Brief Overview of the features>
​
Product Specifications:
<Table with key product feature specifications>
​
The description should focus on the most important features
a customer might look for in a phone including the foldable display screen, processing power, RAM, camera and battery life.
​
After the description, the table should have the
key specifications of the product. It should have two columns.
The first column should have 'Feature'
and the second column should have 'Specification'
and try to put exact numeric values for features if they exist.
Only put these features in the table - foldable display screen, processing power, RAM, camera and battery life

Technical specifications:
{fact_sheet_mobile}
"""
chat_template = ChatPromptTemplate.from_template(prompt_txt)


# ### Use an LCEL LLM Chain to generate the second advert


chain = (chat_template
            |
         chatgpt)
response = chain.invoke({"fact_sheet_mobile": fact_sheet_mobile})


print(response.content)


from IPython.display import display, Markdown
display(Markdown(response.content))


# ### Create prompt template for the third advert


prompt_txt = """
Act as a marketing manager.
Your task is to help a marketing team create a
description for a retail website advert of a product based
on a technical fact sheet specifications for a mobile smartphone
​
Write a catchy product description with some emojis,
which uses at most 60 words
and focuses on the most important things about the smartphone
which might matter to users like display and camera

Technical specifications:
{fact_sheet_mobile}
"""
chat_template = ChatPromptTemplate.from_template(prompt_txt)


# ### Use an LCEL LLM Chain to generate the third advert


chain = (chat_template
            |
         chatgpt)
response = chain.invoke({"fact_sheet_mobile": fact_sheet_mobile})


print(response.content)


from IPython.display import display, Markdown
display(Markdown(response.content))


###########################################################################################
# ## Mini-Project 4 - IT Support Analyst
###########################################################################################



# 
# Ask ChatGPT to act as a IT support agent, process each customer IT ticket message and output the response in JSON with the following fields
# 
# ```
# orig_msg: The original customer message
# orig_lang: Detected language of the customer message e.g. Spanish
# category: 1-2 word describing the category of the problem
# trans_msg: Translated customer message in English
# response: Response to the customer in orig_lang
# trans_response: Response to the customer in English
# ```
# 
# Try to use a JSON parser to get the responses in JSON for each ticket


# ### Define Output Parser


from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser # Updated import path
from pydantic import BaseModel, Field


# Define your desired data structure - like a python data class.
class ITSupportResponse(BaseModel):
    orig_msg: str = Field(description="The original customer IT support query message")
    orig_lang: str = Field(description="Detected language of the customer message e.g. Spanish")
    category: str = Field(description="1-2 word describing the category of the problem")
    trans_msg: str = Field(description="Translated customer IT support query message in English")
    response: str = Field(description="Response to the customer in their original language - orig_lang")
    trans_response: str = Field(description="Response to the customer in English")


parser = JsonOutputParser(pydantic_object=ITSupportResponse)


# ### Create the input prompt for the LLM


# create the final prompt with formatting instructions from the parser
prompt_txt = """
             Act as an Information Technology (IT) customer support agent.
             For the IT support message mentioned below
             use the following output format when generating the output response

             Output format instructions:
             {format_instructions}

             Customer IT support message:
             {it_support_msg}
             """
prompt = PromptTemplate(
    template=prompt_txt,
    input_variables=["it_support_msg"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)


# ### Create a LCEL LLM Chain


# create a simple LCEL chain to take the prompt, pass it to the LLM, enforce response format using the parser
llm_chain = (prompt
              |
            chatgpt
              |
            parser)


# ### Access Customer IT Support ticket data


it_support_queue = [
    "Não consigo sincronizar meus contatos com o telefone. Sempre recebo uma mensagem de falha.",
    "Ho problemi a stampare i documenti da remoto. Il lavoro non viene inviato alla stampante di rete.",
    "プリンターのトナーを交換しましたが、印刷品質が低下しています。サポートが必要です。",
    "Я не могу войти в систему учета времени, появляется сообщение об ошибке. Мне нужна помощь.",
    "Internet bağlantım çok yavaş ve bazen tamamen kesiliyor. Yardım eder misiniz?",
    "Не могу установить обновление безопасности. Появляется код ошибки. Помогите, пожалуйста."
]

formatted_msgs = [{"it_support_msg": msg}
                    for msg in it_support_queue]
formatted_msgs[0]


# ### Get responses from the LLM


responses = llm_chain.map().invoke(formatted_msgs)


# ### View LLM responses


responses[0]


type(responses[0])


import pandas as pd

df = pd.DataFrame(responses)
df


# Try out more use-cases based on your own problems using what you learnt!





