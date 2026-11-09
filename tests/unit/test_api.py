# tests/unit/test_api.py - Owner: Amine
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_query_route_exists():
    res = client.post("/api/query", json={"question": "What is LangGraph?"})
    assert res.status_code in [200, 501]
