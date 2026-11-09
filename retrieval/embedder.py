# retrieval/embedder.py
# Owner: Ghassen

from config.settings import EMBED_MODEL

_model = None


def get_model():
    """Loaded lazily: sentence-transformers is slow to import."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def embed(texts: list[str]):
    # TODO: return normalised np.ndarray of shape (len(texts), dim) - dim is 384 for MiniLM
    raise NotImplementedError
