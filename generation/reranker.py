# generation/reranker.py
# Owner: Mariem


import logging
from typing import Any
from FlagEmbedding import FlagReranker

logger = logging.getLogger(__name__)

DEFAULT_RERANKER_MODEL = "BAAI/bge-reranker-base"
_reranker_instance: FlagReranker | None = None


def _get_reranker(model_name: str = DEFAULT_RERANKER_MODEL) -> FlagReranker:
    """Lazy-load and cache the FlagReranker model in memory."""
    global _reranker_instance
    if _reranker_instance is None:
        logger.info("Loading cross-encoder reranker: %s", model_name)
        # use_fp16=True speeds up GPU inference and safely falls back to fp32 on CPU
        _reranker_instance = FlagReranker(model_name, use_fp16=True)
    return _reranker_instance


def rerank(
    query: str,
    chunks: list[dict[str, Any]],
    top_k: int = 5,
    model_name: str = DEFAULT_RERANKER_MODEL,
    enabled: bool = True,
) -> list[dict[str, Any]]:
    """
    Re-score and sort retrieved chunks against the query using a cross-encoder.

    Args:
        query: User query string.
        chunks: Candidate chunk dicts from hybrid_retriever (must contain 'text').
        top_k: Number of top-scoring chunks to return.
        model_name: Hugging Face cross-encoder model ID.
        enabled: Bypass flag; returns chunks[:top_k] if False.

    Returns:
        Top-k chunk dicts sorted by cross-encoder relevance score (descending),
        preserving all original metadata and adding 'rerank_score'.
    """
    if not chunks:
        return []

    if not enabled or top_k <= 0:
        return chunks[: max(top_k, 0)]

    # Separate valid text chunks from malformed entries
    valid_chunks = [c for c in chunks if c.get("text", "").strip()]
    if not valid_chunks:
        return chunks[:top_k]

    pairs = [[query, c["text"]] for c in valid_chunks]

    try:
        reranker = _get_reranker(model_name)
        raw_scores = reranker.compute_score(pairs)

        # FlagReranker returns a single float instead of a list when len(pairs) == 1
        if isinstance(raw_scores, (int, float)):
            scores = [float(raw_scores)]
        else:
            scores = [float(s) for s in raw_scores]

        reranked: list[dict[str, Any]] = []
        for chunk, score in zip(valid_chunks, scores):
            updated = dict(chunk)
            updated["rerank_score"] = score
            reranked.append(updated)

        reranked.sort(key=lambda item: item["rerank_score"], reverse=True)
        return reranked[:top_k]

    except Exception as exc:
        logger.warning(
            "Reranking failed (%s); falling back to original retrieval order.", exc
        )
        return chunks[:top_k]


if __name__ == "__main__":
    sample_query = "How do I create a stateful graph in LangGraph?"
    sample_chunks = [
        {
            "chunk_id": "1",
            "text": "FastAPI uses Pydantic models for request validation.",
            "framework": "fastapi",
            "score": 0.62,
        },
        {
            "chunk_id": "2",
            "text": "In LangGraph, StateGraph is initialized with a state schema and compiled into a runnable.",
            "framework": "langgraph",
            "score": 0.65,
        },
        {
            "chunk_id": "3",
            "text": "Docker Compose mounts host volumes using the volumes key.",
            "framework": "docker",
            "score": 0.68,
        },
    ]

    results = rerank(sample_query, sample_chunks, top_k=2)
    for r in results:
        print(f"[{r['rerank_score']:.4f}] ({r['framework']}) {r['text']}")