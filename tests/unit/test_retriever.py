# tests/unit/test_retriever.py - Owner: Ghassen
from retrieval.hybrid_retriever import retrieve


def test_returns_list():
    assert isinstance(retrieve("What is LangGraph?", k=3), list)


def test_has_required_keys():
    result = retrieve("What is LangGraph?", k=1)
    if result:
        for key in ("chunk_id", "text", "url", "framework", "score"):
            assert key in result[0]
