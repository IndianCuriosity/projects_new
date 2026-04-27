from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

test_cases = [
    {"input": "What is window memory?", "must_contain": ["last", "messages"]},
    {"input": "What is RAG?", "must_contain": ["retrieve", "context"]},
]

for case in test_cases:
    output = llm.invoke(case["input"]).content.lower()
    passed = all(term in output for term in case["must_contain"])
    print(case["input"], "PASS" if passed else "FAIL")
    print(output[:300], "\n")
