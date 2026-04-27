"""
Simple local evaluator:
Before LangSmith datasets, understand what evaluation means.
"""

from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

test_cases = [
    {"input": "What is window memory?", "must_contain": ["last", "messages"]},
    {"input": "What is RAG?", "must_contain": ["retrieve", "context"]},
]

def answer(q):
    return llm.invoke(q).content.lower()

for case in test_cases:
    output = answer(case["input"])
    passed = all(term in output for term in case["must_contain"])
    print(case["input"], "PASS" if passed else "FAIL")
    print(output[:300], "\n")
