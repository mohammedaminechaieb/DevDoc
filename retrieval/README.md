# retrieval/ - Hybrid Retrieval
Owner: Ghassen | Branch: feat/retrieval
Other file here: graph_retriever.py (Oussema)
Ghassen also owns: generation/reranker.py, agents/knowledge_retriever.py

## Pipeline
1. embedder.py - sentence-transformers
2. faiss_indexer.py - build + save FAISS index and metadata to `data/` (run once)
3. faiss_retriever.py - vector search
4. graph_retriever.py (Oussema) - Neo4j traversal
5. hybrid_retriever.py - merge + deduplicate, used by `agents/knowledge_retriever.py`

Chunk format returned by every retriever: `{chunk_id, text, url, framework, score}`

## Run
~~~
python -m retrieval.faiss_indexer
~~~
