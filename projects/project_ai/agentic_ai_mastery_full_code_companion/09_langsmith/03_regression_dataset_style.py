from dataclasses import dataclass
from langchain_openai import ChatOpenAI

@dataclass
class TestCase:
    question: str
    expected_keywords: list[str]

tests = [
    TestCase("Explain tool calling.", ["tool", "function"]),
    TestCase("Explain LangGraph.", ["state", "graph"]),
]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

for t in tests:
    answer = llm.invoke(t.question).content.lower()
    passed = all(k in answer for k in t.expected_keywords)
    print(t.question, "PASS" if passed else "FAIL")
