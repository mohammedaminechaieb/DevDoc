# tests/integration/test_pipeline.py
# Owner: Oussema
# Everyone merges here: full LangGraph pipeline end to end.


def test_full_pipeline():
    from agents.orchestrator import run_copilot

    result = run_copilot("What is LangGraph?", top_k=3)
    assert result["intent"] == "learn"
    assert isinstance(result["answer"], str) and result["answer"]
    assert result["sources"]
