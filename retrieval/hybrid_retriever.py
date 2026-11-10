# retrieval/hybrid_retriever.py
# Owner: Mariem
#
# Merges FAISS and Neo4j results, deduplicates by chunk_id.

from retrieval.faiss_retriever import retrieve_vector
from retrieval.graph_retriever import retrieve_graph


def retrieve(query: str, k: int = 5, use_graph: bool = True) -> list[dict]:
    # TODO: combine both result sets (graph only if use_graph), deduplicate by chunk_id,
    #       return top-k as [{chunk_id, text, url, framework, score}]
    raise NotImplementedError
