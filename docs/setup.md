# Setup Guide

## Backend
`
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp config/.env.example config/.env
`

## Neo4j
`
docker compose up neo4j -d
`

## Build indexes (run once)
`
python -m retrieval.faiss_indexer
python -m graph.neo4j_loader
`

## Run API
`
uvicorn api.main:app --reload
`

## Run Frontend
`
cd frontend && npm install && npm run dev
`
"@

W "docs\api_reference.md" @"
# API Reference

## GET /health  (owner: Aya)
{"status": "ok", "service": "devdoc-ai"}

## POST /api/query  (owner: Mariem)
Request:  {"question": str, "top_k": 5, "use_graph": true}
Response: {"answer": str, "sources": [{url, framework, text}], "query": str}
