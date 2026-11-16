# agents/intent_analyzer.py
# Owner: Amine
# Role: Intent Analyzer - understands what the user needs.
#
# 1. Ask the LLM for {"intent": ..., "entities": [...]} as JSON.
# 2. If the LLM is unavailable or answers badly, fall back to keyword rules.
# Entities are matched with the knowledge-graph vocabulary (graph/vocabulary.py),
# so knowledge_retriever can look them up in Neo4j directly.

import json
import re

from agents.state import INTENTS, CopilotState
from generation.llm_client import call_llm
from graph import vocabulary as V
from graph.entity_extractor import find_mentions

# Cheap fallback used when the LLM is unavailable (and as a sanity check in tests)
KEYWORDS = {
    "code":      ["code", "implement", "error", "bug", "exception", "traceback", "example", "snippet", "fix"],
    "design":    ["architecture", "design", "concevoir", "how should i build", "structure my"],
    "recommend": ["which framework", "recommend", "compare", " vs ", "versus", "choose", "better"],
    "evaluate":  ["evaluate", "evaluation", "hallucination", "reliability", "metric", "benchmark", "measure"],
    "explore":   ["workflow", "flow", "step by step", "visualize", "visualise", "transition"],
}

# Canonical entity names known to the graph (name -> type), longest first for the prompt
KNOWN_ENTITIES = sorted(V.ENTITIES, key=len, reverse=True)

INTENT_PROMPT = """You classify questions asked to an Agentic AI copilot.

Intents (pick exactly one key):
{intents}

Known entities (frameworks, concepts, components): {entities}

Previous turns:
{history}

Question: {question}

Reply with ONLY a JSON object, no explanation:
{{"intent": "<intent key>", "entities": ["<known entity>", ...]}}"""


def classify_keywords(question: str) -> str:
    q = f" {question.lower()} "
    for intent, words in KEYWORDS.items():
        if any(w in q for w in words):
            return intent
    return "learn"


def extract_entities(question: str) -> list[str]:
    """Graph entities mentioned in the question, using Aya's vocabulary + aliases.
    Overlapping mentions keep the longest one ("Tool Calling" beats "Tool")."""
    mentions = sorted(find_mentions(question), key=lambda m: (m["start"], -(m["end"] - m["start"])))
    found: list[str] = []
    last_end = -1
    for m in mentions:
        if m["start"] < last_end:          # nested inside the previous, longer mention
            continue
        if m["name"] not in found:
            found.append(m["name"])
        last_end = m["end"]
    return found


def _format_history(history: list[dict] | None, max_turns: int = 4) -> str:
    turns = (history or [])[-max_turns:]
    lines = [f"{t.get('role', 'user')}: {str(t.get('content', ''))[:200]}" for t in turns]
    return "\n".join(lines) or "(none)"


def classify_llm(question: str, history: list[dict] | None = None) -> dict | None:
    """Returns {"intent", "entities"} or None when the LLM fails or gives an unknown intent."""
    prompt = INTENT_PROMPT.format(
        intents="\n".join(f"- {k}: {v}" for k, v in INTENTS.items()),
        entities=", ".join(KNOWN_ENTITIES[:80]),
        history=_format_history(history),
        question=question,
    )
    try:
        raw = call_llm(prompt, system="You are a strict JSON classifier.")
        match = re.search(r"\{.*\}", raw, re.S)
        data = json.loads(match.group(0)) if match else {}
    except Exception:          # RuntimeError (no key), network error, bad JSON...
        return None
    intent = data.get("intent")
    if intent not in INTENTS:
        return None
    entities = [e for e in data.get("entities", []) if isinstance(e, str) and e in V.ENTITIES]
    return {"intent": intent, "entities": entities}


def run(state: CopilotState) -> dict:
    question = state["question"]
    result = classify_llm(question, state.get("history"))
    if result is None:
        result = {"intent": classify_keywords(question), "entities": []}
    # Always add exact matches so the graph lookup has something even if the LLM missed them
    entities = list(dict.fromkeys(result["entities"] + extract_entities(question)))
    return {"intent": result["intent"], "entities": entities}
