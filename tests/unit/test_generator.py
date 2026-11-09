# tests/unit/test_generator.py - Owner: Mariem
from generation.answer_generator import generate_answer

CHUNKS = [{
    "chunk_id": "lg_001",
    "text": "LangGraph is a library for building stateful agents.",
    "url": "https://langchain-ai.github.io/langgraph/",
    "framework": "langgraph", "score": 0.95,
}]


def test_returns_dict():
    assert isinstance(generate_answer("What is LangGraph?", CHUNKS), dict)


def test_has_required_keys():
    r = generate_answer("What is LangGraph?", CHUNKS)
    assert "answer" in r and "sources" in r and "query" in r
