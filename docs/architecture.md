# Architecture - DevDoc AI

## Cross-module map
  Oussema  -> graph/ (primary)  +  retrieval/graph_retriever.py
  Ghassen  -> retrieval/ (primary)  +  graph/queries.py
  Mariem   -> generation/ (primary)  +  api/routes/query.py
  Amine    -> api/ (primary)  +  generation/reranker.py
  Aya      -> frontend/ (primary)  +  api/routes/health.py  +  tests/eval/

## Pipeline
  full_corpus_clean.jsonl
    |
    +--[Oussema]--> graph/ --> Neo4j
    |
    +--[Ghassen]--> retrieval/faiss_indexer --> FAISS index
                        |
                hybrid_retriever (FAISS + Neo4j)
                        |
                [Mariem] generation/ --> LLM answer
                        |
                [Amine]  api/ --> FastAPI
                        |
                [Aya]    frontend/ --> React UI
