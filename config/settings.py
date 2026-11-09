# config/settings.py - shared by all modules
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent

# config/.env first, then a .env at the repo root (both optional, never committed)
load_dotenv(ROOT / "config" / ".env")
load_dotenv(ROOT / ".env")


def _path(var: str, default: str) -> str:
    """Relative paths are resolved from the repo root, so scripts work from any folder."""
    p = Path(os.getenv(var, default))
    return str(p if p.is_absolute() else ROOT / p)


# Data
CORPUS_PATH = _path("CORPUS_PATH", "full_corpus/full_corpus_clean.jsonl")
FAISS_INDEX = _path("FAISS_INDEX", "data/faiss.index")
FAISS_META  = _path("FAISS_META",  "data/faiss_meta.jsonl")  # chunk order of the FAISS index
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Neo4j
NEO4J_URI  = os.getenv("NEO4J_URI",  "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "password")

# LLM
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")  # groq | ollama
LLM_MODEL    = os.getenv("LLM_MODEL",    "llama-3.1-8b-instant")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OLLAMA_URL   = os.getenv("OLLAMA_URL",   "http://localhost:11434")

# Retrieval
TOP_K = int(os.getenv("TOP_K", "5"))
