# tests/unit/test_extractor.py
# Owner: Aya
from graph.entity_extractor import extract_entities

CHUNK = {
    "chunk_id": "lg_001",
    "text": "In LangGraph, each node of the workflow can call a tool and update the agent memory.",
    "framework": "langgraph",
    "url": "https://langchain-ai.github.io/langgraph/",
}


def test_returns_list():
    assert isinstance(extract_entities(CHUNK), list)


def test_finds_langgraph():
    names = [e["name"] for e in extract_entities(CHUNK)]
    assert "LangGraph" in names
