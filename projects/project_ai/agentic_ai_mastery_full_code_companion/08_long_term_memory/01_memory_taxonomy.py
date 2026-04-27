memories = [
    ("episodic", "User asked about ConversationSummaryMemory yesterday."),
    ("semantic", "User specializes in FX volatility."),
    ("procedural", "To analyze long gamma, compare implied vol, realized vol, theta, costs, and event risk."),
]

for kind, text in memories:
    print(kind.upper(), "=>", text)
