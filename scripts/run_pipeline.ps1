# Run from the repo root: .\scripts\run_pipeline.ps1
$ErrorActionPreference = 'Stop'
python -m retrieval.faiss_indexer
python -m graph.neo4j_loader
uvicorn api.main:app --reload
