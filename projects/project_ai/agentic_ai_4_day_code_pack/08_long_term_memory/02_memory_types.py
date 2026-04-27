"""
Memory types:
- Episodic: what happened
- Semantic: durable facts
- Procedural: how to do things
"""

memories = [
    {"type": "episodic", "text": "On Day 1, user built a Chroma RAG demo."},
    {"type": "semantic", "text": "User specializes in FX volatility and systematic options trading."},
    {"type": "procedural", "text": "For FX vol analysis, retrieve market data, compute implied-vs-realized, inspect skew, then check event risk."},
]

for m in memories:
    print(f"{m['type'].upper()}: {m['text']}")
