# graph/relation_extractor.py
# Owner: Aya
#
# Extracteur de RELATIONS par règles (par phrase). Précis mais à faible rappel : c'est la base
# de comparaison. Dans une phrase, un verbe déclencheur ("uses") relie l'entité qui le précède
# (source) à celle qui le suit (cible), sous contraintes de type. Le verbe est conservé dans
# raw_predicate ; la relation canonique est celle de la règle.

import re

from graph.entity_extractor import clean_text, find_mentions
from graph.extractors.base import make_relation
from graph.schema import NODE_TYPES, RELATION_TYPES

# Les ensembles contiennent des TYPES du schéma et/ou des NOMS d'entités autorisés.
ACTORS = {"Framework", "Agent", "AI Agent", "Crew", "Workflow", "LLM", "RAG", "GraphRAG",
          "Multi-Agent System", "Orchestration", "ReAct", "Reflection", "Routing", "Retrieval"}
ALL_TYPES = set(NODE_TYPES)

RULES = [  # (relation canonique, déclencheur, sources autorisées, cibles autorisées)
    ("DELEGATES_TO", r"\b(?:delegates?|hands?\s+off|handoffs?|transfers?(?:\s+control)?|routes?)\s+(?:\w+\s+){0,2}?to\b",
     {"Agent", "AI Agent", "LLM", "Crew"}, {"Agent", "AI Agent", "Crew"}),
    ("CONTAINS", r"\b(?:contains?|consists?\s+of|is\s+composed\s+of|comprises?|is\s+made\s+up\s+of|includes?)\b",
     {"Workflow", "Crew", "Multi-Agent System", "Orchestration"}, {"Node", "Edge", "Agent", "Task", "Tool", "State"}),
    ("HAS", r"\b(?:has|have|maintains?|stores?|keeps?|holds?)\b",
     {"Agent", "AI Agent", "Crew", "Workflow", "Multi-Agent System"},
     {"Memory", "Tool", "State", "Task", "LLM", "Checkpointer", "Planning", "Reasoning"}),
    ("CONNECTS_TO", r"\b(?:connects?|exposes?|bridges?)\b",
     {"MCP"}, {"Agent", "AI Agent", "Tool", "Model", "API"}),
    ("ALTERNATIVE_TO", r"\b(?:alternative\s+to|compared\s+(?:to|with)|versus|vs\.?|instead\s+of|unlike)\b",
     {"Framework"}, {"Framework"}),
    ("IMPLEMENTS", r"\b(?:implements?|is\s+built\s+(?:on|with)|builds?\s+on)\b",
     {"Framework"}, {"Workflow", "Agent", "Multi-Agent System", "Orchestration", "ReAct", "Reflection",
                    "Routing", "Retrieval", "Human-in-the-loop", "RAG", "GraphRAG"}),
    ("SUPPORTS", r"\b(?:supports?|provides?|offers?|enables?|allows?)\b",
     {"Framework"}, {"Concept", "Technique", "Protocol", "Tool", "Agent", "Component", "DataStore"}),
    ("INVOKES", r"\b(?:calls?|invokes?|executes?)\b",
     ACTORS, {"Tool", "API", "Model", "Technique"}),
    ("USES", r"\b(?:uses?|using|utili[sz]es?|leverages?|relies\s+on|requires?|depends\s+on)\b",
     ACTORS, ALL_TYPES),
]
for _rel, *_ in RULES:
    assert _rel in RELATION_TYPES, f"relation absente du schéma : {_rel}"
_COMPILED = [(r, re.compile(rx, re.IGNORECASE), s, t) for r, rx, s, t in RULES]

MAX_GAP, MAX_SENT = 70, 350
_SENT = re.compile(r"(?<=[.!?])\s+|\n+")


def _ok(m: dict, allowed: set) -> bool:
    return m["name"] in allowed or m["type"] in allowed


def _drop_nested(ments: list[dict]) -> list[dict]:
    """Mention contenue dans une plus longue ("tool" dans "tool calling") : on garde la plus longue."""
    return [m for m in ments
            if not any(o is not m and o["start"] <= m["start"] and m["end"] <= o["end"]
                       and (o["end"] - o["start"]) > (m["end"] - m["start"]) for o in ments)]


def extract_relations(chunk: dict, entities: list[dict]) -> list[dict]:
    allowed = {e["name"] for e in entities}
    text = clean_text(chunk.get("text", ""))
    found, pos = {}, 0
    for sent in _SENT.split(text):
        start = text.find(sent, pos)
        pos = start + len(sent) if start >= 0 else pos
        if not sent or len(sent) > MAX_SENT:
            continue
        ments = _drop_nested([m for m in find_mentions(sent) if m["name"] in allowed])
        if len(ments) < 2:
            continue
        for rel, rx, src_ok, tgt_ok in _COMPILED:
            for t in rx.finditer(sent):
                if any(m["start"] < t.end() and t.start() < m["end"] for m in ments):
                    continue  # le "verbe" fait partie d'une entité ("tool use")
                before = [m for m in ments if m["end"] <= t.start() and t.start() - m["end"] <= MAX_GAP and _ok(m, src_ok)]
                after = [m for m in ments if m["start"] >= t.end() and m["start"] - t.end() <= MAX_GAP and _ok(m, tgt_ok)]
                if not before or not after:
                    continue
                s_m, t_m = before[-1], after[0]
                if s_m["name"] == t_m["name"] and rel != "DELEGATES_TO":
                    continue
                key = (s_m["name"], rel, t_m["name"])
                if key not in found:
                    found[key] = make_relation(
                        s_m["name"], t_m["name"], t.group(0).lower(), chunk, "rules",
                        confidence=0.6 if len(sent) < 200 else 0.4, evidence=sent,
                        source_type=s_m["type"], target_type=t_m["type"], relation=rel)
    return list(found.values())
