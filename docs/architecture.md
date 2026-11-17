# Architecture - Agentic AI Copilot

Specification: [NLP.pdf](../NLP.pdf)

## Request flow
~~~
React UI (frontend/)  chat + markdown answers + force-graph GraphViewer + health polling
   | POST /api/query {question, top_k, use_graph, history}
   v
FastAPI (api/) --> agents.orchestrator.run_copilot()      422 bad input | 503 index missing | 500 error
   |
   v  LangGraph StateGraph (agents/)
   intent_analyzer      LLM (JSON) with keyword fallback -> intent + graph entities (graph/vocabulary.py)
   knowledge_retriever  hybrid_retriever: FAISS top-3k  +  Neo4j GraphRAG (retrieve_graph)
                        -> Reciprocal Rank Fusion -> cross-encoder reranker -> top_k
                        + retrieve_subgraph(question) -> state["graph"] for the UI
   route by intent:
      learn            -> responder (A)
      explore          -> responder (E)
      recommend/design -> architecture_advisor (B, C)
      code             -> code_assistant (D)
      evaluate         -> evaluation_assistant.run (F)
   reviewer            -> evaluation_assistant.review: citations [n] in range, no invented URLs,
                          vocabulary grounding score, optional LLM judge (REVIEW_USE_LLM=1)
   |
   v
{query, intent, entities, answer, sources, graph, review}
~~~

## LLM provider
`generation/llm_client.call_llm(prompt, system)` is the single entry point.
`LLM_PROVIDER` in `config/.env`: `gemini` (default, GEMINI_API_KEY) | `groq` | `ollama` (local).
Used by the intent analyzer, all specialist agents, the reviewer's judge and the graph LLM extractor.

## Offline build
~~~
full_corpus/full_corpus_clean.jsonl   (6,161 chunks, scripts/fetch_full_docs_v3.py)
    |
    +--[Aya]    python -m graph.pipeline     dictionary -> GLiNER -> LLM relations -> fusion ->
    |                                        entity resolution -> validation -> data/graph/*.jsonl
    |           python -m graph.neo4j_loader data/graph -> Neo4j (Entity, Chunk, MENTIONED_IN, typed relations)
    |
    +--[Mariem] python -m retrieval.faiss_indexer -> data/faiss.index + data/faiss_meta.jsonl
~~~

## Corpus
Each chunk: `chunk_id, source_id, url, framework, concept, component, version, char_start, text`.
Frameworks: crewai, langchain, openai, langgraph, anthropic, mcp, autogen, foundational.

## Knowledge graph
See [graph/README.md](../graph/README.md) and `graph/schema.py` (hybrid open-world schema):
18 node types + Chunk, ~35 relation types incl. the PDF examples (IMPLEMENTS, USES, HAS,
DELEGATES_TO, CONTAINS, CONNECTS) + MENTIONED_IN. Every relation keeps its provenance:
source_chunk_id, source_url, document_version, evidence, extraction_method, confidence, support.

## Evaluation
`python -m tests.eval.evaluate` runs the 22 questions of `tests/eval/questions.json`
(conceptual, comparison, architecture, code, workflow, evaluation, out-of-scope) and reports
intent accuracy, framework hit rate, reviewer acceptance, citation rate, refusal on out-of-scope,
latency. `--compare` runs vector-only vs hybrid (GraphRAG) for the ablation table.

## Ownership
| Person  | Area | Branch |
|---------|------|--------|
| Aya     | graph/, retrieval/graph_retriever.py | feat/graph |
| Mariem  | retrieval/ (vector + hybrid), generation/reranker.py, agents/knowledge_retriever.py | feat/retrieval |
| Ghassen | generation/, agents/responder.py, agents/architecture_advisor.py, agents/code_assistant.py | feat/generation |
| Amine   | api/, config/, agents/orchestrator.py, agents/state.py, agents/intent_analyzer.py, Docker | feat/api |
| Oussema | frontend/, api/routes/health.py, agents/evaluation_assistant.py, tests/eval/, tests/integration/ | feat/frontend |

Full file list: see the root [README](../README.md#team-and-ownership).
