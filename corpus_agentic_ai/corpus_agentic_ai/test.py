"""
Agentic AI Copilot — RAG test script v3
No OpenAI key needed. Uses free local HuggingFace embeddings.

Install:
    pip install langchain langchain-community faiss-cpu sentence-transformers

Usage:
    python test_v3.py
    python test_v3.py --corpus full_corpus/full_corpus_clean.jsonl
    python test_v3.py --query "how does LangGraph handle state?"
"""

import argparse
import json
from pathlib import Path

from langchain_core.documents import Document                    # fixed import
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

DEFAULT_CORPUS = "corpus_clean.jsonl"
EMBED_MODEL    = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K          = 5

TEST_QUERIES = [
    "How does LangGraph manage agent state?",
    "What is the difference between CrewAI and AutoGen?",
    "How do I add human-in-the-loop to a LangGraph workflow?",
    "What is the Model Context Protocol?",
    "How does ReAct combine reasoning and acting?",
]

def load_corpus(path: str) -> list[Document]:
    docs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            c = json.loads(line)
            docs.append(Document(
                page_content=c["text"],
                metadata={
                    "chunk_id":  c.get("chunk_id", ""),
                    "source_id": c.get("source_id", ""),
                    "framework": c.get("framework", ""),
                    "concept":   c.get("concept", ""),
                    "url":       c.get("url", ""),
                    "version":   c.get("version", ""),
                    "quality":   c.get("quality_score", 0),
                },
            ))
    return docs

def build_index(docs: list[Document]) -> FAISS:
    print(f"Loading embedding model: {EMBED_MODEL}  (first run downloads ~80 MB)")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    print(f"Building FAISS index for {len(docs)} chunks …")
    vs = FAISS.from_documents(docs, embeddings)
    print("Index ready.\n")
    return vs

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default=DEFAULT_CORPUS)
    parser.add_argument("--query", default=None)
    parser.add_argument("--top-k", type=int, default=TOP_K)
    args = parser.parse_args()

    corpus_path = Path(args.corpus)
    if not corpus_path.exists():
        # try common locations
        for candidate in [
            Path("corpus_v2") / "corpus_clean.jsonl",
            Path("full_corpus") / "full_corpus_clean.jsonl",
            Path("corpus_agentic_ai") / "corpus_clean.jsonl",
        ]:
            if candidate.exists():
                corpus_path = candidate
                break
        else:
            print(f"Corpus file not found: {args.corpus}")
            print("Pass --corpus <path/to/corpus_clean.jsonl>")
            return

    print(f"Loading corpus from: {corpus_path}")
    docs = load_corpus(str(corpus_path))
    print(f"Loaded {len(docs)} chunks.\n")

    vs = build_index(docs)
    queries = [args.query] if args.query else TEST_QUERIES

    for q in queries:
        print("=" * 70)
        print(f"QUERY: {q}")
        print("-" * 70)
        results = vs.similarity_search(q, k=args.top_k)
        for i, doc in enumerate(results, 1):
            m = doc.metadata
            print(f"\n  [{i}] framework={m['framework']}  concept={m['concept']}  quality={m['quality']:.2f}")
            print(f"      source: {m['source_id']}")
            snippet = doc.page_content[:200].replace("\n", " ")
            print(f"      text:   {snippet}…")
        print()

    print("Done. RAG retrieval is working.")

if __name__ == "__main__":
    main()