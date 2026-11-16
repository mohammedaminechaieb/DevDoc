# retrieval/faiss_retriever.py
# Owner: Mariem

import json
import os

import faiss
from config.settings import FAISS_INDEX, FAISS_META
from retrieval.embedder import BGEM3Embedder

# Global variables to ensure we only load the model and index ONCE when the API starts
_index = None
_metadata = []
_embedder = None

def _load_resources():
    """Lazy-loads the heavy assets only when the first query is run."""
    global _index, _metadata, _embedder
    if _index is None:
        for path in (FAISS_INDEX, FAISS_META):
            if not os.path.exists(path):
                raise FileNotFoundError(2, "Index not built: run python -m retrieval.faiss_indexer", path)
        print("Loading FAISS Index into memory...")
        _index = faiss.read_index(FAISS_INDEX)
        
        print("Loading Metadata into memory...")
        with open(FAISS_META, 'r', encoding='utf-8') as f:
            _metadata = [json.loads(line) for line in f]
            
        print("Loading Embedder for live queries...")
        _embedder = BGEM3Embedder(batch_size=1)

def search_faiss(query: str, k: int = 5) -> list[dict]:
    """Embeds the user query and searches the FAISS index."""
    _load_resources()
    
    # 1. Embed the incoming query (we only need the dense vector for FAISS)
    dense_vecs = _embedder.embed_corpus([query])
    
    # 2. Perform the vector search
    distances, indices = _index.search(dense_vecs, k)
    
    # 3. Map the results back to the original text
    results = []
    for i, idx in enumerate(indices[0]):
        if idx == -1:  # FAISS returns -1 if there aren't enough chunks
            continue
            
        chunk_meta = _metadata[idx]
        
        results.append({
            "chunk_id": chunk_meta.get("chunk_id", ""),
            "text": chunk_meta["text"],
            "url": chunk_meta.get("url", ""),
            "framework": chunk_meta.get("framework", ""),
            "score": float(distances[0][i])
        })
        
    return results

if __name__ == "__main__":
    # Quick local test
    test_results = search_faiss("How do I build a LangGraph agent?", k=2)
    for res in test_results:
        print(f"\nScore: {res['score']:.4f} | Framework: {res['framework']}")
        print(f"Text: {res['text'][:150]}...")