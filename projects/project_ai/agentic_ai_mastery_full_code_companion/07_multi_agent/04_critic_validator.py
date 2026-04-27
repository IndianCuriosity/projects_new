from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

answer = llm.invoke("Recommend a vol trade before ECB.").content

validation = llm.invoke(f"""
Validate this trade recommendation.
Check: missing assumptions, risk, data dependency, overconfidence.

Recommendation:
{answer}
""").content

print(validation)
