from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

draft = llm.invoke("Explain when long gamma makes money.").content
critique = llm.invoke(f"Critique this answer for missing trading risks:\n{draft}").content
final = llm.invoke(f"Improve the answer using the critique.\nDraft:\n{draft}\nCritique:\n{critique}").content

print(final)
