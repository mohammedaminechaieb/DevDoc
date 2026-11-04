# tests/integration/test_pipeline.py
# Everyone merges here

import pytest

def test_full_pipeline():
    from retrieval.hybrid_retriever import retrieve
    from generation.answer_generator import generate_answer

    chunks = retrieve("What is LangGraph?", k=3)
    result = generate_answer("What is LangGraph?", chunks)
    assert isinstance(result["answer"], str)
    assert len(result["answer"]) > 0
