# graph/entity_extractor.py
# Primary owner: Oussema
#
# Input:  one chunk dict {chunk_id, text, framework, concept, component, version, url, ...}
# Output: list[{name, type, chunk_id}]   (type is a key of graph.schema.NODE_LABELS)

from graph.schema import NODE_LABELS

# Surface form -> canonical entity name (extend while reading the corpus)
ALIASES = {
    "tool use": "Tool Calling",
    "tool calling": "Tool Calling",
    "function calling": "Function Calling",
    "multi-agent": "Multi-Agent System",
    "multi agent": "Multi-Agent System",
    "model context protocol": "MCP",
    "vector store": "Vector Database",
    "human in the loop": "Human-in-the-loop",
}

_nlp = None


def get_nlp():
    """spaCy is loaded lazily so importing this module stays fast."""
    global _nlp
    if _nlp is None:
        import spacy
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


def extract_entities(chunk: dict) -> list[dict]:
    # TODO: 1) case-insensitive whole-word match of NODE_LABELS names + ALIASES in chunk["text"]
    #       2) optional: spaCy noun chunks / NER to propose new candidates
    #       3) deduplicate by (name, type)
    raise NotImplementedError
