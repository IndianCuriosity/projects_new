from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_template("Explain {topic} in 5 bullets.")
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

chain = prompt | llm | StrOutputParser()
print(chain.invoke({"topic": "LangChain Runnable pipelines"}))
