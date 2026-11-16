# tests/unit/test_relations.py
from graph.entity_extractor import extract_entities
from graph.relation_extractor import extract_relations


def run(text, fw="langgraph"):
    chunk = {"chunk_id": "c1", "url": "u", "framework": fw, "version": "0.2", "text": text}
    return extract_relations(chunk, extract_entities(chunk))


def triples(text):
    return {(r["source"], r["relation"], r["target"]) for r in run(text)}


def test_agent_uses_tool():
    assert ("Agent", "USES", "Tool") in triples("An agent uses a tool to fetch data.")


def test_call_is_invokes_not_uses():
    t = triples("An agent calls a tool.")
    assert ("Agent", "INVOKES", "Tool") in t and ("Agent", "USES", "Tool") not in t


def test_workflow_contains_node():
    assert ("Workflow", "CONTAINS", "Node") in triples("A workflow contains several nodes and edges.")


def test_no_relation_without_verb():
    assert triples("Agent, tool, memory.") == set()


def test_type_constraint_blocks_wrong_direction():
    assert ("LangGraph", "USES", "Agent") not in triples("The agent uses LangGraph.")


def test_tool_use_is_an_entity_not_a_verb():
    assert not any(r["target"] == "Tool Calling" and r["source"] == "Tool" for r in run("A tool use example."))


def test_provenance_and_raw_predicate_kept():
    r = run("A crew contains agents.", fw="crewai")[0]
    assert r["source_chunk_id"] == "c1" and r["source_url"] == "u" and r["document_version"] == "0.2"
    assert r["extraction_method"] == "rules" and r["raw_predicate"] == "contains" and r["evidence"]
