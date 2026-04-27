# Set environment variables before running:
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_API_KEY=your_langsmith_key
# LANGCHAIN_PROJECT=agentic-ai-mastery

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_template("Explain {concept} in 3 bullets for a quant developer.")
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
chain = prompt | llm

print(chain.invoke({"concept": "LangSmith tracing"}).content)
