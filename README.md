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
| Person  | Primary module | Branch          | Also contributes to                          |
|---------|----------------|-----------------|----------------------------------------------|
| Oussema | graph/         | feat/graph      | retrieval/graph_retriever.py                 |
| Ghassen | retrieval/     | feat/retrieval  | graph/queries.py                             |
| Mariem  | generation/    | feat/generation | api/routes/query.py                          |
| Amine   | api/           | feat/api        | generation/reranker.py                       |
| Aya     | frontend/      | feat/frontend   | api/routes/health.py + tests/eval/           |
| _to assign_ | agents/    | feat/agents     | -                                            |

## Quick start
See [docs/setup.md](docs/setup.md). Architecture: [docs/architecture.md](docs/architecture.md).
API: [docs/api_reference.md](docs/api_reference.md).
