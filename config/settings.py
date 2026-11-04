# config/settings.py - Shared by all modules
from dotenv import load_dotenv
import os

load_dotenv()

CORPUS_PATH  = os.getenv("CORPUS_PATH",  "data/full_corpus_clean.jsonl")
NEO4J_URI    = os.getenv("NEO4J_URI",    "bolt://localhost:7687")
NEO4J_USER   = os.getenv("NEO4J_USER",   "neo4j")
NEO4J_PASS   = os.getenv("NEO4J_PASS",   "password")
FAISS_INDEX  = os.getenv("FAISS_INDEX",  "data/faiss.index")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
LLM_MODEL    = os.getenv("LLM_MODEL",    "llama3-8b-8192")
EMBED_MODEL  = os.getenv("EMBED_MODEL",  "sentence-transformers/all-MiniLM-L6-v2")
TOP_K        = int(os.getenv("TOP_K",    "5"))
