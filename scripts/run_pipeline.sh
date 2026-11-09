#!/bin/bash
# Run from the repo root: bash scripts/run_pipeline.sh
set -e
python -m retrieval.faiss_indexer
python -m graph.neo4j_loader
uvicorn api.main:app --reload
