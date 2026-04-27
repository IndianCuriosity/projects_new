"""
Critic loop:
Generate answer -> critique answer -> revise answer.
"""

from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

question = "Explain when to use LangGraph instead of a simple LangChain chain."

draft = llm.invoke(question).content

critique = llm.invoke(f"""
Critique the answer below. Look for missing practical details.

Answer:
{draft}
""").content

revised = llm.invoke(f"""
Original question:
{question}

Draft:
{draft}

Critique:
{critique}

Revise the answer.
""").content

print(revised)
