# tests/unit/test_graph_pipeline.py - tri, validation, résolution, pipeline complet (faux modèles, aucun réseau)
import json

from graph.extractors import get_extractor
from graph.extractors.gliner_extractor import GlinerExtractor
from graph.extractors.llm_extractor import LLMExtractor, evidence_in_text
from graph.pipeline import assemble, run
from graph.preprocess import profile_chunk
from graph.resolution import EntityResolver, acronym
from graph.validate import Policy, accept_relation, check_relation, is_valid_entity_name

PROSE = ("In LangGraph, a supervisor agent delegates tasks to worker agents. The worker agents use tools "
         "through MCP, and the StateGraph holds the shared state of the workflow.")


def chunk(cid, text=PROSE, fw="langgraph", **kw):
    return {"chunk_id": cid, "text": text, "framework": fw, "url": f"https://x/{cid}", "version": "1",
            "source_id": f"doc_{cid}", **kw}


# ---------------------------------------------------------------- tri
def test_profile_kinds():
    assert profile_chunk(chunk("p"))["kind"] == "prose" and profile_chunk(chunk("p"))["informative"]
    css = "font-face font-family: 'IBM Plex Mono'; font-display: swap; unicode-range: U 0460; " * 3
    assert profile_chunk(chunk("c", css))["skip_all"]
    arxiv = "Toggle alphaXiv ( What is alphaXiv? ) Links to Code Toggle CatalyzeX Code Finder for Papers " * 2
    assert profile_chunk(chunk("b", arxiv))["kind"] == "boilerplate"
    code = 'model.invoke( "Hello", config={"callbacks": [handler]} ); x = f(y["k"]); z = {"a": [1, 2]}' * 3
    assert profile_chunk(chunk("k", code))["kind"] == "code"
    assert profile_chunk(chunk("s", "too short"))["kind"] == "short"
    assert profile_chunk(chunk("l", PROSE, source_id="crewai_changelog_mdx"))["kind"] == "changelog"


# ---------------------------------------------------------------- validation
def test_entity_name_filter():
    good = ["LangGraph", "InMemorySaver", "supervisor agent", "Tool Calling"]
    bad = ["it", "example", "https://a.io", "src/app.py", "v1.2.3", "OPENAI_API_KEY", "ResponseNewParamsInputUnion", "a"]
    assert all(is_valid_entity_name(n) for n in good)
    assert not any(is_valid_entity_name(n) for n in bad)


def test_relation_constraints():
    assert check_relation("USES", "Agent", "Tool")[0]
    assert not check_relation("DELEGATES_TO", "Metric", "Agent")[0]
    assert not check_relation("ALTERNATIVE_TO", "Framework", "Technique")[0]
    assert check_relation("DELEGATES_TO", "Unclassified", "Agent")[0]           # schéma ouvert : jamais pénalisé
    r = {"source": "A", "target": "B", "relation": "RELATED_TO", "confidence": 0.65, "evidence": "A and B"}
    assert not accept_relation(r, Policy())                                     # RELATED_TO exige 0.7
    assert accept_relation({**r, "relation": "USES"}, Policy())
    assert not accept_relation({**r, "relation": "USES", "evidence": ""}, Policy())


# ---------------------------------------------------------------- résolution
def _e(name, t="Concept", c=1, m="llm", conf=0.7):
    return {"name": name, "canonical_type": t, "raw_type": t, "count": c, "confidence": conf, "method": m}


def test_resolution_merges_safely():
    assert acronym("Retrieval-Augmented Generation") == "RAG"
    r = EntityResolver().fit([_e("Retrieval-Augmented Generation", "Technique"), _e("RAG", "Concept", 5, "dictionary", 1),
                              _e("Checkpointers", "Component"), _e("checkpointer", "Component", 3),
                              _e("GPT-4", "Model"), _e("GPT-3", "Model"),
                              _e("LangGraph", "Framework", m="dictionary"), _e("LangChain", "Framework", m="dictionary"),
                              _e("Agent Client Protocol", "Protocol"), _e("Agent Communication Protocol", "Protocol"),
                              _e("ACP", "Protocol")])
    assert r.canonical("retrieval augmented generation") == "RAG"
    assert r.canonical("Checkpointers") == r.canonical("checkpointer")
    assert r.canonical("GPT-4") != r.canonical("GPT-3")                         # versions jamais fusionnées
    assert r.canonical("LangGraph") != r.canonical("LangChain")
    assert r.canonical("ACP") == "ACP" and r.canonical("Agent Client Protocol") != "ACP"   # acronyme ambigu
    assert any(s["b"] == "ACP" for s in r.suggestions)
    assert "Retrieval-Augmented Generation" in r.clusters["rag"]["aliases"]


# ---------------------------------------------------------------- LLM : evidence
def test_evidence_check():
    text = "The worker agents use tools through MCP, and the StateGraph holds the state."
    assert evidence_in_text("the worker agents use tools through MCP", text)
    assert evidence_in_text("The worker agents use tools through MCP.", text)
    assert not evidence_in_text("agents talk to Kubernetes clusters every day", text)


