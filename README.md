# Agentic AI Copilot

An assistant for students, developers and engineers who want to **learn, design and build
Agentic AI systems** (LangGraph, CrewAI, AutoGen, MCP, tool calling, memory, RAG...).

It combines a **LangGraph multi-agent orchestrator** with **Hybrid GraphRAG**:
- **FAISS** vector search over the official documentation corpus
- a **Neo4j** knowledge graph of concepts, frameworks, components, protocols and techniques

Project specification: [`NLP.pdf`](NLP.pdf).

## Features (NLP.pdf section 4)
| | Feature | Handled by (intent) |
|---|---|---|
| A | Agentic AI Learning Assistant | `responder` (`learn`) |
| B | Framework Recommendation | `architecture_advisor` (`recommend`) |
| C | Agentic Architecture Designer | `architecture_advisor` (`design`) |
| D | Code Assistant | `code_assistant` (`code`) |
| E | Agentic Workflow Explorer | `responder` + graph view (`explore`) |
| F | Evaluation and Optimization Assistant | `evaluation_assistant` (`evaluate`) |

## Tech stack
| Component | Technology |
|---|---|
| Language | Python 3.10+ |
| Agent orchestration | LangGraph |
| LLM | Groq API or Ollama |
| Embeddings | Sentence Transformers |
| Vector search | FAISS |
| Knowledge graph | Neo4j |
| Backend | FastAPI |
| Frontend | React (Vite) |

## Repository layout
```
agents/        LangGraph orchestrator + the 5 agent roles
graph/         entity/relation extraction -> Neo4j
retrieval/     embeddings, FAISS index, graph retrieval, hybrid merge
generation/    reranker, prompts, LLM client, grounded answer
api/           FastAPI backend (POST /api/query, GET /health)
frontend/      React UI
full_corpus/   full_corpus_clean.jsonl (6,161 chunks, 8 frameworks)
scripts/       corpus builder + pipeline scripts
tests/         unit, integration and evaluation
notebooks/     experiments (launch Jupyter from the repo root)
docs/          architecture, setup, API reference
```

## Team and ownership
Each person works on their own branch and merges into `main` through a pull request.

| Person | Area | Branch | Files |
|---|---|---|---|
| Oussema | Knowledge graph (Neo4j) | feat/graph | `graph/*`, `retrieval/graph_retriever.py`, `tests/unit/test_extractor.py`, `notebooks/01_graph_exploration.ipynb` |
| Ghassen | Vector + hybrid retrieval | feat/retrieval | `retrieval/embedder.py`, `retrieval/faiss_indexer.py`, `retrieval/faiss_retriever.py`, `retrieval/hybrid_retriever.py`, `generation/reranker.py`, `agents/knowledge_retriever.py`, `tests/unit/test_retriever.py`, `notebooks/02_retrieval_experiments.ipynb` |
| Mariem | Generation + specialist agents | feat/generation | `generation/prompt_builder.py`, `generation/llm_client.py`, `generation/answer_generator.py`, `agents/responder.py`, `agents/architecture_advisor.py`, `agents/code_assistant.py`, `tests/unit/test_generator.py`, `notebooks/03_generation_tests.ipynb` |
| Amine | Orchestration + API | feat/api | `agents/orchestrator.py`, `agents/state.py`, `agents/intent_analyzer.py`, `api/*` (except `routes/health.py`), `config/`, `Dockerfile`, `docker-compose.yml`, `tests/unit/test_agents.py`, `tests/unit/test_api.py` |
| Aya | Frontend + evaluation | feat/frontend | `frontend/*`, `api/routes/health.py`, `agents/evaluation_assistant.py`, `tests/eval/*`, `tests/integration/test_pipeline.py`, `notebooks/04_evaluation.ipynb` |

Agent roles of NLP.pdf: Intent Analyzer + orchestrator -> Amine, Knowledge Retrieval -> Ghassen,
Architecture Advisor + Code Assistant -> Mariem, Evaluation Assistant -> Aya.

Shared (change through a PR everyone reviews): `docs/`, `scripts/`, `requirements.txt`, `full_corpus/`, `README.md`.
## Quick start
See [docs/setup.md](docs/setup.md). Architecture: [docs/architecture.md](docs/architecture.md).
API: [docs/api_reference.md](docs/api_reference.md).
