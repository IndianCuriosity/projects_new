from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a macro quant assistant."),
    ("human", "Explain {concept} using a {style} style."),
])

messages = prompt.invoke({"concept": "RAG", "style": "trading infrastructure"})
print(messages)
