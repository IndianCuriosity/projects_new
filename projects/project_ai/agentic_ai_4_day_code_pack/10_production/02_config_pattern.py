"""
Config pattern:
Keep model names, collection names, and paths configurable.
"""

from dataclasses import dataclass

@dataclass
class AgentConfig:
    model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    chroma_dir: str = "./chroma_prod"
    collection_name: str = "fx_vol_agent_memory"
    retrieval_k: int = 5
    temperature: float = 0.0

config = AgentConfig()
print(config)
