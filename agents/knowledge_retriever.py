# agents/knowledge_retriever.py
# Owner: Mariem
# Role: Knowledge Retrieval - queries the docs through FAISS + the Neo4j graph.

import logging
from typing import Any

from agents.state import CopilotState
from retrieval.hybrid_retriever import retrieve
from generation.reranker import rerank

logger = logging.getLogger(__name__)

DEFAULT_CANDIDATE_K = 15


def _fetch_subgraph(question: str) -> dict[str, list[Any]]:
    """
    Fetch the Neo4j subgraph around entities in the question for the frontend GraphViewer.
    Falls back to an empty graph until Eya's graph_retriever branch is merged.
    """
    try:
        from retrieval.graph_retriever import retrieve_subgraph  # type: ignore

        subgraph = retrieve_subgraph(question)
        return {
            "nodes": subgraph.get("nodes", []),
            "edges": subgraph.get("edges", []),
        }
    except ImportError:
        logger.debug("graph_retriever.retrieve_subgraph not available yet; returning empty graph.")
    except Exception as exc:
        logger.warning("Subgraph lookup failed (%s); returning empty graph.", exc)

    return {"nodes": [], "edges": []}


def run(state: CopilotState) -> dict:
    question = state.get("question", "").strip()
    if not question:
        logger.warning("knowledge_retriever.run received an empty question.")
        return {"chunks": [], "graph": {"nodes": [], "edges": []}}

    top_k = int(state.get("top_k", 5))
    use_graph = bool(state.get("use_graph", True))
    use_reranker = bool(state.get("use_reranker", True))

    candidate_k = max(top_k * 3, DEFAULT_CANDIDATE_K) if use_reranker else top_k

    candidates = retrieve(
        question,
        k=candidate_k,
        use_graph=use_graph,
    )

    chunks = rerank(
        query=question,
        chunks=candidates,
        top_k=top_k,
        enabled=use_reranker,
    )

    graph = _fetch_subgraph(question) if use_graph else {"nodes": [], "edges": []}

    return {"chunks": chunks, "graph": graph}