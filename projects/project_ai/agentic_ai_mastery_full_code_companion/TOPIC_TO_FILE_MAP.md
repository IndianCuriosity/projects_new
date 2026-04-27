# Topic-to-File Map

## Phase 1 — Foundations
- LLM direct call: `01_foundations/01_llm_direct_answer.py`
- Workflow vs agentic decomposition: `01_foundations/02_workflow_vs_agent.py`
- Structured output: `01_foundations/03_structured_outputs_pydantic.py`
- Tool call request only: `01_foundations/04_tool_call_request_only.py`
- Tool call execution loop: `01_foundations/05_tool_call_execute.py`
- Embeddings and similarity: `01_foundations/06_embeddings_similarity.py`

## Phase 2 — LangChain Core
- Prompt templates: `02_langchain_core/01_prompt_template.py`
- Runnable pipelines: `02_langchain_core/02_runnable_chain.py`
- Structured parser: `02_langchain_core/03_output_parser_json.py`
- Router chain: `02_langchain_core/04_router_chain_fixed.py`
- Streaming: `02_langchain_core/05_streaming.py`
- Retry pattern: `02_langchain_core/06_retry_pattern.py`

## Phase 3 — Memory
- Buffer memory modern: `03_memory/01_buffer_memory_modern.py`
- Window memory modern: `03_memory/02_window_memory_modern.py`
- Summary memory modern: `03_memory/03_summary_memory_modern.py`
- Semantic memory with Chroma: `03_memory/04_chroma_semantic_memory.py`
- Hybrid memory: `03_memory/05_hybrid_memory_summary_plus_window.py`

## Phase 4 — RAG
- Basic Chroma RAG: `04_rag/01_basic_chroma_rag.py`
- Chunking: `04_rag/02_chunking_strategy.py`
- Metadata filtering: `04_rag/03_metadata_filtering.py`
- Multi-query retrieval: `04_rag/04_multi_query_retrieval_simple.py`
- Reranking: `04_rag/05_simple_reranking.py`
- RAG with citations: `04_rag/06_rag_with_citations.py`

## Phase 5 — Tool-Using Agents
- Tool abstraction: `05_tool_agents/01_tool_abstraction.py`
- Tool execution loop: `05_tool_agents/02_tool_call_execute_loop.py`
- Planner-executor: `05_tool_agents/03_planner_executor.py`
- Dynamic tool routing: `05_tool_agents/04_dynamic_tool_routing.py`
- Self-reflection: `05_tool_agents/05_self_reflection.py`

## Phase 6 — LangGraph
- Basic graph: `06_langgraph/01_basic_state_graph.py`
- Conditional routing: `06_langgraph/02_conditional_routing.py`
- Research workflow: `06_langgraph/03_research_workflow.py`
- Retry/error handling: `06_langgraph/04_retry_error_handling.py`
- Human approval gate: `06_langgraph/05_human_in_loop_simulated.py`
- Parallel branches: `06_langgraph/06_parallel_branches_simple.py`

## Phase 7 — Multi-Agent Systems
- Specialist roles: `07_multi_agent/01_specialist_roles.py`
- Coordinator: `07_multi_agent/02_coordinator_agent.py`
- Debate agents: `07_multi_agent/03_debate_agents.py`
- Critic/validator: `07_multi_agent/04_critic_validator.py`
- Hierarchical agents: `07_multi_agent/05_hierarchical_agents.py`

## Phase 8 — Long-Term Memory
- Memory taxonomy: `08_long_term_memory/01_memory_taxonomy.py`
- Durable Chroma memory: `08_long_term_memory/02_chroma_durable_memory.py`
- Procedural memory: `08_long_term_memory/03_procedural_memory.py`
- Simple knowledge graph: `08_long_term_memory/04_knowledge_graph_simple.py`
- Session replay: `08_long_term_memory/05_session_replay.py`

## Phase 9 — LangSmith
- Basic tracing: `09_langsmith/01_tracing_basic.py`
- Local evaluator: `09_langsmith/02_local_evaluator.py`
- Dataset-style regression tests: `09_langsmith/03_regression_dataset_style.py`

## Phase 10 — Production
- FastAPI service: `10_production/01_fastapi_service.py`
- Config pattern: `10_production/02_config_pattern.py`
- Async batch calls: `10_production/03_async_batch.py`
- Dockerfile example: `10_production/Dockerfile`

## Capstone
- FX vol research agent: `11_capstone_fx_vol_agent/01_fx_vol_research_agent.py`
- LangGraph FX vol agent: `11_capstone_fx_vol_agent/02_langgraph_fx_vol_agent.py`
