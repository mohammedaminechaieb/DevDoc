# generation/reranker.py
# Owner: Mariem


def rerank(query: str, chunks: list[dict]) -> list[dict]:
    # TODO: score each chunk against query (cross-encoder or BM25 fallback)
    # Returns chunks sorted by relevance score descending
    raise NotImplementedError
