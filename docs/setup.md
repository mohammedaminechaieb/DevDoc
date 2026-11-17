# Setup Guide

Commands are for Windows PowerShell, run from the repo root
(macOS/Linux: `source venv/bin/activate`, `cp` instead of `Copy-Item`).
Prerequisites: Python 3.10+, Node.js 18+, Docker Desktop.

## 1. Backend environment
~~~
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -r graph/requirements-extraction.txt      # GLiNER + torch for the graph extraction
python -m spacy download en_core_web_sm
Copy-Item config\.env.example config\.env
~~~
Edit `config\.env`:
- `LLM_PROVIDER=gemini` and `GEMINI_API_KEY=...` (default), or `LLM_PROVIDER=groq` + `GROQ_API_KEY`,
  or `LLM_PROVIDER=ollama` (local, e.g. `LLM_MODEL=mistral:7b`, no key).
- `LLM_RPM=10` for the graph extraction on the Gemini free tier.

## 2. Unit tests (no external service needed)
~~~
pytest tests -q
~~~
Expected: 101 passed, 3 skipped (2 FAISS smoke tests until the index exists, 1 live test).

## 3. Vector index (run once, ~3 min CPU)
~~~
python -m retrieval.faiss_indexer
~~~
Writes `data/faiss.index` and `data/faiss_meta.jsonl` (git-ignored).

## 4. Neo4j + knowledge graph
~~~
docker compose up neo4j -d                 # browser: http://localhost:7474  (neo4j / password)
python -m graph.pipeline --estimate        # size of the LLM step
python -m graph.pipeline --llm-max-chunks 300   # quality profile; re-run = resume
python -m graph.neo4j_loader --reset       # loads data/graph/ into Neo4j
~~~
Fast alternative without any LLM call: `python -m graph.pipeline --profile standard`.
See graph/README.md for profiles and outputs.

## 5. Smoke test (no API)
~~~
python -m agents.orchestrator "How does LangGraph handle memory and checkpoints?"
python -m agents.orchestrator --mermaid    # graph of the orchestrator for the report
~~~
First run downloads the reranker model (BAAI/bge-reranker-base, ~1 GB).
With Neo4j empty or down the answer still works (FAISS only, warning in the log).

## 6. API
~~~
uvicorn api.main:app --reload
~~~
Swagger: http://localhost:8000/docs - `POST /api/query`, `GET /health`.

## 7. Frontend
~~~
cd frontend
npm install
npm run dev
~~~
App: http://localhost:5173 (proxies /api and /health to :8000). The "Knowledge graph"
switch toggles hybrid (FAISS + Neo4j) vs vector-only retrieval.

## 8. Evaluation
~~~
python -m tests.eval.evaluate --compare    # 22 questions, vector-only vs hybrid -> data/eval/
$env:RUN_LIVE_TESTS = "1"; pytest tests/integration -q
~~~

## Everything in Docker
~~~
docker compose up --build                  # api + neo4j, data/ mounted
docker compose -f docker-compose.yml -f docker-compose.graph.yml run --rm graph   # graph job
~~~

## Rebuild the corpus (optional)
~~~
python scripts/fetch_full_docs_v3.py
~~~
