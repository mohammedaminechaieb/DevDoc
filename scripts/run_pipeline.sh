#!/bin/bash
set -e
python -m retrieval.faiss_indexer
python -m graph.neo4j_loader
uvicorn api.main:app --reload