class FakeGliner:
    def predict_entities(self, text, labels, threshold=0.5):
        out = []
        for name, label in (("supervisor agent", "ai agent"), ("worker agents", "ai agent"), ("it", "concept")):
            if name in text:
                out.append({"text": name, "label": label, "score": 0.8})
        return out


def fake_llm(prompt):
    assert "CANDIDATE ENTITIES" in prompt                   # mode guidé
    return json.dumps({
        "entities": [{"name": "supervisor agent", "type": "Agent"}, {"name": "worker agents", "type": "Agent"}],
        "relations": [
            {"source": "supervisor agent", "predicate": "delegates to", "target": "worker agents",
             "evidence": "a supervisor agent delegates tasks to worker agents"},
            {"source": "worker agents", "predicate": "uses", "target": "MCP",
             "evidence": "The worker agents use tools through MCP"},
            {"source": "LangGraph", "predicate": "uses", "target": "Kubernetes",          # inventé
             "evidence": "LangGraph runs on Kubernetes"},
            {"source": "it", "predicate": "holds", "target": "state",                     # pronom
             "evidence": "the StateGraph holds the shared state"}]})


# ---------------------------------------------------------------- pipeline complet
def test_pipeline_end_to_end(tmp_path):
    corpus = tmp_path / "corpus.jsonl"
    css = "font-face font-family: 'X'; font-display: swap; unicode-range: U 0460; " * 3
    rows = [chunk("c1"), chunk("c2", PROSE.replace("LangGraph", "CrewAI"), "crewai"), chunk("c3", css)]
    corpus.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    calls = []

    def counting_llm(p):
        calls.append(1)
        return fake_llm(p)

    def extractors():
        return {"dictionary": get_extractor("dictionary"), "gliner": GlinerExtractor(model=FakeGliner()),
                "llm": LLMExtractor(complete=counting_llm, cache_path=tmp_path / "cache.jsonl")}

    out = tmp_path / "graph"
    m = run(corpus, out, extractors=extractors(), verbose=False)
    ents = {e["name"]: e for e in map(json.loads, (out / "entities.jsonl").read_text().splitlines())}
    rels = {(r["source"], r["relation"], r["target"]): r for r in map(json.loads, (out / "relations.jsonl").read_text().splitlines())}

    assert m["chunk_kinds"]["css"] == 1 and m["processed"]["llm"] == 2
    assert {"LangGraph", "CrewAI", "MCP", "StateGraph", "supervisor agent", "worker agents"} <= set(ents)
    assert "Kubernetes" not in ents and "it" not in ents
    d = rels[("supervisor agent", "DELEGATES_TO", "worker agents")]
    assert d["support"] == 2 and d["confidence"] > 0.8 and set(d["chunk_ids"]) == {"c1", "c2"}
    assert d["evidence"] and d["source_url"].startswith("https://x/") and d["type_ok"]
    assert ("worker agents", "USES", "MCP") in rels
    assert ents["worker agents"]["canonical_type"] == "Agent" and ents["worker agents"]["df"] == 2
    mentions = [json.loads(l) for l in (out / "mentions.jsonl").read_text().splitlines()]
    assert all(x["chunk_id"] in {"c1", "c2"} for x in mentions)               # css jamais traité
    assert (out / "manifest.json").exists() and (out / "review" / "merge_suggestions.jsonl").exists()

    n = len(calls)                                                              # reprise : rien n'est refait
    m2 = run(corpus, out, extractors=extractors(), verbose=False)
    assert len(calls) == n and m2["counts"]["relations"] == m["counts"]["relations"]


def test_pipeline_llm_budget_and_priority(tmp_path):
    corpus = tmp_path / "corpus.jsonl"
    rich = chunk("rich")
    poor = chunk("poor", "LangGraph is a library that people like to talk about at length in many posts online.")
    corpus.write_text("\n".join(json.dumps(r) for r in (poor, rich)), encoding="utf-8")
    seen = []
    llm = LLMExtractor(complete=lambda p: (seen.append(p), fake_llm(p))[1], cache_path=None)
    m = run(corpus, tmp_path / "g", extractors={"dictionary": get_extractor("dictionary"), "llm": llm},
            llm_max_chunks=1, verbose=False)
    assert m["llm"]["eligible"] == 1 and len(seen) == 1 and "supervisor agent" in seen[0]   # le chunk dense d'abord


def test_type_violation_is_penalised():
    stores = {"llm": {"c1": {"entities": [], "relations": [{
        "source": "F1 score", "target": "Agent", "relation": "DELEGATES_TO", "raw_predicate": "delegates to",
        "evidence": "F1 score delegates to the Agent", "source_chunk_id": "c1", "source_url": "u",
        "document_version": "1", "extraction_method": "llm", "confidence": 0.8,
        "source_type": "Metric", "target_type": "Agent"}]}}}
    g = assemble([chunk("c1")], stores, Policy(min_relation_conf=0.0))
    r = g["relations"][0]
    assert r["type_ok"] is False and r["confidence"] == 0.4 and "Metric" in r["type_issue"]
