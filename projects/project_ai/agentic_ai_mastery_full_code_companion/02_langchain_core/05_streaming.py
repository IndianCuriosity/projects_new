from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

for chunk in llm.stream("Explain tool calling in LangChain."):
    print(chunk.content, end="", flush=True)
