# retrieval/hybrid_retriever.py
# Primary owner: Ghassen
#
# Merges FAISS and Neo4j results, deduplicates by chunk_id.

from retrieval.faiss_retriever import retrieve_vector
from retrieval.graph_retriever import retrieve_graph

def retrieve(query: str, k: int = 5) -> list[dict]:
    # TODO: combine both result sets, deduplicate by chunk_id, return top-k
    raise NotImplementedError
