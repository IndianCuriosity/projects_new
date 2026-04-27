from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def run_agent(role, task):
    prompt = ChatPromptTemplate.from_messages([("system", role), ("human", "{task}")])
    return (prompt | llm).invoke({"task": task}).content

task = "Evaluate long EURUSD gamma before an ECB event."

for role in ["You are a macro strategist.", "You are an FX options quant.", "You are a risk manager."]:
    print("\nROLE:", role)
    print(run_agent(role, task))
