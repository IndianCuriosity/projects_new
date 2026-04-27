graph = {
    "Long Gamma": ["benefits from realized vol", "costs theta", "requires delta hedging"],
    "Event Vol": ["can inflate implied vol", "can cause vol crush"],
    "Risk Reversal": ["measures skew", "reflects call-put demand imbalance"],
}

for node, edges in graph.items():
    print(node)
    for edge in edges:
        print("  ->", edge)
