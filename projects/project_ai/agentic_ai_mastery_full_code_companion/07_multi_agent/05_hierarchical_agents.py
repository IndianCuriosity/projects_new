from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

manager_plan = llm.invoke("Break FX vol trade research into specialist tasks.").content
researcher_result = llm.invoke(f"Complete the data/research task from this plan:\n{manager_plan}").content
risk_result = llm.invoke(f"Complete the risk-review task from this plan:\n{manager_plan}").content

final = llm.invoke(f"""
Manager plan:
{manager_plan}

Research result:
{researcher_result}

Risk result:
{risk_result}

Create final recommendation.
""").content

print(final)
