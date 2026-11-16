# retrieval/faiss_indexer.py
# Owner: Mariem
#
# Reads CORPUS_PATH, embeds every chunk, builds a FAISS index and saves it to FAISS_INDEX.
# Also writes FAISS_META (one chunk per line, same order as the index) to map ids -> chunks.
# Run: python -m retrieval.faiss_indexer

import os
import json
import faiss
from config.settings import CORPUS_PATH, FAISS_INDEX, FAISS_META, EMBED_MODEL
from retrieval.embedder import CustomEmbedder  # Assumes you updated your embedder class name

def build_index():
    # 1. Setup paths based on config/settings.py
    # Settings already resolves to absolute paths, so this is safe for Docker
    os.makedirs(os.path.dirname(FAISS_INDEX), exist_ok=True)
    
    # Pass the EMBED_MODEL from settings to your embedder
    print(f"Initializing embedder with model: {EMBED_MODEL}")
    embedder = CustomEmbedder(model_name=EMBED_MODEL, batch_size=16)
    
    texts = []
    metadata = []
    
    # 2. Load corpus
    print(f"Loading corpus from {CORPUS_PATH}...")
    with open(CORPUS_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
                
            doc = json.loads(line.strip())
            texts.append(doc["text"])
            
            metadata.append({
                "chunk_id": doc.get("chunk_id", ""),
                "text": doc["text"],
                "url": doc.get("url", ""),
                "framework": doc.get("framework", "")
            })
            
    # 3. Embed chunks
    print("Embedding chunks...")
    # Update this line depending on whether your embedder returns sparse weights too
    dense_vecs = embedder.embed_corpus(texts) 
    
    # 4. Build FAISS index
    print("Building FAISS index...")
    dimension = dense_vecs.shape[1]
    
    # Using L2 distance (or IP if vectors are normalized)
    index = faiss.IndexFlatL2(dimension)
    index.add(dense_vecs)
    
    # 5. Save index and metadata
    print(f"Saving FAISS index to {FAISS_INDEX}")
    faiss.write_index(index, FAISS_INDEX)
    
    print(f"Saving FAISS metadata to {FAISS_META}")
    with open(FAISS_META, 'w', encoding='utf-8') as f:
        for i, meta in enumerate(metadata):
            f.write(json.dumps(meta) + '\n')

def load_index():
    import faiss
    return faiss.read_index(FAISS_INDEX)

if __name__ == "__main__":
    build_index()
    print("FAISS index built.")