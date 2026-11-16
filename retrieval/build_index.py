import json
import pickle
from pathlib import Path
import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
CHUNKS_FILE = PROJECT_ROOT / "corpus_agentic_ai" / "processed_chunks.json"
INDEX_DIR = SCRIPT_DIR / "vector_store"
BM25_FILE = SCRIPT_DIR / "bm25_index.pkl"
KG_FILE = PROJECT_ROOT / "corpus_agentic_ai" / "knowledge_graph_triples.json"

INDEX_DIR.mkdir(parents=True, exist_ok=True)


def load_chunks() -> list[dict]:
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def build_indices():
    chunks = load_chunks()
    print(f"🚀 Loaded {len(chunks)} clean chunks for indexing.\n")

    # 1. Dense Vector Store (ChromaDB)
    print("⏳ [1/3] Generating dense vectors using BAAI/bge-small-en-v1.5...")
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    
    chroma_client = chromadb.PersistentClient(path=str(INDEX_DIR))
    # Reset collection if re-indexing
    try:
        chroma_client.delete_collection("devdoc_chunks")
    except Exception:
        pass
        
    collection = chroma_client.create_collection(
        name="devdoc_chunks",
        metadata={"hnsw:space": "cosine"}
    )

    ids = [c["chunk_id"] for c in chunks]
    documents = [c["content"] for c in chunks]
    metadatas = [
        {
            "doc_id": c["doc_id"],
            "technology": c["technology"],
            "title": c["title"],
            "section_title": c["section_title"],
            "source_url": c["source_url"]
        }
        for c in chunks
    ]

    embeddings = model.encode(documents, show_progress_bar=True, batch_size=32).tolist()

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )
    print(f"  ✓ Vector Index populated: {collection.count()} chunks in ChromaDB.")

    # 2. Sparse BM25 Keyword Index
    print("\n⏳ [2/3] Building sparse BM25 index for exact token matches...")
    tokenized_corpus = [doc.lower().split() for doc in documents]
    bm25 = BM25Okapi(tokenized_corpus)

    with open(BM25_FILE, "wb") as f:
        pickle.dump({"bm25": bm25, "chunks": chunks}, f)
    print(f"  ✓ BM25 index persisted -> {BM25_FILE.relative_to(PROJECT_ROOT)}")

    # 3. Knowledge Graph Triples
    print("\n⏳ [3/3] Generating entity-relation graph triples...")
    triples = []
    for c in chunks:
        triples.append({
            "subject": c["technology"],
            "predicate": "HAS_DOCUMENT",
            "object": c["title"],
            "source_chunk": c["chunk_id"]
        })
        triples.append({
            "subject": c["title"],
            "predicate": "HAS_SECTION",
            "object": c["section_title"],
            "source_chunk": c["chunk_id"]
        })

    with open(KG_FILE, "w", encoding="utf-8") as f:
        json.dump(triples, f, indent=2)
    print(f"  ✓ Knowledge graph saved -> {KG_FILE.relative_to(PROJECT_ROOT)}")

    print("\n✅ Phase 2 Indexing complete.")


if __name__ == "__main__":
    build_indices()