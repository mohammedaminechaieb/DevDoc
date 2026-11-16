# tests/unit/test_normalize.py
from graph import normalize as N


def test_entity_resolution_merges_variants():
    assert N.norm_key("State Graph") == N.norm_key("StateGraph") == N.norm_key("state graphs")
    assert N.canonical_entity_name("tool use") == "Tool Calling"
    assert N.canonical_entity_name("Langgraph") == "LangGraph"


def test_type_known_synonym_and_unknown():
    assert N.normalize_type("Framework") == "Framework"
    assert N.normalize_type("library") == "Framework"
    N.CANDIDATES["node_type"].clear()
    assert N.normalize_type("quantum widget") == "Unclassified"
    assert N.CANDIDATES["node_type"]["quantum widget"] == 1      # candidat à relire


def test_relation_normalization():
    assert N.normalize_relation("uses") == ("USES", True)
    assert N.normalize_relation("relies on") == ("USES", True)
    assert N.normalize_relation("delegates to") == ("DELEGATES_TO", True)
    assert N.normalize_relation("is built on") == ("IMPLEMENTS", True)
    assert N.normalize_relation("DEPENDS_ON") == ("DEPENDS_ON", True)
    assert N.normalize_relation("frobnicates", record=False) == ("RELATED_TO", False)
