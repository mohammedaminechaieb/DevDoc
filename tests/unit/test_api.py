# tests/unit/test_api.py
# Owner: Amine
# The pipeline itself is mocked here: unit tests never touch FAISS, Neo4j or an LLM.

from fastapi.testclient import TestClient

from api.main import app
from api.routes import query as query_route

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_query_route_exists_and_maps_not_implemented_to_501(monkeypatch):
    def not_ready(q, **kw):
        raise NotImplementedError("stage missing")

    monkeypatch.setattr(query_route, "run_copilot", not_ready)

    res = client.post("/api/query", json={"question": "What is LangGraph?"})

    assert res.status_code == 501
    assert "stage missing" in res.json()["detail"]


def test_missing_index_maps_to_503(monkeypatch):
    def no_index(q, **kw):
        raise FileNotFoundError(2, "Index not built", "data/faiss.index")

    monkeypatch.setattr(query_route, "run_copilot", no_index)

    res = client.post("/api/query", json={"question": "What is LangGraph?"})

    assert res.status_code == 503
    assert "faiss_indexer" in res.json()["detail"]


def test_query_rejects_empty_question():
    res = client.post("/api/query", json={"question": ""})

    assert res.status_code == 422


def test_query_rejects_bad_top_k():
    res = client.post(
        "/api/query",
        json={"question": "What is LangGraph?", "top_k": 0},
    )

    assert res.status_code == 422


def test_query_response_shape(monkeypatch):
    monkeypatch.setattr(
        query_route,
        "run_copilot",
        lambda q, **kw: {
            "intent": "learn",
            "entities": ["LangGraph"],
            "answer": "LangGraph builds stateful agents.",
            "sources": [
                {
                    "chunk_id": "c1",
                    "url": "u",
                    "framework": "langgraph",
                    "text": "...",
                }
            ],
            "graph": {"nodes": [], "edges": []},
            "review": {"ok": True, "issues": []},
        },
    )

    res = client.post(
        "/api/query",
        json={
            "question": "What is LangGraph?",
            "history": [
                {"role": "user", "content": "hi"},
                {"role": "assistant", "content": "hello"},
            ],
        },
    )

    assert res.status_code == 200

    body = res.json()

    assert body["query"] == "What is LangGraph?"
    assert body["intent"] == "learn"
    assert body["entities"] == ["LangGraph"]
    assert body["sources"][0]["framework"] == "langgraph"
    assert body["review"]["ok"] is True


def test_pipeline_error_becomes_500(monkeypatch):
    def boom(q, **kw):
        raise RuntimeError("neo4j down")

    monkeypatch.setattr(query_route, "run_copilot", boom)

    res = client.post("/api/query", json={"question": "What is LangGraph?"})

    assert res.status_code == 500
    assert "neo4j down" in res.json()["detail"]
