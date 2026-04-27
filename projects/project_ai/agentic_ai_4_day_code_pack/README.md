# Agentic AI 4-Day Mastery Code Pack

This pack gives runnable patterns for the roadmap using modern LangChain, LangGraph, LangSmith, and Chroma.

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -U langchain langchain-openai langchain-community langchain-chroma langgraph langsmith chromadb python-dotenv pandas pydantic fastapi uvicorn
```

Create `.env`:

```bash
OPENAI_API_KEY=your_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=agentic-ai-mastery
```

## 4-Day Plan

Day 1:
- Foundations
- LangChain Core
- Memory

Day 2:
- RAG
- Tool-using agents

Day 3:
- LangGraph
- Multi-agent systems

Day 4:
- Long-term memory
- LangSmith evaluation
- Production deployment
- FX-vol capstone
