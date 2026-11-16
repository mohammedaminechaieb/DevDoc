# tests/unit/test_agents.py
# Owner: Amine
from agents import intent_analyzer, knowledge_retriever, responder
from agents.intent_analyzer import classify_keywords, extract_entities
from agents.orchestrator import ROUTES, build_graph, route_by_intent
from agents.state import INTENTS


def test_every_intent_is_routed():
    assert set(ROUTES) == set(INTENTS)


def test_unknown_intent_goes_to_responder():
    assert route_by_intent({"intent": "???"}) == "responder"


def test_graph_compiles():
    assert build_graph() is not None


def test_keyword_intents():
    assert classify_keywords("Which framework do you recommend, CrewAI vs AutoGen?") == "recommend"
    assert classify_keywords("I get an error when my LangGraph node returns None") == "code"
    assert classify_keywords("What is tool calling?") == "learn"


def test_extract_entities_matches_graph_names():
    found = extract_entities("How does LangGraph handle memory and tool calling?")
    assert "LangGraph" in found
    assert "Memory" in found
    assert "Tool Calling" in found
    assert "Tool" not in found          # covered by "Tool Calling"


def test_intent_falls_back_to_keywords_when_llm_unavailable(monkeypatch):
    def broken_llm(prompt, system=None):
        raise NotImplementedError
    monkeypatch.setattr(intent_analyzer, "call_llm", broken_llm)
    out = intent_analyzer.run({"question": "Compare CrewAI vs AutoGen"})
    assert out["intent"] == "recommend"
    assert "CrewAI" in out["entities"] and "AutoGen" in out["entities"]


def test_intent_uses_llm_json_when_available(monkeypatch):
    monkeypatch.setattr(intent_analyzer, "call_llm",
                        lambda prompt, system=None: 'Sure: {"intent": "design", "entities": ["CrewAI"]}')
    out = intent_analyzer.run({"question": "I want three agents that write a report"})
    assert out["intent"] == "design"
    assert "CrewAI" in out["entities"]          # + "Agent" found by the vocabulary matcher


def test_intent_rejects_unknown_llm_intent(monkeypatch):
    monkeypatch.setattr(intent_analyzer, "call_llm",
                        lambda prompt, system=None: '{"intent": "banana", "entities": []}')
    out = intent_analyzer.run({"question": "What is tool calling?"})
    assert out["intent"] == "learn"


def test_pipeline_end_to_end_with_mocked_nodes(monkeypatch):
    """Orchestration works even while retrieval / generation are not implemented yet."""
    def broken_llm(prompt, system=None):
        raise RuntimeError("no LLM in tests")
    monkeypatch.setattr(intent_analyzer, "call_llm", broken_llm)
    monkeypatch.setattr(knowledge_retriever, "run",
                        lambda state: {"chunks": [{"chunk_id": "c1", "text": "LangGraph builds agents.",
                                                "url": "u", "framework": "langgraph", "score": 1.0}],
                                    "graph": {"nodes": [], "edges": []}})
    monkeypatch.setattr(responder, "run",
                        lambda state: {"answer": "LangGraph builds stateful agents.",
                                    "sources": [{"chunk_id": "c1", "url": "u", "framework": "langgraph", "text": "..."}]})
    app = build_graph()
    result = app.invoke({"question": "What is LangGraph?", "top_k": 3, "use_graph": True, "history": []})
    assert result["intent"] == "learn"
    assert result["entities"] == ["LangGraph"]
    assert result["answer"].startswith("LangGraph")
    assert result["review"]["ok"] is True