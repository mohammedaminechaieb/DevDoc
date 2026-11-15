# tests/unit/test_graph_neo4j.py - loader / requêtes / retriever avec un FAUX driver Neo4j (aucune base requise)
import re

from graph import neo4j_loader as L
from graph import queries as Q
from retrieval import graph_retriever as GR


class FakeResult(list):
    def consume(self):
        return None

    def single(self):
        return self[0] if self else None


class Rec(dict):
    def data(self):
        return dict(self)


class FakeSession:
    def __init__(self, driver):
        self.d = driver

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def run(self, query, **params):
        self.d.calls.append((query, params))
        return FakeResult(Rec(r) for r in self.d.responder(query, params))

    def execute_write(self, fn):
        return fn(self)


class FakeDriver:
    def __init__(self, responder=lambda q, p: []):
        self.calls, self.responder = [], responder

    def session(self):
        return FakeSession(self)


def test_loader_uses_whitelisted_labels_and_batches():
    d = FakeDriver()
    ents = [{"key": f"e{i}", "name": f"E{i}", "canonical_type": "Framework" if i % 2 else "Evil`) DETACH DELETE n //"}
            for i in range(1200)]
    L.load_entities(d, ents)
    queries = [q for q, _ in d.calls]
    assert all("Evil" not in q for q in queries)                       # type hors schéma -> Unclassified
    assert any("SET e:`Unclassified`" in q for q in queries) and any("SET e:`Framework`" in q for q in queries)
    assert sum(len(p["rows"]) for _, p in d.calls) == 1200 and max(len(p["rows"]) for _, p in d.calls) <= L.BATCH
    d2 = FakeDriver()
    L.load_relations(d2, [{"source_key": "a", "target_key": "b", "relation": "DROP_ALL", "confidence": 0.9},
                          {"source_key": "a", "target_key": "c", "relation": "USES", "confidence": 0.9}])
    rel_types = {re.search(r"\[r:`(\w+)`\]", q).group(1) for q, _ in d2.calls}
    assert rel_types == {"RELATED_TO", "USES"}


def test_schema_statements_are_idempotent():
    assert all("IF NOT EXISTS" in s for s in L.SCHEMA_STATEMENTS)


GRAPH = {  # mini graphe en mémoire servi par le faux driver
    "nodes": {"langgraph": ("LangGraph", "Framework", 900), "stategraph": ("StateGraph", "Component", 150),
              "checkpointer": ("Checkpointer", "Component", 150), "agent": ("Agent", "Agent", 1900)},
    "edges": [("langgraph", "PROVIDES", "stategraph", 0.9, "c1"), ("stategraph", "USES", "checkpointer", 0.8, "c2"),
              ("langgraph", "SUPPORTS", "agent", 0.7, "c3")],
    "mentions": [("langgraph", "c1", 3, 1.0), ("stategraph", "c1", 2, 1.0), ("stategraph", "c2", 1, 0.9),
                 ("checkpointer", "c2", 2, 0.9), ("agent", "c4", 5, 1.0)],
}


def responder(q, p):
    N = GRAPH["nodes"]
    if "fulltext" in q:
        return []
    if "e.key IN $keys" in q and "MENTIONED_IN" not in q:
        return [{"key": k, "name": N[k][0], "type": N[k][1], "df": N[k][2]} for k in p["keys"] if k in N]
    if "MATCH (a:Entity)-[r]-(b:Entity)" in q:
        out = []
        for s, rel, t, conf, cid in GRAPH["edges"]:
            for a, b in ((s, t), (t, s)):
                if a in p["keys"]:
                    out.append({"a": a, "b": b, "b_name": N[b][0], "b_type": N[b][1], "b_df": N[b][2], "src": s,
                                "dst": t, "relation": rel, "confidence": conf, "support": 1, "evidence": "...",
                                "chunk_id": cid})
        return out
    if "MENTIONED_IN" in q:
        return [{"key": k, "chunk_id": c, "text": f"text {c}", "url": f"u/{c}", "framework": "langgraph",
                 "count": n, "confidence": conf} for k, c, n, conf in GRAPH["mentions"] if k in p["keys"]]
    return []


def test_link_and_subgraph():
    d = FakeDriver(responder)
    linked = Q.link_entities(d, "How does a StateGraph in LangGraph persist state?")
    assert {e["key"] for e in linked} == {"stategraph", "langgraph"}
    sub = Q.query_subgraph(d, ["LangGraph"], depth=2)
    ids = {n["id"] for n in sub["nodes"]}
    assert {"langgraph", "stategraph", "checkpointer", "agent"} <= ids
    assert all(e["source"] in ids and e["target"] in ids for e in sub["edges"])
    rel = Q.query_related_entities(d, "LangGraph", depth=2)
    assert [r["key"] for r in rel if r["distance"] == 2] == ["checkpointer"]


def test_hubs_are_not_traversed():
    GRAPH["edges"].append(("agent", "USES", "secret", 0.9, "c9"))
    GRAPH["nodes"]["secret"] = ("Secret", "Tool", 3)
    try:
        nodes, _ = Q._bfs(FakeDriver(responder), ["langgraph"], depth=2)
        assert "agent" in nodes and "secret" not in nodes
    finally:
        GRAPH["edges"].pop()
        del GRAPH["nodes"]["secret"]


def test_retrieve_graph_contract_and_ranking():
    res = GR.retrieve_graph("How does a StateGraph in LangGraph persist state?", k=3, driver=FakeDriver(responder))
    assert res and all(set(("chunk_id", "text", "url", "framework", "score")) <= set(r) for r in res)
    assert res[0]["chunk_id"] == "c1" and res[0]["score"] == 1.0                # cite les deux entités + preuve
    assert all(0 <= r["score"] <= 1 for r in res)


def test_retrieve_graph_degrades_gracefully():
    from neo4j.exceptions import ServiceUnavailable

    class Down:
        def session(self):
            raise ServiceUnavailable("down")
    assert GR.retrieve_graph("LangGraph?", driver=Down()) == []
    assert GR.retrieve_subgraph("LangGraph?", driver=Down()) == {"nodes": [], "edges": []}
