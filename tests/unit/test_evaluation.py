# tests/unit/test_evaluation.py
from graph.evaluation import evaluate

GOLD = [{"chunk_id": "c1",
         "entities": [{"name": "LangGraph"}, {"name": "Tool"}, {"name": "State Graph"}],
         "relations": [{"source": "Agent", "relation": "USES", "target": "Tool"},
                       {"source": "Agent", "relation": "calls", "target": "API"}]}]


def pred(ents, rels):
    return {"c1": {"entities": [{"name": n} for n in ents],
                   "relations": [{"source": s, "relation": r, "target": t} for s, r, t in rels]}}


def test_perfect_with_aliases_and_synonyms():
    p = pred(["langgraph", "tools", "StateGraph"], [("agent", "USES", "tool"), ("Agent", "INVOKES", "API")])
    m = evaluate(p, GOLD)
    assert m["entities"]["f1"] == 1.0 and m["relations"]["f1"] == 1.0     # "calls" == INVOKES


def test_precision_recall_counts():
    p = pred(["LangGraph", "Kubernetes"], [("Agent", "USES", "Tool"), ("Agent", "SUPPORTS", "API")])
    m = evaluate(p, GOLD)
    assert (m["entities"]["tp"], m["entities"]["fp"], m["entities"]["fn"]) == (1, 1, 2)
    assert (m["relations"]["tp"], m["relations"]["fp"], m["relations"]["fn"]) == (1, 1, 1)
    assert m["pairs"]["recall"] == 1.0          # la bonne paire (Agent, API) trouvée, mais mal étiquetée


def test_missing_chunk_counts_as_empty():
    m = evaluate({}, GOLD)
    assert m["entities"]["recall"] == 0.0 and m["entities"]["fn"] == 3
