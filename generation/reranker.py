# generation/reranker.py
# Cross-module owner: Amine
#
# Amine writes this because he owns the API and needs to know
# exactly what score fields come out before wiring the route.


def rerank(query: str, chunks: list[dict]) -> list[dict]:
    # TODO: score each chunk against query (cross-encoder or BM25 fallback)
    # Returns chunks sorted by relevance score descending
    raise NotImplementedError
