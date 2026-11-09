# retrieval/faiss_retriever.py
# Primary owner: Ghassen

from retrieval.embedder import embed
from retrieval.faiss_indexer import load_index


def retrieve_vector(query: str, k: int = 5) -> list[dict]:
    # TODO: embed query, search FAISS, map indices back to chunks via FAISS_META
    # Returns: [{chunk_id, text, url, framework, score}]
    raise NotImplementedError
