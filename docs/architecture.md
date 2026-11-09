# Architecture - Agentic AI Copilot

Specification: [NLP.pdf](../NLP.pdf)

## Request flow
```
React UI (frontend/)
   | POST /api/query {question, top_k, use_graph, history}
   v
FastAPI (api/) --> agents.orchestrator.run_copilot()
   |
   v  LangGraph StateGraph (agents/)
   intent_analyzer       -> intent: learn | recommend | design | code | explore | evaluate
   knowledge_retriever   -> retrieval.hybrid_retriever  (FAISS + Neo4j)
   route by intent:
      learn / explore     -> responder            (generation.answer_generator)
      recommend / design  -> architecture_advisor
      code                -> code_assistant
      evaluate            -> evaluation_assistant
   reviewer              -> evaluation_assistant.review (grounding + citations)
   |
   v
{query, intent, answer, sources, graph}
```

## Offline build
```
full_corpus/full_corpus_clean.jsonl   (built by scripts/fetch_full_docs_v3.py)
    |
    +--[Oussema]--> graph/  entity + relation extraction --> Neo4j
    |
    +--[Ghassen]--> retrieval/faiss_indexer --> data/faiss.index + data/faiss_meta.jsonl
```

## Corpus
6,161 chunks, each with `chunk_id, source_id, url, framework, concept, component,
version, char_start, text`. Frameworks: crewai, langchain, openai, langgraph,
anthropic, mcp, autogen, foundational.

## Knowledge graph
See [graph/README.md](../graph/README.md) and `graph/schema.py`.
Nodes: Concept, Framework, Component, Technology, Technique, Chunk.
Relations: IMPLEMENTS, USES, HAS, DELEGATES_TO, CONTAINS, CONNECTS, SUPPORTS,
ALTERNATIVE_TO, MENTIONED_IN (each with its source chunk_id / url).

## Cross-module map
| Person  | Primary | Also writes |
|---------|---------|-------------|
| Oussema | graph/ | retrieval/graph_retriever.py |
| Ghassen | retrieval/ | graph/queries.py |
| Mariem  | generation/ | api/routes/query.py |
| Amine   | api/ | generation/reranker.py |
| Aya     | frontend/ | api/routes/health.py, tests/eval/ |
| _to assign_ | agents/ | - |
