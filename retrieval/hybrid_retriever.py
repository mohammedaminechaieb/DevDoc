# retrieval/hybrid_retriever.py
import logging
from typing import Any

from retrieval.faiss_retriever import search_faiss

logger = logging.getLogger(__name__)


def rrf_merge(
    ranked_lists: list[list[dict[str, Any]]],
    k_rrf: int = 60,
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """
    Deduplicate chunks by 'chunk_id' and fuse multiple ranked lists using
    Reciprocal Rank Fusion: score = sum(1 / (k_rrf + rank)).
    """
    fused_scores: dict[str, float] = {}
    chunk_store: dict[str, dict[str, Any]] = {}

    for result_list in ranked_lists:
        for rank, chunk in enumerate(result_list, start=1):
            cid = str(chunk.get("chunk_id") or hash(chunk.get("text", "")))
            fused_scores[cid] = fused_scores.get(cid, 0.0) + (1.0 / (k_rrf + rank))
            if cid not in chunk_store:
                chunk_store[cid] = dict(chunk)

    merged: list[dict[str, Any]] = []
    for cid, rrf_score in sorted(fused_scores.items(), key=lambda x: x[1], reverse=True):
        entry = chunk_store[cid]
        entry["rrf_score"] = rrf_score
        entry["score"] = rrf_score
        merged.append(entry)

    return merged[:top_k]


def retrieve(
    query: str,
    k: int = 10,
    use_graph: bool = True,
) -> list[dict[str, Any]]:
    """Retrieve candidate chunks from FAISS and optionally fuse with Neo4j graph search."""
    vector_chunks = search_faiss(query, k=k)
    ranked_lists = [vector_chunks]

    if use_graph:
        try:
            from retrieval.graph_retriever import retrieve_graph  # type: ignore

            graph_chunks = retrieve_graph(query, k=k)
            if graph_chunks:
                ranked_lists.append(graph_chunks)
        except ImportError:
            logger.debug("graph_retriever.retrieve_graph not available yet; using FAISS only.")
        except Exception as exc:
            logger.warning("Graph retrieval failed (%s); falling back to FAISS only.", exc)

    return rrf_merge(ranked_lists, top_k=k)