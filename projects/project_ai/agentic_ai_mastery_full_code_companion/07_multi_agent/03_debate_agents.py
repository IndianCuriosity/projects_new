from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

bull = llm.invoke("Argue FOR buying EURUSD gamma before an ECB event.").content
bear = llm.invoke("Argue AGAINST buying EURUSD gamma before an ECB event.").content

judge = llm.invoke(f"""
Bull case:
{bull}

Bear case:
{bear}

As a neutral PM, decide what extra data is needed before trading.
""").content

print(judge)
