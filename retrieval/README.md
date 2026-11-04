# retrieval/ - Hybrid Retrieval
Primary owner: Ghassen | Branch: feat/retrieval
Cross-module contribution here: Oussema (graph_retriever.py)
Ghassen contributes to: graph/queries.py

## Pipeline
1. embedder.py - sentence-transformers
2. faiss_indexer.py - build + save FAISS index (run once)
3. faiss_retriever.py - vector search
4. graph_retriever.py (Oussema) - Neo4j traversal
5. hybrid_retriever.py - merge + deduplicate

## Run
`
python -m retrieval.faiss_indexer
`
"@

# ══════════════════════════════════════════════════════════════════════════════
# GENERATION/ - primary: Mariem
# generation/reranker.py written by Amine (cross-module)
# api/routes/query.py written by Mariem (cross-module, see api/)
# ══════════════════════════════════════════════════════════════════════════════
W "generation\__init__.py" "# generation/__init__.py"

# generation/reranker.py - written by Amine (cross-module contribution)
W "generation\reranker.py" @"
# generation/reranker.py
# Cross-module owner: Amine
#
# Amine writes this because he owns the API and needs to know
# exactly what score fields come out before wiring the route.

def rerank(query: str, chunks: list[dict]) -> list[dict]:
    # TODO: score each chunk against query (cross-encoder or BM25 fallback)
    # Returns chunks sorted by relevance score descending
    raise NotImplementedError
