# Setup Guide

Commands are for Windows PowerShell, run from the repo root
(on macOS/Linux use `source venv/bin/activate` and `cp`).

## Backend
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
Copy-Item config\.env.example config\.env
```
Then edit `config\.env` and set `GROQ_API_KEY` (or `LLM_PROVIDER=ollama`).

## Neo4j
```
docker compose up neo4j -d
```
Browser: http://localhost:7474 (neo4j / password)

## Build indexes (run once)
```
python -m retrieval.faiss_indexer
python -m graph.neo4j_loader
```

## Run API
```
uvicorn api.main:app --reload
```
Swagger: http://localhost:8000/docs

## Run frontend
```
cd frontend
npm install
npm run dev
```

## Tests
```
pytest tests/unit
python -m tests.eval.evaluate
```

## Rebuild the corpus (optional)
```
python scripts/fetch_full_docs_v3.py
```

## Everything in Docker
```
docker compose up --build
```
