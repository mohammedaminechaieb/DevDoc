# tests/unit/test_retriever.py - Owner: Ghassen
import pytest
from retrieval.hybrid_retriever import retrieve

def test_returns_list():
    assert isinstance(retrieve("What is LangGraph?", k=3), list)

def test_has_required_keys():
    result = retrieve("What is LangGraph?", k=1)
    if result:
        assert "chunk_id" in result[0]
        assert "text"     in result[0]
        assert "score"    in result[0]
