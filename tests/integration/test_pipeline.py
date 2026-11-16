# tests/integration/test_pipeline.py
# Owner: Oussema
# Everyone merges here: full LangGraph pipeline end to end.
#
#   pytest tests/integration                  # offline tests: real graph + real API, mocked retrieval/LLM
#   RUN_LIVE_TESTS=1 pytest tests/integration # also the live test (FAISS index, Neo4j and an LLM required)
import os

import pytest

from agents import evaluation_assistant, intent_analyzer, knowledge_retriever
from agents import orchestrator
from agents.orchestrator import build_graph

CHUNKS = [
    {"chunk_id": "e1", "framework": "langgraph", "score": 0.9, "url": "https://docs.example.com/eval",
     "text": "Evaluate an agent by measuring answer quality, tool usage accuracy, execution errors and "
             "latency. Hallucinations are reduced by grounding every answer in retrieved passages."},
    {"chunk_id": "e2", "framework": "crewai", "score": 0.7, "url": "https://docs.example.com/reliability",
     "text": "Reliability of a multi-agent system is measured with repeated runs, success rate and "
             "the number of failed tool calls."},
]
QUESTION = "How can I evaluate the reliability of my multi-agent system and limit hallucinations?"
GOOD_LLM_ANSWER = (
    "Evaluate the agent by measuring answer quality, tool usage accuracy, execution errors and latency [1]. "
    "Hallucinations are reduced by grounding every answer in retrieved passages [1]. Reliability of a "
    "multi-agent system is measured with repeated runs, the success rate and the number of failed tool "
    "calls [2].\n\nSources:\n[1] langgraph https://docs.example.com/eval\n"
    "[2] crewai https://docs.example.com/reliability"
)


@pytest.fixture
def offline_copilot(monkeypatch):
    """Real LangGraph + real agents. Only the outside world is mocked: LLM and retrieval."""
    # the orchestrator may cache its compiled graph (get_app): never keep a graph built with mocks
    monkeypatch.setattr(orchestrator, "_app", None, raising=False)

    def no_llm(prompt, system=None):
        raise RuntimeError("no LLM in tests")

    monkeypatch.setattr(intent_analyzer, "call_llm", no_llm, raising=False)    # keyword fallback
    monkeypatch.setattr(knowledge_retriever, "run", lambda state: {
        "chunks": CHUNKS, "graph": {"nodes": [{"id": "agent", "label": "Agent", "type": "Component"}],
                                    "edges": []}})
    monkeypatch.setattr(evaluation_assistant, "build_prompt", lambda q, chunks, instr=None: "PROMPT")
    llm = {"answer": GOOD_LLM_ANSWER}
    monkeypatch.setattr(evaluation_assistant, "call_llm", lambda prompt, system=None: llm["answer"])
    return llm


def _invoke():
    return build_graph().invoke({"question": QUESTION, "top_k": 2, "use_graph": True, "history": []})


def test_evaluate_intent_flows_through_evaluation_assistant_and_reviewer(offline_copilot):
    result = _invoke()
    assert result["intent"] == "evaluate"
    assert result["answer"] == GOOD_LLM_ANSWER
    assert [s["chunk_id"] for s in result["sources"]] == ["e1", "e2"]
    assert result["review"] == {"ok": True, "issues": []}


def test_reviewer_flags_a_hallucinated_link_end_to_end(offline_copilot):
    offline_copilot["answer"] = GOOD_LLM_ANSWER + "\nSee https://invented.example.org/paper"
    review = _invoke()["review"]
    assert review["ok"] is False
    assert any("invented.example.org" in issue for issue in review["issues"])


def test_api_returns_review_and_graph(offline_copilot):
    from fastapi.testclient import TestClient

    from api.main import app
    from api.schemas.response import QueryResponse

    if "review" not in QueryResponse.model_fields:
        pytest.skip("needs the feat/api version of api/schemas (review field)")
    res = TestClient(app).post("/api/query", json={"question": QUESTION, "top_k": 2})
    assert res.status_code == 200
    body = res.json()
    assert body["intent"] == "evaluate"
    assert body["review"]["ok"] is True
    assert len(body["sources"]) == 2
    assert body["graph"]["nodes"][0]["label"] == "Agent"


@pytest.mark.skipif(os.getenv("RUN_LIVE_TESTS") != "1",
                    reason="live test: needs the FAISS index, Neo4j and an LLM (set RUN_LIVE_TESTS=1)")
def test_full_pipeline():
    from agents.orchestrator import run_copilot

    result = run_copilot("What is LangGraph?", top_k=3)
    assert result["intent"] == "learn"
    assert isinstance(result["answer"], str) and result["answer"]
    assert result["sources"]
    assert "ok" in result["review"]
