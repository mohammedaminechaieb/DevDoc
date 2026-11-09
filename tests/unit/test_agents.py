# tests/unit/test_agents.py
# Owner: Amine
from agents.intent_analyzer import classify_keywords
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
