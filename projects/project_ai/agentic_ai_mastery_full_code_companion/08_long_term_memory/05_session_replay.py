session_events = [
    {"role": "user", "content": "I want to master Agentic AI."},
    {"role": "assistant", "content": "Start with LangChain core and memory."},
    {"role": "user", "content": "Show Chroma memory."},
]

for e in session_events:
    print(f"{e['role'].upper()}: {e['content']}")
