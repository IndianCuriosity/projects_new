from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_retry(stop_after_attempt=3)
prompt = ChatPromptTemplate.from_template("Explain {topic} briefly.")
chain = prompt | llm

print(chain.invoke({"topic": "retries in agent pipelines"}).content)
