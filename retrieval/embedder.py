# retrieval/embedder.py
# Owner: Mariem
#
# One embedder for the whole project (indexing AND live queries must use the same model):
# EMBED_MODEL from config/.env, loaded once, vectors L2-normalised (float32) for FAISS.

import numpy as np

from config.settings import EMBED_MODEL

_model = None


def get_model():
    """Loaded lazily: sentence-transformers is slow to import."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def embed(texts: list[str], batch_size: int = 32) -> np.ndarray:
    """np.ndarray of shape (len(texts), dim), normalised - dim is 384 for MiniLM, 1024 for bge-m3."""
    vecs = get_model().encode(list(texts), batch_size=batch_size,
                              normalize_embeddings=True, show_progress_bar=len(texts) > 100)
    return np.asarray(vecs, dtype="float32")


class Embedder:
    """Object form used by faiss_indexer / faiss_retriever."""

    def __init__(self, model_name: str | None = None, batch_size: int = 32):
        self.model_name = model_name or EMBED_MODEL
        self.batch_size = batch_size

    def embed_corpus(self, texts: list[str]) -> np.ndarray:
        return embed(texts, self.batch_size)


# names used by faiss_indexer.py / faiss_retriever.py
BGEM3Embedder = Embedder
CustomEmbedder = Embedder
