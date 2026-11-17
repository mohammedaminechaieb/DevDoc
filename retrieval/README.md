# retrieval/ - Hybrid Retrieval
Owner: Mariem | Branch: feat/retrieval
Other file here: graph_retriever.py (Aya)
Mariem also owns: generation/reranker.py, agents/knowledge_retriever.py

## Pipeline
1. embedder.py - one sentence-transformers model (`EMBED_MODEL`) for indexing AND queries, normalised vectors
2. faiss_indexer.py - builds `data/faiss.index` + `data/faiss_meta.jsonl` (run once)
3. faiss_retriever.py - `search_faiss(query, k)` (503 from the API if the index is missing)
4. graph_retriever.py (Aya) - `retrieve_graph(query, k)`: question entities -> Neo4j neighbourhood -> evidence chunks
5. hybrid_retriever.py - `retrieve(query, k, use_graph)`: **Reciprocal Rank Fusion** of the FAISS and graph
   lists (score = sum 1/(60+rank), dedup by chunk_id). Graph unavailable or empty -> vector only + warning.
6. generation/reranker.py - cross-encoder `BAAI/bge-reranker-base` re-scores the fused candidates
7. agents/knowledge_retriever.py - asks for 3 x top_k candidates, reranks to top_k, adds the subgraph for the UI

Chunk format returned by every retriever: `{chunk_id, text, url, framework, score}`
(FAISS `score` is an L2 distance; after fusion `score` is the RRF score; after reranking `rerank_score` is added).

## Run
~~~
python -m retrieval.faiss_indexer
python -c "from retrieval.hybrid_retriever import retrieve; print(retrieve('How does LangGraph handle memory?', k=3))"
~~~
