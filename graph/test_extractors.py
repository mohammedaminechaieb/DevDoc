# tests/unit/test_extractors.py - interface commune, LLM/GLiNER/Relex avec de FAUX modèles (aucun réseau)
import json

from graph.extractors import get_extractor
from graph.extractors.gliner_extractor import GlinerExtractor
from graph.extractors.llm_extractor import LLMExtractor
from graph.extractors.relex_extractor import GlinerRelexExtractor
from graph.merge import filter_by_votes, merge_extractions

CHUNK = {"chunk_id": "c1", "url": "u", "framework": "langgraph", "version": "1",
         "text": "In LangGraph, an agent calls a tool. The StateGraph holds the state."}


def test_dictionary_via_registry():
    out = get_extractor("dictionary").extract(CHUNK)
    assert {"LangGraph", "Agent", "Tool", "StateGraph"} <= {e["name"] for e in out["entities"]}
    assert all("canonical_type" in e and e["method"] == "dictionary" for e in out["entities"])


class FakeGliner:
    def predict_entities(self, text, labels, threshold=0.5):
        return [{"text": "LangGraph", "label": "framework", "score": 0.9, "start": 3, "end": 12},
                {"text": "state graph", "label": "data structure", "score": 0.6, "start": 0, "end": 1},
                {"text": "it", "label": "concept", "score": 0.9, "start": 0, "end": 1}]


def test_gliner_normalizes_types_and_names():
    out = GlinerExtractor(model=FakeGliner()).extract(CHUNK)
    byname = {e["name"]: e for e in out["entities"]}
    assert byname["LangGraph"]["canonical_type"] == "Framework"
    assert byname["StateGraph"]["canonical_type"] == "DataStructure"   # alias résolu, type issu du modèle
    assert "it" not in byname                                           # mot vide filtré


class FakeRelex:
    def inference(self, texts, labels, relations, **kw):
        assert "uses" in relations and "depends on" in relations
        ents = [[{"text": "agent", "label": "ai agent", "score": 0.8}, {"text": "tool", "label": "tool", "score": 0.7}]]
        rels = [[{"head": {"text": "agent", "type": "ai agent"}, "tail": {"text": "tool", "type": "tool"},
                  "relation": "calls", "score": 0.66}]]
        return ents, rels


def test_relex_relations_get_canonical_label_and_evidence():
    out = GlinerRelexExtractor(model=FakeRelex()).extract(CHUNK)
    r = out["relations"][0]
    assert (r["source"], r["relation"], r["target"]) == ("Agent", "INVOKES", "Tool")
    assert r["raw_predicate"] == "calls" and "agent calls a tool" in r["evidence"].lower()


def test_llm_validation_and_cache(tmp_path):
    calls = []

    def fake_complete(prompt):
        calls.append(1)
        return "```json\n" + json.dumps({
            "entities": [{"name": "LangGraph", "type": "Framework"}, {"name": "Kubernetes", "type": "Platform"}],
            "relations": [
                {"source": "agent", "predicate": "calls", "target": "tool", "evidence": "an agent calls a tool"},
                {"source": "agent", "predicate": "uses", "target": "Kubernetes", "evidence": "x"},      # hallucination
                {"source": "agent", "predicate": "uses", "target": "tool", "evidence": ""}]}) + "\n```"  # sans evidence

    ex = LLMExtractor(complete=fake_complete, cache_path=tmp_path / "c.jsonl")
    out = ex.extract(CHUNK)
    names = {e["name"] for e in out["entities"]}
    assert "Kubernetes" not in names and {"LangGraph", "Agent", "Tool"} <= names
    assert [(r["source"], r["relation"], r["target"]) for r in out["relations"]] == [("Agent", "INVOKES", "Tool")]
    ex.extract(CHUNK)
    assert len(calls) == 1                                  # 2e appel : servi par le cache
    assert len(LLMExtractor(complete=fake_complete, cache_path=tmp_path / "c.jsonl").cache.data) == 1


def test_llm_garbage_output_is_safe():
    ex = LLMExtractor(complete=lambda p: "sorry, no json", cache_path=None)
    assert ex.extract(CHUNK) == {"entities": [], "relations": []}


def test_merge_votes():
    d = get_extractor("dictionary").extract(CHUNK)
    g = GlinerExtractor(model=FakeGliner()).extract(CHUNK)
    m = merge_extractions({"dictionary": d, "gliner": g})
    lg = next(e for e in m["entities"] if e["name"] == "LangGraph")
    assert lg["votes"] == 2 and lg["method"] == ["dictionary", "gliner"] and lg["confidence"] >= 0.9
    both = {e["name"] for e in filter_by_votes(m, 2)["entities"]}
    assert "LangGraph" in both and "Tool" not in both        # Tool : trouvé par le dictionnaire seul
